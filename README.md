# chat_flask
 
# FlowMind AI

FlowMind AI é uma aplicação web que oferece dois modos de interação com modelos de IA: Modo Assistente (RAG) e Modo GPT.

## Funcionalidades

- **Autenticação**: Login e registro de usuários.
- **Modo Assistente (RAG)**: Respostas baseadas em documentos específicos.
- **Modo GPT**: Conversas gerais com o modelo GPT.


chat_etheriumtech/
project/
│
├── app.py                     # Arquivo principal do Flask
├── requirements.txt           # Dependências do projeto
├── static/                    # Arquivos estáticos (CSS, JS, imagens, etc.)
│   ├── styles.css             # Estilos CSS
│   ├── particles.js           # Biblioteca particles.js
│   └── particles-config.json  # Configuração das partículas
├── templates/                 # Templates HTML
│   ├── base.html              # Template base
│   ├── index.html             # Página inicial
│   ├── login.html             # Página de login
│   ├── register.html          # Página de registro
│   ├── mode_selection.html    # Página de seleção de modo
│   ├── chatbot_assistente.html # Página do Modo Assistente
│   └── chatbot_gpt.html       # Página do Modo GPT
├── utils/                     # Utilitários
│   ├── database.py            # Funções de banco de dados
│   ├── helpers.py             # Funções auxiliares
│   ├── chatbot_assistente.py  # Lógica do Modo Assistente
│   └── chatbot_gpt.py         # Lógica do Modo GPT
└── Dockerfile                 # Criar imagem
└── docker-compose.yml         # Docker Compose
└── README.md                  # Documentação do projeto
