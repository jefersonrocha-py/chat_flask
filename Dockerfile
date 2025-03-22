# Base image
FROM python:3.10-slim

# Instala as dependências do sistema necessárias (incluindo unixodbc-dev)
RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários para o contêiner
COPY . .

# Update no pip install
#pip install --upgrade pip

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Torna o script de inicialização executável
RUN chmod a+x project/entrypoint.sh

# Expõe as portas necessárias
EXPOSE 5000 8501 8502 8503

# Comando para iniciar os serviços
ENTRYPOINT ["./entrypoint.sh"]
