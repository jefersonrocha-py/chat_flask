import os
import requests
import logging
import pandas as pd
import streamlit as st
from io import StringIO
from docx import Document
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.schema import Document as LangChainDocument
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import json
import hashlib
import mysql.connector
import psycopg2
from pymongo import MongoClient
from sqlalchemy import create_engine, inspect

# Configuração de logging
logging.basicConfig(
    filename="chatbot_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def show_error(message):
    st.error(f"🥺 Oops! Algo deu errado: {message}")
    logging.error(message)

try:
    load_dotenv()
except Exception as e:
    show_error(f"Não foi possível carregar variáveis de ambiente: {e}")

OLLAMA_SERVER_URL = "http://localhost:11434"

def check_backend_connection():
    try:
        response = requests.get(OLLAMA_SERVER_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

backend_connected = check_backend_connection()
if not backend_connected:
    st.warning("⚠️ O servidor backend não está disponível. Algumas funcionalidades podem estar limitadas.")

try:
    embeddings = OllamaEmbeddings(base_url=OLLAMA_SERVER_URL, model="llama3.2:latest")
    chat_model = ChatOllama(base_url=OLLAMA_SERVER_URL, model="llama3.2:latest")
except Exception as e:
    show_error(f"Erro ao configurar embeddings ou chat model: {e}")
    st.stop()

DOCUMENTS_DIR = "utils/uploads/files"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.chmod(DOCUMENTS_DIR, 0o700)

# Processamento de arquivos
def process_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return [LangChainDocument(page_content=row.to_string()) for _, row in df.iterrows()]
    except Exception as e:
        show_error(f"Erro CSV: {e}")
        return None

def process_xlsx(file_path):
    try:
        df = pd.read_excel(file_path)
        return [LangChainDocument(page_content=row.to_string()) for _, row in df.iterrows()]
    except Exception as e:
        show_error(f"Erro Excel: {e}")
        return None

def process_docx(file_path):
    try:
        doc = Document(file_path)
        return [LangChainDocument(page_content=p.text) for p in doc.paragraphs if p.text.strip()]
    except Exception as e:
        show_error(f"Erro DOCX: {e}")
        return None

def process_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        return [LangChainDocument(page_content=page.extract_text()) for page in reader.pages]
    except Exception as e:
        show_error(f"Erro PDF: {e}")
        return None

def process_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [LangChainDocument(page_content=f.read())]
    except Exception as e:
        show_error(f"Erro TXT: {e}")
        return None

def validate_file(uploaded_file):
    allowed_types = ['csv', 'xml', 'xls', 'xlsx', 'docx', 'pdf', 'txt']
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in allowed_types:
        raise ValueError("Tipo não suportado. Use .csv, .xml, .xls, .xlsx, .docx, .pdf ou .txt.")

def get_file_hash(file_path):
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        show_error(f"Erro hash: {e}")
        return None

@st.cache_data
def create_file_retriever(file_path, _file_hash):
    try:
        docs = []
        if file_path.endswith('.csv'):
            docs = process_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls', '.xml')):
            docs = process_xlsx(file_path)
        elif file_path.endswith('.docx'):
            docs = process_docx(file_path)
        elif file_path.endswith('.pdf'):
            docs = process_pdf(file_path)
        elif file_path.endswith('.txt'):
            docs = process_txt(file_path)
            
        if not docs:
            return None
            
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore.as_retriever()
    except Exception as e:
        show_error(f"Erro carregar dados: {e}")
        return None

# Processamento de bancos de dados
def get_mysql_data(engine):
    try:
        tables = inspect(engine).get_table_names()
        return [pd.read_sql(f"SELECT * FROM {table}", engine) for table in tables]
    except Exception as e:
        show_error(f"Erro MySQL: {e}")
        return []

def get_postgresql_data(engine):
    try:
        tables = inspect(engine).get_table_names()
        return [pd.read_sql(f"SELECT * FROM {table}", engine) for table in tables]
    except Exception as e:
        show_error(f"Erro PostgreSQL: {e}")
        return []

def get_mongodb_data(db):
    try:
        collections = db.list_collection_names()
        return [pd.DataFrame(list(db[coll].find())) for coll in collections]
    except Exception as e:
        show_error(f"Erro MongoDB: {e}")
        return []

def create_db_retriever(db_type, host, user, password, database):
    try:
        if db_type == "MySQL":
            engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}")
            data = get_mysql_data(engine)
        elif db_type == "PostgreSQL":
            engine = create_engine(f"postgresql://{user}:{password}@{host}/{database}")
            data = get_postgresql_data(engine)
        elif db_type == "MongoDB":
            client = MongoClient(f"mongodb://{user}:{password}@{host}/{database}")
            db = client[database]
            data = get_mongodb_data(db)
        else:
            return None
            
        docs = []
        for df in data:
            for _, row in df.iterrows():
                docs.append(LangChainDocument(
                    page_content=f"[BANCO] Tabela: {df.name}\n{row.to_string()}"
                ))
                
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore.as_retriever()
    except Exception as e:
        show_error(f"Erro BD: {e}")
        return None

# Sistema híbrido
def hybrid_retriever(question):
    contexts = []
    
    # Recupera dados de arquivos
    if st.session_state.get("file_retriever"):
        contexts += st.session_state.file_retriever.get_relevant_documents(question)
        
    # Recupera dados do banco
    if st.session_state.get("use_database") and st.session_state.get("db_retriever"):
        contexts += st.session_state.db_retriever.get_relevant_documents(question)
        
    return "\n".join([doc.page_content for doc in contexts])

def create_chain():
    prompt = ChatPromptTemplate.from_template("""
    Você tem acesso a:
    1. Documentos: {file_context}
    2. Banco de Dados: {db_context}
    
    Responda com base nas informações disponíveis:
    Pergunta: {question}
    """)
    
    return (
        {"file_context": RunnableLambda(lambda q: hybrid_retriever(q)), 
         "db_context": RunnableLambda(lambda q: hybrid_retriever(q)) if st.session_state.get("use_database") else "",
         "question": RunnablePassthrough()}
        | prompt
        | chat_model
    )

# Interface principal
def chatbot_assistente_page():
    st.markdown(
        """
        <div class="chat-title">FlowMind AI 🤖</div>
        """,
        unsafe_allow_html=True
    )
    
    # Inicializa componentes
    if "file_retriever" not in st.session_state:
        st.session_state.file_retriever = None
    if "db_retriever" not in st.session_state:
        st.session_state.db_retriever = None
    if "use_database" not in st.session_state:
        st.session_state.use_database = False
    if "chain" not in st.session_state:
        st.session_state.chain = create_chain()

    # Verifica arquivos existentes
    initial_file = check_files_in_directory()
    if initial_file and not st.session_state.file_retriever:
        file_hash = get_file_hash(initial_file)
        retriever = create_file_retriever(initial_file, file_hash)
        if retriever:
            st.session_state.file_retriever = retriever
            st.session_state.chain = create_chain()

    with st.sidebar:
        initial = user_logged[0].upper() if user_logged else "U"
        st.markdown(
            f"""
            <div class="avatar-container">
                <div class="avatar-initial">{initial}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.header("📁 Upload de Arquivos")
        uploaded_files = st.file_uploader(
            "Carregue documentos (.csv, .xml, .xls, .xlsx, .docx, .pdf, .txt)",
            type=['csv', 'xml', 'xls', 'xlsx', 'docx', 'pdf', 'txt'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    validate_file(uploaded_file)
                    file_path = os.path.join(DOCUMENTS_DIR, uploaded_file.name)
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    with st.spinner(f"Processando {uploaded_file.name}..."):
                        file_hash = get_file_hash(file_path)
                        retriever = create_file_retriever(file_path, file_hash)
                    if retriever:
                        st.session_state.file_retriever = retriever
                        st.session_state.chain = create_chain()
                        st.success(f"✅ {uploaded_file.name} processado")
                except ValueError as ve:
                    show_error(str(ve))
                except Exception as e:
                    show_error(f"Erro no upload: {e}")

        st.markdown("---")
        st.header("🗄️ Conexão com Banco de Dados")
        use_database = st.checkbox(" Usar Banco de Dados")
        if use_database:
            db_type = st.selectbox("Tipo", ["MySQL", "PostgreSQL", "MongoDB"])
            host = st.text_input("Host/IP")
            database = st.text_input("Banco")
            user = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            if st.button(" Conectar Banco"):
                with st.spinner("Conectando..."):
                    db_retriever = create_db_retriever(db_type, host, user, password, database)
                    if db_retriever:
                        st.session_state.db_retriever = db_retriever
                        st.session_state.use_database = True
                        st.session_state.chain = create_chain()
                        st.success("✅ Banco conectado!")

        FLASK_ROUTE = "http://localhost:5000/mode_selection"
        st.markdown(
            f"""
            <div class="sidebar-footer">
                <a href="{FLASK_ROUTE}" target="_self">
                    <button class="back-button">🛠️ Voltar</button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Verifica fontes de dados
    if not st.session_state.file_retriever and not st.session_state.db_retriever:
        st.info("Você precisa carregar um arquivo ou conectar um banco de dados.")
        return

    # Interface de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Você:"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        try:
            with st.chat_message("assistant"):
                response = st.session_state.chain.invoke(user_input)
                st.markdown(response.content)
                st.session_state.messages.append({"role": "assistant", "content": response.content})
                save_history()
        except Exception as e:
            show_error(f"Erro na resposta: {e}")

    # Footer
    st.markdown("""
        <div class="custom-footer">
            <div class="footer-content">
                <div class="footer-logo">
                    <img src="https://etheriumtech.com.br/wp-content/uploads/2024/04/LOGO-BRANCO.png">
                </div>
                <div class="footer-center">
                    FlowMind AI © 2025 - Todos direitos reservados
                </div>
                <div class="footer-neon">
                    💡⚡ Powered by Jeferson Rocha
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def check_files_in_directory():
    try:
        files = os.listdir(DOCUMENTS_DIR)
        return os.path.join(DOCUMENTS_DIR, files[0]) if files else None
    except Exception as e:
        show_error(f"Erro diretório: {e}")
        return None

def save_history():
    try:
        with open("chat_history.json", "w") as f:
            json.dump(st.session_state.messages, f)
    except Exception as e:
        show_error(f"Erro salvar histórico: {e}")

try:
    chatbot_assistente_page()
except Exception as e:
    show_error(f"Erro crítico: {e}")
    st.stop()