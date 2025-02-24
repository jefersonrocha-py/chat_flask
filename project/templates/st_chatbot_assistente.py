import os
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
from langchain_core.runnables import RunnablePassthrough

# Configuração de logging
logging.basicConfig(
    filename="chatbot_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Função para exibir mensagens de erro amigáveis
def show_error(message):
    st.error(f"😕 Oops! Algo deu errado: {message}")
    logging.error(message)

# Carregar variáveis de ambiente
try:
    load_dotenv()
except Exception as e:
    show_error(f"Não foi possível carregar variáveis de ambiente: {e}")

# Configurações do Ollama (definir antes de qualquer uso)
OLLAMA_SERVER_URL = "http://localhost:11434"

# Verificar conexão com o servidor backend
def check_backend_connection():
    try:
        import requests
        response = requests.get(OLLAMA_SERVER_URL, timeout=5)
        if response.status_code == 200:
            st.success("✅ Conexão com o servidor backend estabelecida!")
            return True
        else:
            show_error(f"Erro ao conectar ao servidor backend: Status Code {response.status_code}")
    except requests.exceptions.Timeout:
        show_error(f"Timeout ao tentar conectar ao servidor backend em {OLLAMA_SERVER_URL}.")
    except Exception as e:
        show_error(f"Erro ao conectar ao servidor backend: {e}")
    return False

# Verificar conexão antes de prosseguir
backend_connected = check_backend_connection()

if not backend_connected:
    st.warning("⚠️ O servidor backend não está disponível. Algumas funcionalidades podem estar limitadas.")

# Configurar o Ollama como provedor de embeddings e chat
try:
    embeddings = OllamaEmbeddings(base_url=OLLAMA_SERVER_URL, model="llama3.2:latest")
    chat_model = ChatOllama(base_url=OLLAMA_SERVER_URL, model="llama3.2:latest")
except Exception as e:
    show_error(f"Erro ao configurar embeddings ou chat model: {e}")
    st.stop()

# Criar diretório para armazenar arquivos
DOCUMENTS_DIR = "/utils/uploads/files"
try:
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
except Exception as e:
    show_error(f"Erro ao criar diretório: {e}")
    st.stop()

# Funções para processar diferentes tipos de arquivos
def process_csv(file_path):
    """Processa arquivos CSV."""
    try:
        df = pd.read_csv(file_path)
        return [{"page_content": row.to_string()} for _, row in df.iterrows()]
    except Exception as e:
        show_error(f"Erro ao processar CSV: {e}")
        return None

def process_xlsx(file_path):
    """Processa arquivos Excel."""
    try:
        df = pd.read_excel(file_path)
        return [{"page_content": row.to_string()} for _, row in df.iterrows()]
    except Exception as e:
        show_error(f"Erro ao processar Excel: {e}")
        return None

def process_docx(file_path):
    """Processa arquivos Word."""
    try:
        doc = Document(file_path)
        full_text = [p.text for p in doc.paragraphs if p.text.strip()]
        return [{"page_content": text} for text in full_text]
    except Exception as e:
        show_error(f"Erro ao processar DOCX: {e}")
        return None

def process_pdf(file_path):
    """Processa arquivos PDF."""
    try:
        reader = PdfReader(file_path)
        pages = [page.extract_text() for page in reader.pages if page.extract_text()]
        return [{"page_content": text} for text in pages]
    except Exception as e:
        show_error(f"Erro ao processar PDF: {e}")
        return None

def process_txt(file_path):
    """Processa arquivos TXT."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return [{"page_content": text}]
    except Exception as e:
        show_error(f"Erro ao processar TXT: {e}")
        return None

@st.cache_data
def load_data(file_path):
    """Carrega o arquivo e gera o retriever para busca."""
    try:
        file_type = file_path.split('.')[-1].lower()
        if file_type == 'csv':
            documents_raw = process_csv(file_path)
        elif file_type in ['xlsx', 'xls', 'xml']:
            documents_raw = process_xlsx(file_path)
        elif file_type == 'docx':
            documents_raw = process_docx(file_path)
        elif file_type == 'pdf':
            documents_raw = process_pdf(file_path)
        elif file_type == 'txt':
            documents_raw = process_txt(file_path)
        else:
            show_error("Formato de arquivo não suportado. Use .csv, .xlsx, .docx, .pdf ou .txt.")
            return None
        if not documents_raw:
            show_error("Nenhum dado foi processado do arquivo.")
            return None
        documents = [LangChainDocument(page_content=doc["page_content"]) for doc in documents_raw]
        vectorstore = FAISS.from_documents(documents, embeddings)
        return vectorstore.as_retriever()
    except Exception as e:
        show_error(f"Erro ao carregar dados: {e}")
        return None

# Função para verificar arquivos no diretório
def check_files_in_directory():
    """Verifica se existem arquivos no diretório e retorna o caminho do primeiro arquivo encontrado."""
    try:
        files = os.listdir(DOCUMENTS_DIR)
        if files:
            return os.path.join(DOCUMENTS_DIR, files[0])
        return None
    except Exception as e:
        show_error(f"Erro ao verificar diretório: {e}")
        return None

# CSS customizado para estilização
st.markdown(
    """
    <style>
    /* Estilo geral */
    .css-18e3th9 {
        padding-top: 1rem;
    }
    .css-1d391kg {
        padding: 0;
    }

    /* Avatar */
    .avatar-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
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
        margin-right: 0.5rem;
    }

    /* Botão Voltar */
    .back-button {
        background-color: #2196F3; /* Azul */
        color: white;
        padding: 0.6em 1em;
        border: none;
        border-radius: 20px; /* Arredondado */
        cursor: pointer;
        text-decoration: none;
        font-size: 16px;
        font-weight: bold;
        box-shadow: none; /* Sem sombra */
        outline: none; /* Remove o contorno branco */
        transition: background-color 0.3s ease; /* Transição suave */
    }

    /* Adaptação para tema Light */
    [data-testid="stSidebar"] .back-button {
        background-color: #2196F3; /* Azul padrão */
    }

    /* Adaptação para tema Dark */
    [data-testid="stSidebar"][class*="dark"] .back-button {
        background-color: #1E88E5; /* Azul mais escuro para o tema Dark */
    }

    /* Rodapé da sidebar */
    .sidebar-footer {
        position: fixed;
        bottom: 0;
        width: 250px; /* Largura da sidebar */
        background-color: transparent; /* Fundo transparente para adaptar ao tema */
        padding: 10px 0;
        text-align: center;
        box-shadow: none; /* Sem sombra */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Captura os parâmetros "full_name" da query string e salva na sessão
params = st.query_params
if "full_name" in params:
    st.session_state["full_name"] = params["full_name"][0]

def chatbot_assistente_page():
    # Título do chatbot (na área principal)
    st.markdown('🚀 FlowMind AI - AI da Etheriumtech 🤖', unsafe_allow_html=True)
    
    # Verifica se há um arquivo disponível no diretório
    initial_file = check_files_in_directory()
    retriever = None
    if initial_file:
        # Verifica se já existe um retriever carregado na sessão
        if "retriever" not in st.session_state or st.session_state["current_file"] != initial_file:
            st.info(f"📄 Arquivo detectado no diretório: {os.path.basename(initial_file)}. Carregando...")
            retriever = load_data(initial_file)
            st.session_state["retriever"] = retriever
            st.session_state["current_file"] = initial_file
        else:
            retriever = st.session_state["retriever"]
    
    # Área lateral (sidebar)
    with st.sidebar:
        # Exibir avatar no topo da sidebar com a inicial do usuário
        full_name = st.session_state.get("full_name", "Usuário")
        initial = full_name[0].upper() if full_name else "U"
        st.markdown(
            f"""
            <div class="avatar-container">
                <div class="avatar-initial">{initial}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.header("📁 Upload dos Files")
        uploaded_file = st.file_uploader(
            "Envie sua base de conhecimento (.csv, .xml, .xls, .xlsx, .docx, .pdf, .txt)",
            type=['csv', 'xml', 'xls', 'xlsx', 'docx', 'pdf', 'txt']
        )
        if uploaded_file:
            try:
                file_path = os.path.join(DOCUMENTS_DIR, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ Arquivo {uploaded_file.name} carregado com sucesso!")
                # Atualiza o retriever apenas se o arquivo for diferente
                if "current_file" not in st.session_state or st.session_state["current_file"] != file_path:
                    retriever = load_data(file_path)
                    st.session_state["retriever"] = retriever
                    st.session_state["current_file"] = file_path
            except Exception as e:
                show_error(f"Erro ao salvar arquivo: {e}")

        # Botão "Voltar" no rodapé da sidebar
        FLASK_ROUTE = "http://localhost:5000/mode_selection"
        st.markdown(
            f"""
            <div class="sidebar-footer">
                <a href="{FLASK_ROUTE}" target="_self" style="text-decoration: none;">
                    <button class="back-button">🔙 Voltar</button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Se houver retriever, exibe a interface do chat
    if retriever:
        rag_template = """
        Você é um assistente virtual. 
        Seu trabalho é ajudar os usuários com base nas informações fornecidas no arquivo.
        Forneça respostas curtas, claras e precisas.
        Contexto: {context}
        Pergunta do cliente: {question}
        """
        prompt = ChatPromptTemplate.from_template(rag_template)
        chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | chat_model
        )
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Exibe o histórico de mensagens
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Entrada do usuário
        if user_input := st.chat_input("Você:"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            try:
                response_stream = chain.stream({"text": user_input})
                full_response = ""
                response_container = st.chat_message("assistant")
                response_text = response_container.empty()
                for partial_response in response_stream:
                    full_response += str(partial_response.content)
                    response_text.markdown(full_response + "▌")
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                show_error(f"Erro ao gerar resposta: {e}")
    else:
        st.info("📂 Use a aba à esquerda para carregar um arquivo e começar.")

# Executa a página do chatbot
try:
    chatbot_assistente_page()
except Exception as e:
    show_error(f"Erro crítico na aplicação: {e}")