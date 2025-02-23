import os
import logging
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
    logging.error(message)

# Configurações do Ollama
OLLAMA_SERVER_URL = "http://localhost:11434"
CHAT_MODEL = "llama3.2:latest"

# Verificar conexão com o servidor backend
def check_backend_connection():
    try:
        import requests
        response = requests.get(OLLAMA_SERVER_URL, timeout=5)
        if response.status_code == 200:
            models_response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags", timeout=5)
            available_models = models_response.json().get("models", [])
            if CHAT_MODEL not in [model["name"] for model in available_models]:
                show_error(f"Modelo '{CHAT_MODEL}' não encontrado no servidor.")
                return False
            return True
        else:
            show_error(f"Erro ao conectar ao servidor backend: Status Code {response.status_code}")
    except Exception as e:
        show_error(f"Erro ao conectar ao servidor backend: {e}")
    return False

# Configurar o modelo de chat
try:
    chat_model = ChatOllama(base_url=OLLAMA_SERVER_URL, model=CHAT_MODEL)
except Exception as e:
    show_error(f"Erro ao configurar o modelo de chat: {e}")

# Template do prompt
conversation_prompt = ChatPromptTemplate.from_template(
    """
    Você é um assistente virtual amigável. Ajude os usuários com respostas claras, precisas e úteis.
    Mensagens anteriores:
    {history}
    Nova pergunta do usuário:
    {user_input}
    """
)

def generate_conversation_title(messages):
    try:
        if not messages or "content" not in messages[0]:
            return "Nova Conversa"
        first_message = messages[0]["content"]
        return first_message[:30] + "..." if len(first_message) > 30 else first_message
    except Exception as e:
        show_error(f"Erro ao gerar título da conversa: {e}")
        return "Nova Conversa"

def chatbot_gpt_logic(user_input, history):
    try:
        prompt = conversation_prompt.format(
            history="\n".join(f"{msg['role']}: {msg['content']}" for msg in history),
            user_input=user_input
        )
        response_stream = chat_model.stream(prompt)
        full_response = ""
        for partial_response in response_stream:
            full_response += str(partial_response.content)
        return full_response
    except Exception as e:
        show_error(f"Erro ao gerar resposta: {e}")
        return None