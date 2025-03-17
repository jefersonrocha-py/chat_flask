from flask import Flask, render_template, request, redirect, url_for, session, flash
from utils.database import create_database, register_user, fetch_credentials
from datetime import timedelta
import os
import bcrypt  # Certifique-se de que o bcrypt esteja instalado e importado

# Inicialização do aplicativo Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
app.permanent_session_lifetime = timedelta(minutes=30)

# Configurações iniciais
create_database()

# Rota principal (redireciona para login se não autenticado)
@app.route("/")
def index():
    if "authenticated" not in session or not session["authenticated"]:
        return redirect(url_for("login"))
    return render_template("index.html")

# Rota de Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        credentials = fetch_credentials()
        user_data = credentials["usernames"].get(username)
        if user_data and bcrypt.checkpw(password.encode(), user_data["password"].encode()):
            session["authenticated"] = True
            session["username"] = username
            session["full_name"] = user_data["name"]
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("mode_selection"))
        else:
            flash("Credenciais inválidas!", "danger")
    return render_template("login.html")

# Rota de Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Você foi desconectado.", "info")
    return redirect(url_for("login"))

# Rota de Registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        organization = request.form.get("organization")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        if password != confirm_password:
            flash("As senhas não coincidem.", "danger")
            return redirect(url_for("register"))
        if register_user(username, password, email, full_name, organization):
            flash("Conta criada com sucesso! Faça login.", "success")
            return redirect(url_for("login"))
        else:
            flash("Erro: Usuário/e-mail já existente ou dados inválidos.", "danger")
    return render_template("register.html")

# Rota de Seleção de Modo
@app.route("/mode_selection")
def mode_selection():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return render_template("mode_selection.html")

# Rota para o Chatbot Assistente (Streamlit)
@app.route("/chatbot_assistente")
def chatbot_assistente():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    username = session.get("username")
    # Redireciona para o app Streamlit st_chatbot_assistente.py rodando na porta 8501
    streamlit_url = f"http://localhost:8501/?username={username}"
    return redirect(streamlit_url)

# Rota para o Chatbot GPT (Streamlit)
@app.route("/chatbot_gpt")
def chatbot_gpt():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    username = session.get("username")
    # Redireciona para o app Streamlit st_chatbot_gpt.py rodando na porta 8502
    streamlit_url = f"http://localhost:8502/?username={username}"
    return redirect(streamlit_url)

# Rota para o Chatbot Agent (Streamlit)
@app.route("/chatbot_cagent")
def chatbot_coder():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    username = session.get("username")
    # Redireciona para o app Streamlit st_chatbot_agent.py rodando na porta 8502
    streamlit_url = f"http://localhost:8503/?username={username}"
    return redirect(streamlit_url)

# Rota para a página de recuperação de senha
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        # Aqui você pode implementar a lógica para enviar um e-mail de recuperação
        # Exemplo: verificar se o e-mail existe no banco de dados e enviar um link de redefinição
        flash("Um e-mail de recuperação foi enviado para o endereço fornecido.", "info")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)