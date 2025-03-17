from flask import Flask, render_template, request, redirect, url_for, session, flash
from utils.database import create_database, register_user, fetch_credentials
from datetime import timedelta
import os
import bcrypt

# Inicialização do aplicativo Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
app.permanent_session_lifetime = timedelta(minutes=30)

# Configurações de portas
ASSISTENTE_PORT = os.getenv("ASSISTENTE_PORT", "8501")
GPT_PORT = os.getenv("GPT_PORT", "8502")
AGENT_PORT = os.getenv("AGENT_PORT", "8503")

# Rota principal
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
        if user_data:
            stored_password = user_data["password"] if isinstance(user_data["password"], bytes) else user_data["password"].encode()
            if bcrypt.checkpw(password.encode(), stored_password):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["full_name"] = user_data["name"]
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for("mode_selection"))
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
    streamlit_url = f"http://localhost:{ASSISTENTE_PORT}/?username={username}"
    return redirect(streamlit_url)

# Rota para o Chatbot GPT (Streamlit)
@app.route("/chatbot_gpt")
def chatbot_gpt():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    username = session.get("username")
    streamlit_url = f"http://localhost:{GPT_PORT}/?username={username}"
    return redirect(streamlit_url)

# Rota para o Chatbot Agent (Streamlit)
@app.route("/chatbot_agent")
def chatbot_agent():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    username = session.get("username")
    streamlit_url = f"http://localhost:{AGENT_PORT}/?username={username}"
    return redirect(streamlit_url)

# Rota para recuperação de senha
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
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
    create_database()  # Movido para evitar execução em imports
    app.run(debug=True)