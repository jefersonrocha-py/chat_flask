import os
import json
import time
import logging
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama

# Conexões com bancos de dados
import mysql.connector
import psycopg2
from pymongo import MongoClient
import pyodbc

# Importa os módulos de prompts e schemas que separei para melhoria
from prompts import *
from schemas import *

# Configuração de logging
logging.basicConfig(
    filename="chatbot_agent_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def show_error(message: str) -> None:
    """Exibe mensagem de erro na interface e registra no log."""
    st.error(f"❌ Oops! Something went wrong: {message}")
    logging.error(message)

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do servidor Ollama
OLLAMA_SERVER_URL = "http://localhost:11434"

def check_backend_connection(url: str = OLLAMA_SERVER_URL) -> bool:
    """Verifica se o backend do Ollama está disponível."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error connecting to the Ollama backend: {e}")
        return False

if not check_backend_connection():
    st.error("Ollama server not available. Please start the server and try again.")
    st.stop()

def initialize_chat_model() -> ChatOllama:
    """Inicializa o modelo de chat do Ollama."""
    try:
        return ChatOllama(base_url=OLLAMA_SERVER_URL, model="llama3.2:latest")
    except Exception as e:
        show_error(f"Error initializing chat model: {e}")
        st.stop()

chat_model = initialize_chat_model()

# CSS customizado e configurações de layout
st.markdown(
    """
    <style>
    .sidebar-footer {
        position: fixed;
        bottom: 100px;
        left: 0;
        width: 244px;
        text-align: center;
        z-index: 10000;
        margin-left: 1rem;
        padding-bottom: 10px;
    }
    .avatar-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px 0;
    }
    .avatar-initial {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: #4CAF50;
        color: white;
        font-size: 24px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .back-button {
        background-color: #4CAF50;
        color: white !important;
        padding: 12px 24px;
        border: none;
        border-radius: 25px;
        cursor: pointer;
        font-size: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        text-decoration: none !important;
    }
    .back-button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
    }
    .custom-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #0E1117;
        padding: 1rem 5%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 9999;
        border-top: 1px solid #2f2f2f;
        color: #fff;
        min-height: 60px;
    }
    [data-testid="stSidebar"] {
        z-index: 1000;
    }
    [data-testid="stAppViewContainer"] {
        padding-bottom: 70px;
    }
    .footer-content {
        max-width: 1200px;
        width: 100%;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 2rem;
    }
    .footer-logo img {
        height: 40px;
        filter: brightness(0) invert(1);
    }
    .footer-neon {
        animation: neonPulse 1.5s infinite alternate;
        white-space: nowrap;
    }
    @keyframes neonPulse {
        from { text-shadow: 0 0 5px rgba(8,255,184,0.3); }
        to { text-shadow: 0 0 15px rgba(8,255,184,0.5); }
    }
    .chat-title {
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
        color: #4CAF50;
    }
    [data-testid="stChatInput"] {
        margin-bottom: 90px !important;
    }
    </style>
    """, unsafe_allow_html=True
)

# Botão de voltar na sidebar
FLASK_ROUTE = "http://172.16.20.230:5000/mode_selection"
st.sidebar.markdown(
    f"""
    <div class="sidebar-footer">
        <a href="{FLASK_ROUTE}" target="_self">
            <button class="back-button">⬅️ Voltar</button>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# Avatar do usuário
