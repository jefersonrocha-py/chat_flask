#!/bin/bash

# Inicia o Flask no VSCode

python3 project/app.py &

# Inicia o Flask com Gunicorn na porta 5000 com timeout ajustado
gunicorn -w 4 --timeout 120 -b 0.0.0.0:5000 app:app &

# Inicia o Streamlit Assistente na porta 8501
streamlit run templates/st_chatbot_assistente.py --server.port 8501 &

# Inicia o Streamlit GPT na porta 8502
streamlit run templates/st_chatbot_gpt.py --server.port 8502 &

# Inicia o Streamlit Coder na porta 8503
streamlit run templates/st_chatbot_agent.py --server.port 8503 &
# Mantém o contêiner rodando
wait
