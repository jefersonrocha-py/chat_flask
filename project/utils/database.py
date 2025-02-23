import sqlite3
import bcrypt
import os
from pathlib import Path

# Caminho para o banco de dados
DB_PATH = Path(__file__).parent.parent / "data" / "users.db"

def create_database():
    """Cria/atualiza a estrutura do banco de dados"""
    try:
        # Garante que o diretório existe
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Verifica permissões de escrita
        if not os.access(DB_PATH.parent, os.W_OK):
            raise PermissionError("Sem permissão de escrita no diretório.")
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Erro ao criar banco de dados: {str(e)}")
    except PermissionError as pe:
        raise RuntimeError(f"Erro de permissão: {str(pe)}")

def register_user(username, password, email, full_name, organization):
    """Registra um novo usuário com validação"""
    try:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password, email, full_name, organization)
                VALUES (?, ?, ?, ?, ?)
            """, (username, hashed_password, email, full_name, organization))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Usuário/E-mail já existente
    except sqlite3.Error as e:
        raise RuntimeError(f"Erro de banco de dados: {str(e)}")

def fetch_credentials():
    """Recupera credenciais para autenticação"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, password, full_name FROM users")
            users = cursor.fetchall()
        return {"usernames": {user[0]: {"name": user[2], "password": user[1]} for user in users}}
    except sqlite3.Error as e:
        raise RuntimeError(f"Erro ao buscar credenciais: {str(e)}")