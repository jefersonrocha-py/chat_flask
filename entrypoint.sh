#!/bin/bash

# Inicia o Flask na porta 5000
python app.py &

# Inicia o Streamlit Assistente na porta 8501
streamlit run project/templates/st_chatbot_assistente.py --server.port 8501 &

# Inicia o Streamlit GPT na porta 8502
streamlit run project/templates/st_chatbot_gpt.py --server.port 8502 &

# Mantém o contêiner rodando
wait