# Base image
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários para o contêiner
COPY . .

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Torna o script de inicialização executável
RUN chmod +x entrypoint.sh

# Expõe as portas necessárias
EXPOSE 5000 8501 8502

# Comando para iniciar os serviços
ENTRYPOINT ["./entrypoint.sh"]