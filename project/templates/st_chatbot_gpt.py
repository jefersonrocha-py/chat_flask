import os
import logging
from dotenv import load_dotenv
import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import json
import requests

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

# Configurações do Ollama
OLLAMA_SERVER_URL = "http://localhost:11434"

# Verificar conexão com o servidor backend
def check_backend_connection():
    OLLAMA_SERVER_URL = "http://localhost:11434"
    try:
        response = requests.get(OLLAMA_SERVER_URL, timeout=5)
        if response.status_code == 200:
            return True
        else:
            st.error(f"Erro ao conectar ao servidor backend: Status Code {response.status_code}")
    except requests.exceptions.Timeout:
        st.error(f"Timeout ao tentar conectar ao servidor backend em {OLLAMA_SERVER_URL}.")
    except Exception as e:
        st.error(f"Erro ao conectar ao servidor backend: {e}")
    return False

# Executa a verificação da conexão
backend_connected = check_backend_connection()
if not backend_connected:
    st.warning("⚠️ O servidor backend não está disponível. Algumas funcionalidades podem estar limitadas.")

# Configurar o Ollama como provedor de chat
CHAT_MODEL = "llama3.2:latest"
try:
    chat_model = ChatOllama(base_url=OLLAMA_SERVER_URL, model=CHAT_MODEL)
except Exception as e:
    show_error(f"Erro ao configurar o modelo de chat: {e}")
    st.stop()

# CSS customizado para estilização
st.markdown(
    """
    <style>
    .css-18e3th9 { padding-top: 1rem; }
    .css-1d391kg { padding: 0; }
    .chat-title { font-size: 32px; font-weight: bold; text-align: center; margin-bottom: 10px; color: #4CAF50; }
    .sidebar-footer { position: fixed; bottom: 0; width: 250px; background-color: transparent; padding: 10px 0; text-align: center; box-shadow: none; }
    .avatar-container { display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
    .avatar-initial { width: 60px; height: 60px; border-radius: 50%; background-color: #4CAF50; color: white; font-size: 24px; font-weight: bold; display: flex; align-items: center; justify-content: center; margin-right: 0.5rem; }
    .back-button { background-color: #2196F3; color: white; padding: 0.6em 1em; border: none; border-radius: 20px; cursor: pointer; text-decoration: none; font-size: 16px; font-weight: bold; box-shadow: none; outline: none; transition: background-color 0.3s ease; }
    [data-testid="stSidebar"] .back-button { background-color: #2196F3; }
    [data-testid="stSidebar"][class*="dark"] .back-button { background-color: #1E88E5; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Obter o username dos parâmetros da URL
query_params = st.query_params
user_logged = query_params.get("username", ["Usuário"])[0]

# Função para gerar título automático da conversa
def generate_conversation_title(messages):
    try:
        if messages:
            content = messages[0]["content"]
            return content[:30] + "..." if len(content) > 30 else content
        return "Nova Conversa"
    except Exception as e:
        show_error(f"Erro ao gerar título da conversa: {e}")
        return "Nova Conversa"

# Função para salvar histórico em JSON
def save_history():
    try:
        with open("chat_history.json", "w") as f:
            json.dump({
                "conversation_history": st.session_state.conversation_history,
                "conversation_titles": st.session_state.conversation_titles
            }, f)
    except Exception as e:
        show_error(f"Erro ao salvar histórico: {e}")

def chatbot_gpt_page():
    st.markdown(
        """
        <div class="chat-title">FlowMind AI 🤖</div>
        """,
        unsafe_allow_html=True
    )

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

        st.header("📜 Histórico de Conversas")
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = []
        if "conversation_titles" not in st.session_state:
            st.session_state.conversation_titles = []
        if "current_conversation_index" not in st.session_state:
            st.session_state.current_conversation_index = None

        try:
            for i, history in enumerate(st.session_state.conversation_history):
                default_title = f"Conversa {i + 1}"
                title = st.session_state.conversation_titles[i] if i < len(st.session_state.conversation_titles) else default_title
                new_title = st.text_input(f"Título da conversa {i + 1}", value=title, key=f"title_{i}_input")
                if new_title != title:
                    if i < len(st.session_state.conversation_titles):
                        st.session_state.conversation_titles[i] = new_title
                    else:
                        st.session_state.conversation_titles.append(new_title)
                if st.button(f"Selecionar {title}", key=f"select_{i}"):
                    st.session_state.current_conversation_index = i
                    st.session_state.current_messages = history.copy()
            if st.button("✨ Iniciar novo Chat", key="new_chat", help="Clique para começar uma nova conversa"):
                st.session_state.current_messages = []
                st.session_state.current_conversation_index = len(st.session_state.conversation_history)
                st.session_state.conversation_titles.append("Nova Conversa")
                st.success("Nova conversa iniciada!")
        except Exception as e:
            show_error(f"Erro ao gerenciar histórico de conversas: {e}")

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

    # Template do prompt
    conversation_prompt = ChatPromptTemplate.from_template(
        """
        Você é um assistente virtual especializado. 
        Forneça respostas claras, concisas e úteis com base no contexto da conversa.
        Mensagens anteriores:
        {history}
        Nova pergunta do usuário:
        {user_input}
        """
    )

    if "current_messages" not in st.session_state:
        st.session_state.current_messages = []

    try:
        for message in st.session_state.current_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html=True)
    except Exception as e:
        show_error(f"Erro ao exibir mensagens: {e}")

    # Entrada do usuário
    if user_input := st.chat_input("Digite sua mensagem aqui:"):
        st.session_state.current_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        try:
            previous_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.current_messages
            ]
            prompt = conversation_prompt.format(
                history="\n".join(f"{msg['role']}: {msg['content']}" for msg in previous_messages),
                user_input=user_input
            )
            with st.spinner("Gerando resposta..."):
                response_stream = chat_model.stream(prompt)
                full_response = ""
                response_container = st.chat_message("assistant")
                response_text = response_container.empty()
                for partial_response in response_stream:
                    content = partial_response.content
                    full_response += content
                    response_text.markdown(full_response + "▌", unsafe_allow_html=True)
                st.session_state.current_messages.append({"role": "assistant", "content": full_response})
                save_history()
        except Exception as e:
            show_error(f"Erro ao gerar resposta: {e}")

    # Salva a conversa no histórico
    try:
        if st.session_state.current_messages:
            idx = st.session_state.current_conversation_index
            if idx is None or idx >= len(st.session_state.conversation_history):
                st.session_state.conversation_history.append(st.session_state.current_messages.copy())
                st.session_state.conversation_titles.append(generate_conversation_title(st.session_state.current_messages))
                st.session_state.current_conversation_index = len(st.session_state.conversation_history) - 1
            else:
                st.session_state.conversation_history[idx] = st.session_state.current_messages.copy()
                st.session_state.conversation_titles[idx] = generate_conversation_title(st.session_state.current_messages)
            save_history()
    except Exception as e:
        show_error(f"Erro ao salvar conversa no histórico: {e}")

# Executa a página
try:
    chatbot_gpt_page()
except Exception as e:
    show_error(f"Erro crítico na aplicação: {e}")