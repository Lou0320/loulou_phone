import sqlite3
import hashlib

DB_NAME = "users.db"

# Fonction pour hacher un mot de passe
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Mise à jour de tous les mots de passe pour qu'ils soient hachés
def update_passwords():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Sélectionner tous les utilisateurs
    c.execute("SELECT username, password FROM users")
    users = c.fetchall()
    
    for user in users:
        username, password = user
        hashed_password = hash_password(password)
        c.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
    
    conn.commit()
    conn.close()

# Lancer la mise à jour des mots de passe
update_passwords()
print("Mise à jour des mots de passe terminée !")
