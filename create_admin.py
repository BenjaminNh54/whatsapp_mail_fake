import sqlite3, hashlib

DB = "chat.db"
username = "admin"
password = "azerty"  # change ton mot de passe ici
hashed = hashlib.sha256(password.encode()).hexdigest()

with sqlite3.connect(DB) as c:
    c.execute("INSERT INTO users(username, password, role) VALUES(?,?,?)", (username, hashed, "admin"))
    print("Admin créé !")
