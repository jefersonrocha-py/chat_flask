import os
import logging
from dotenv import load_dotenv
import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

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

# Configurar o Ollama como provedor de chat
CHAT_MODEL = "deepseek-r1:1.5b"
try:
    chat_model = ChatOllama(base_url=OLLAMA_SERVER_URL, model=CHAT_MODEL)
except Exception as e:
    show_error(f"Erro ao configurar o modelo de chat: {e}")
    st.stop()

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
    .chat-title {
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
        color: #4CAF50;
    }
    .chat-subtitle {
        font-size: 32px;
        font-weight: normal;
        text-align: center;
        margin-bottom: 20px;
        color: #4CAF50;
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
    </style>
    """,
    unsafe_allow_html=True,
)

# Obter o username dos parâmetros da URL enviados pelo Flask
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

def chatbot_gpt_page():
    st.markdown(
        """
        <div class="chat-title">🚀 FlowMind AI</div>
        <div class="chat-subtitle">AI da Etheriumtech 🤖</div>
        """,
        unsafe_allow_html=True
    )

    # Sidebar para histórico de conversas e Modo DeepThink
    with st.sidebar:
        # Exibir avatar no topo da sidebar com a inicial do usuário
        initial = user_logged[0].upper() if user_logged else "U"
        st.markdown(
            f"""
            <div class="avatar-container">
                <div class="avatar-initial">{initial}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Adicionar checkbox para o Modo DeepThink
        deep_think_mode = st.checkbox("🧠 Ativar Modo DeepThink", value=False)
        if deep_think_mode:
            st.info("No Modo DeepThink, o chatbot mostrará seu processo de pensamento antes de responder.")

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
            # Botão para iniciar novo chat
            if st.button("✨ Iniciar novo Chat", key="new_chat", help="Clique para começar uma nova conversa"):
                st.session_state.current_messages = []
                st.session_state.current_conversation_index = len(st.session_state.conversation_history)
                st.session_state.conversation_titles.append("Nova Conversa")
                st.success("Nova conversa iniciada!")
        except Exception as e:
            show_error(f"Erro ao gerenciar histórico de conversas: {e}")

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

    # Definir a instrução de pensamento com base no modo
    if deep_think_mode:
        think_instruction = "Pense passo a passo antes de responder. Mostre seu raciocínio.\n"
    else:
        think_instruction = ""

    # Template do prompt para o chat
    conversation_prompt = ChatPromptTemplate.from_template(
        f"""
        {think_instruction}
        Você é um assistente virtual amigável. Ajude os usuários com respostas claras, precisas e úteis.
        Mensagens anteriores:
        {{history}}
        Nova pergunta do usuário:
        {{user_input}}
        """
    )

    # Inicializa a lista de mensagens da conversa atual se não existir
    if "current_messages" not in st.session_state:
        st.session_state.current_messages = []

    # Exibe o histórico de mensagens da conversa atual
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
        # Gera a resposta utilizando o modelo de chat
        try:
            previous_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.current_messages
            ]
            prompt = conversation_prompt.format(
                history="\n".join(f"{msg['role']}: {msg['content']}" for msg in previous_messages),
                user_input=user_input
            )
            response_stream = chat_model.stream(prompt)
            full_response = ""
            response_container = st.chat_message("assistant")
            response_text = response_container.empty()
            for partial_response in response_stream:
                content = partial_response.content
                # Formatar etapas de pensamento em itálico no Modo DeepThink
                if deep_think_mode and content.strip().startswith(("1.", "2.", "3.", "•", "-")):
                    formatted_content = f"<i>{content}</i>"
                else:
                    formatted_content = content
                full_response += formatted_content
                response_text.markdown(full_response + "▌", unsafe_allow_html=True)
            # Remover o cursor "▌" da resposta final salva no histórico
            st.session_state.current_messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            show_error(f"Erro ao gerar resposta: {e}")

    # Salva automaticamente a conversa atual no histórico
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
    except Exception as e:
        show_error(f"Erro ao salvar conversa no histórico: {e}")

# Executa a página do chatbot
try:
    chatbot_gpt_page()
except Exception as e:
    show_error(f"Erro crítico na aplicação: {e}")