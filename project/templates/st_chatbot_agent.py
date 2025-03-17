import os
import requests
import logging
import time
import streamlit as st
from dotenv import load_dotenv
import json
from langchain_community.chat_models import ChatOllama

# Configuração de logging
logging.basicConfig(
    filename="chatbot_agent_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def show_error(message):
    st.error(f"❌ Oops! Algo deu errado: {message}")
    logging.error(message)

load_dotenv()

# Configuração do Ollama
OLLAMA_SERVER_URL = "http://localhost:11434"

def check_backend_connection():
    try:
        response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Erro ao conectar no backend do Ollama: {e}")
        return False

if not check_backend_connection():
    st.error("Servidor Ollama não disponível. Inicie o servidor e tente novamente.")
    st.stop()

try:
    chat_model = ChatOllama(base_url=OLLAMA_SERVER_URL, model="llama3.2:latest")
except Exception as e:
    show_error(f"Erro ao configurar o chat model: {e}")
    st.stop()

# CSS customizado (mantido igual ao original)
st.markdown("""
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
    """, unsafe_allow_html=True)

# Botão de voltar na sidebar
FLASK_ROUTE = "http://localhost:5000/mode_selection"
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

# Seleção de modo de operação na sidebar
st.sidebar.title("Mode Agent")
agent_mode = st.sidebar.selectbox(
    "Modo de Operação:",
    options=["Educacional", "Pesquisa Web", "Análise"]
)

# Botão para limpar o histórico (opcional)
if st.sidebar.button("Limpar Histórico"):
    st.session_state["chat_messages"] = []
    st.success("Histórico limpo com sucesso!")

# No modo Educacional, exibe o uploader de áudio na sidebar
audio_text = None
if agent_mode == "Educacional":
    audio_file = st.sidebar.file_uploader("Envie um arquivo de áudio (mp3, wav)", type=["mp3", "wav"])
    if audio_file is not None:
        audio_text = "Áudio recebido para correção. (Simulação de transcrição)"
        st.sidebar.info("Áudio recebido! Transcrição simulada disponível.")

# Informações adicionais para cada modo
if agent_mode == "Educacional":
    st.sidebar.info("Foco: Correção e Ensino de Inglês, Espanhol e Francês (áudio/texto).")
elif agent_mode == "Pesquisa Web":
    st.sidebar.info("Foco: Respostas fundamentadas e detalhadas com base na web.")
elif agent_mode == "Análise":
    st.sidebar.info("Foco: Resumir artigos, extrair insights de dados e analisar documentos.")

# Função para montar o prompt conforme o modo selecionado
def get_prompt(query: str, mode: str, audio_info: str = None) -> str:
    if mode == "Educacional":
        prefix = (
            "Você é um especialista educacional focado em ensinar e corrigir idiomas (Inglês, Espanhol e Francês). "
            "Se o usuário enviar áudio, transcreva, corrija a pronúncia, identifique erros e forneça feedback detalhado, "
            "incluindo dicas de gramática, vocabulário e pronúncia. Se o usuário enviar texto, corrija e sugira melhorias."
        )
    elif mode == "Pesquisa Web":
        prefix = (
            "Você é um agente de pesquisa especializado em fornecer respostas detalhadas e fundamentadas com base na web. "
            "Forneça informações precisas, explique conceitos e, se necessário, cite fontes relevantes."
        )
    elif mode == "Análise":
        prefix = (
            "Você é um agente de pesquisa e análise. Sua tarefa é resumir artigos, extrair insights de dados e analisar documentos. "
            "Utilize conexões com APIs relevantes (como Google Scholar e PubMed) e processe PDFs, HTML ou textos longos para fornecer "
            "resumos e insights detalhados."
        )
    else:
        prefix = ""
    full_query = query if query else "[Áudio enviado]"
    if audio_info:
        full_query += f"\nÁudio: {audio_info}"
    return f"{prefix}\nConsulta do usuário: {full_query}"

# Inicializa o histórico do chat na sessão
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

st.markdown("<div class='chat-title'>FlowMind Agent AI🤖</div>", unsafe_allow_html=True)

# Exibe o histórico do chat
for message in st.session_state["chat_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do usuário (texto)
user_input = st.chat_input("Digite sua consulta:")

# Se houver entrada do usuário ou áudio, processa a consulta
if user_input or audio_text:
    combined_input = user_input if user_input else ""
    if audio_text:
        combined_input += f"\n{audio_text}"
    st.session_state["chat_messages"].append({"role": "user", "content": combined_input})
    
    prompt = get_prompt(user_input, agent_mode, audio_info=audio_text)
    
    # Processamento com spinner e tempo de pesquisa
    start_time = time.time()
    try:
        with st.spinner("Gerando resposta..."):
            response = chat_model.invoke(prompt).content
    except Exception as e:
        show_error(f"Erro ao gerar resposta: {e}")
        response = "Desculpe, ocorreu um erro ao gerar a resposta."
    
    elapsed = time.time() - start_time
    
    # Exibe o tempo de pesquisa apenas para Pesquisa Web e Análise
    if agent_mode in ["Pesquisa Web", "Análise"]:
        st.success(f"Pesquisa concluída em {elapsed:.1f} segundos!")
    
    st.session_state["chat_messages"].append({"role": "assistant", "content": response})

# Função para salvar o histórico do chat
def save_history():
    try:
        with open("chat_history.json", "w") as f:
            json.dump(st.session_state["chat_messages"], f)
    except Exception as e:
        show_error(f"Erro ao salvar histórico: {e}")

save_history()

# Footer customizado (mantido igual ao original)
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