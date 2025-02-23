from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from utils.database import create_database, register_user, fetch_credentials
from utils.chatbot_assistente import (
    chatbot_assistente_logic,
    check_files_in_directory,
    load_data,
    show_error
)
from utils.chatbot_gpt import chatbot_gpt_logic
import os
import bcrypt
from datetime import timedelta

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

# Rota do Chatbot Assistente (Flask)
@app.route("/streamlit_chatbot_assistente")
def chatbot_assistente():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    # Pega o username da sessão do Flask
    username = session.get("username")
    # Monta a URL para o app Streamlit (ajuste a porta se necessário)
    streamlit_url = f"http://localhost:8501/?username={username}"
    return redirect(streamlit_url)

# Rota do Chatbot GPT
@app.route("/chatbot_gpt", methods=["GET", "POST"])
def chatbot_gpt():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    if request.method == "POST":
        user_input = request.form.get("user_input")
        history = request.form.get("history", [])
        response = chatbot_gpt_logic(user_input, history)
        return jsonify({"response": response})
    return render_template("chatbot_gpt.html", user_name=session.get("full_name"))

if __name__ == "__main__":
    app.run(debug=True)
