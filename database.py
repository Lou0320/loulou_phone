import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "users.db"

def migrate_database():
    """Ajoute la colonne points si elle n'existe pas"""
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        c = conn.cursor()
        # Vérifie si la colonne points existe
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        if 'points' not in columns:
            # Ajoute la colonne points
            c.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
            conn.commit()

def create_table():
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")  # Set WAL mode
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT)''')
        conn.commit()
    # Après la création de la table, on lance la migration
    migrate_database()

def create_user(username, password):
    """Ajoute un utilisateur avec un mot de passe haché"""
    try:
        hashed_password = generate_password_hash(password)
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Échec si l'utilisateur existe déjà

def check_user(username, password):
    """Vérifie si l'utilisateur existe et si le mot de passe est correct"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = c.fetchone()

    return user and check_password_hash(user[0], password)

def add_points(username, points):
    """Ajoute des points au score total d'un utilisateur"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET points = points + ? WHERE username = ?", (points, username))
        conn.commit()

def get_points(username):
    """Récupère le nombre total de points d'un utilisateur"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT points FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        return result[0] if result else 0

def get_all_users_points():
    """Récupère le classement de tous les utilisateurs par nombre de points"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT username, points FROM users ORDER BY points DESC')
        ranking = c.fetchall()
        return ranking

# Création de la table et migration au lancement
create_table()