query_params = st.query_params
user_logged = query_params.get("username", ["Usuário"])[0]
initial = user_logged[0].upper() if user_logged else "U"
st.sidebar.markdown(
    f"""
    <div class="avatar-container">
        <div class="avatar-initial">{initial}</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Botão de voltar na sidebar
FLASK_ROUTE = "http://172.16.20.230:5000/mode_selection"
st.sidebar.markdown(
    f"""
    <div class="sidebar-footer">
        <a href="{FLASK_ROUTE}" target="_self">
            <button class="back-button">⬅️ Voltar</button>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# Seleção de modo de operação
st.sidebar.title("Mode Agent")
agent_mode = st.sidebar.selectbox(
    "Modo de Operação:",
    options=["Educacional", "Pesquisa Web", "Análise"]
)

# Botão para limpar o histórico de chat
if st.sidebar.button("Limpar Histórico"):
    st.session_state["chat_messages"] = []
    st.success("Histórico limpo com sucesso!")

# Uploader de áudio (apenas para modo Educacional)
audio_text = None
if agent_mode == "Educacional":
    audio_file = st.sidebar.file_uploader("Envie um arquivo de áudio (mp3, wav)", type=["mp3", "wav"])
    if audio_file is not None:
        audio_text = "Audio received for correction. (Simulated transcription)"
        st.sidebar.info("Audio received! Simulated transcription available.")

# Informações adicionais por modo
if agent_mode == "Educacional":
    st.sidebar.info("Focus: Correction and teaching of English, Spanish, and French (audio/text).")
elif agent_mode == "Pesquisa Web":
    st.sidebar.info("Focus: Detailed, sourced answers based on web research.")
elif agent_mode == "Análise":
    st.sidebar.info("Focus: Data extraction, summarization, and interpretation to generate insights and reports.")

# =============================================================================
# FUNÇÕES DE CONEXÃO COM BANCO DE DADOS
# =============================================================================
def connect_mysql(host: str, port: str, user: str, password: str, database: str):
    try:
        return mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
    except Exception as e:
        st.error("Error connecting to MySQL: " + str(e))
        return None

def connect_postgresql(host: str, port: str, user: str, password: str, database: str):
    try:
        return psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=database
        )
    except Exception as e:
        st.error("Error connecting to PostgreSQL: " + str(e))
        return None

def connect_mongodb(host: str, port: str, user: str, password: str, database: str):
    try:
        uri = f"mongodb://{user}:{password}@{host}:{port}/{database}"
        client = MongoClient(uri)
        return client[database]
    except Exception as e:
        st.error("Error connecting to MongoDB: " + str(e))
        return None

def connect_sqlserver(host: str, port: str, user: str, password: str, database: str):
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password}"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error("Error connecting to SQL Server: " + str(e))
        return None

def analyze_database(conn, db_type: str) -> dict:
    analysis = {}
    try:
        if db_type in ["MySQL", "PostgreSQL", "SQL Server"]:
            cursor = conn.cursor()
            if db_type == "MySQL":
                cursor.execute("SHOW TABLES")
                for (table_name,) in cursor.fetchall():
                    cursor.execute(f"DESCRIBE {table_name}")
                    analysis[table_name] = {"columns": cursor.fetchall()}
            elif db_type == "PostgreSQL":
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                for (table_name,) in cursor.fetchall():
                    cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
                    analysis[table_name] = {"columns": cursor.fetchall()}
            elif db_type == "SQL Server":
                cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
                for (table_name,) in cursor.fetchall():
                    cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
                    analysis[table_name] = {"columns": cursor.fetchall()}
        elif db_type == "MongoDB":
            for coll in conn.list_collection_names():
                sample = conn[coll].find_one()
                analysis[coll] = {"sample_document": sample}
    except Exception as e:
        st.error(f"Error analyzing the database: {e}")
    return analysis

# =============================================================================
# CONEXÃO COM BANCO DE DADOS (Sidebar)
# =============================================================================
with st.sidebar.expander("Conexão com Banco de Dados"):
    db_type = st.selectbox("Tipo de Banco", ["MySQL", "PostgreSQL", "MongoDB", "SQL Server"])
    host = st.text_input("Host", value="localhost")
    default_ports = {"MySQL": "3306", "PostgreSQL": "5432", "MongoDB": "27017", "SQL Server": "1433"}
    port = st.text_input("Porta", value=default_ports[db_type])
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    database = st.text_input("Database")

    if st.button("Conectar Banco de Dados"):
        connection = None
        if db_type == "MySQL":
            connection = connect_mysql(host, port, username, password, database)
        elif db_type == "PostgreSQL":
            connection = connect_postgresql(host, port, username, password, database)
        elif db_type == "MongoDB":
            connection = connect_mongodb(host, port, username, password, database)
        elif db_type == "SQL Server":
            connection = connect_sqlserver(host, port, username, password, database)

        if connection:
            st.success(f"Conexão com {db_type} realizada com sucesso!")
            st.session_state["db_connection"] = connection
            st.session_state["db_type"] = db_type
            analysis_result = analyze_database(connection, db_type)
            st.subheader("Análise do Banco de Dados:")
            st.json(analysis_result)
        else:
            st.error("Falha na conexão com o banco de dados.")

# =============================================================================
# GERAÇÃO DE DASHBOARDS
# =============================================================================
def generate_dashboard_plotly(df: pd.DataFrame) -> None:
    fig = px.bar(df, x=df.columns[0], y=df.columns[1], title="Dashboard Plotly")
    st.plotly_chart(fig)

def generate_dashboard_matplotlib(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots()
    ax.bar(df[df.columns[0]], df[df.columns[1]])
    ax.set_title("Dashboard Matplotlib")
    st.pyplot(fig)

def generate_dashboard_seaborn(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots()
    sns.barplot(x=df.columns[0], y=df.columns[1], data=df, ax=ax)
    ax.set_title("Dashboard Seaborn")
    st.pyplot(fig)

# Se o modo for "Análise" e o usuário solicitar "dashboard", processa a análise
def process_dashboard_request(dashboard_lib: str) -> None:
    if "db_connection" in st.session_state:
        db_type = st.session_state.get("db_type")
        connection = st.session_state.get("db_connection")
        analysis_result = analyze_database(connection, db_type)
        st.subheader("Dashboard from Data Analysis")
        # Exemplo de conversão dos resultados da análise para DataFrame
        if analysis_result:
            df = pd.DataFrame({
                "Category": list(analysis_result.keys()),
                "Value": [len(str(val)) for val in analysis_result.values()]
            })
        else:
            # DataFrame dummy se não houver análise
            df = pd.DataFrame({
                "Category": ["A", "B", "C", "D"],
                "Value": [10, 20, 15, 30]
            })
        if dashboard_lib == "Plotly":
            generate_dashboard_plotly(df)
        elif dashboard_lib == "Matplotlib":
            generate_dashboard_matplotlib(df)
        elif dashboard_lib == "Seaborn":
            generate_dashboard_seaborn(df)
    else:
        st.error("Nenhuma conexão de banco de dados encontrada para análise.")

# =============================================================================
# INTERFACE DO CHAT
# =============================================================================
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

st.markdown("<div class='chat-title'>FlowMind Agent AI 🤖</div>", unsafe_allow_html=True)
chat_container = st.container()

def render_chat() -> None:
    """Renderiza as mensagens de chat na interface."""
    with chat_container:
        for message in st.session_state["chat_messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

def process_user_input(user_input: str, audio_text: str = None) -> None:
    """Processa a entrada do usuário, atualiza o chat e gera resposta do modelo."""
    combined_input = user_input if user_input else ""
    if audio_text:
        combined_input += f"\n{audio_text}"
    st.session_state["chat_messages"].append({"role": "user", "content": combined_input})
    render_chat()

    # Se o modo for "Análise" e o input conter "dashboard", processa a requisição de dashboard
    if agent_mode == "Análise" and "dashboard" in user_input.lower():
        dashboard_lib = st.selectbox("Selecione a biblioteca para o Dashboard:", ["Plotly", "Matplotlib", "Seaborn"], key="dashboard_lib")
        process_dashboard_request(dashboard_lib)
        return

    prompt = get_prompt(user_input, agent_mode, audio_info=audio_text)
    start_time = time.time()
    try:
        with st.spinner("Generating response..."):
            response = chat_model.invoke(prompt).content
            # Valida a resposta usando schemas (pode ser expandido conforme necessário)
            if not validate_response(response):
                response = "The response did not pass validation."
    except Exception as e:
        show_error(f"Error generating response: {e}")
        response = "Sorry, an error occurred while generating the response."
    elapsed = time.time() - start_time
    if agent_mode in ["Pesquisa Web", "Análise"]:
        st.success(f"Processing completed in {elapsed:.1f} seconds!")

    st.session_state["chat_messages"].append({"role": "assistant", "content": response})
    render_chat()

# Entrada do usuário via chat
user_input = st.chat_input("Digite sua consulta:")
if user_input or audio_text:
    process_user_input(user_input, audio_text)

def save_history() -> None:
    """Salva o histórico do chat em um arquivo JSON."""
    try:
        with open("chatbot_agent_history.json", "w") as f:
            json.dump(st.session_state["chat_messages"], f)
    except Exception as e:
        show_error(f"Error saving chat history: {e}")

save_history()

# =============================================================================
# FOOTER CUSTOMIZADO
# =============================================================================
st.markdown(
    """
    <div class="custom-footer">
        <div class="footer-content">
            <div class="footer-logo">
                <img src="https://etheriumtech.com.br/wp-content/uploads/2024/04/LOGO-BRANCO.png" alt="Logo">
            </div>
            <div class="footer-center">
                FlowMind AI © 2025 - Todos os direitos reservados
            </div>
            <div class="footer-neon">
                💡⚡ Powered by Jeferson Rocha
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
