"""Nous allons coder un bot qui repond salut quand un utilisateur envoie bonjour dans un groupe de discussion il ne fonctionnera pas avec de l'IA mais simplement en détectant les messages et en envoyant bonjour. Il y a une route prevue que les bots puissent voir les msg d'un groupe dans app.py
/bot/messages/<int:group_id> maintenant creons un nouveau fichier bot_bonjour.py pour notre bot de bienvenue"""
"""import requests
import time
CHAT_URL = "http://localhost:5000/"
USERNAME = "bot"
PASSWORD = "botpassword"
GROUP_ID = 1
session = requests.Session()
# ========= CONNEXION =========
def login():
    r = session.post(f"{CHAT_URL}/login", data={
        "username": USERNAME,
        "password": PASSWORD
    })
    if r.status_code == 200:
        print("🤖 Bot Bonjour connecté")
    else:
        print("⚠️ Échec de la connexion du bot Bonjour")
login()
LAST_ID = 0

def get_messages():
    global LAST_ID
    r = session.get(f"{CHAT_URL}/bot/messages/{GROUP_ID}")
    print("GET /bot/messages status:", r.status_code)
    if r.status_code != 200:
        return []
    msgs = r.json()
    print("DEBUG MESSAGES:", msgs)
    
    new = []
    for m in msgs:
        if m["id"] > LAST_ID:
            new.append(m)
            LAST_ID = m["id"]
    return new
def send_message(msg):
    r = session.post(f"{CHAT_URL}/send_message", data={
        "group_id": GROUP_ID,
        "msg": msg
    })
    print("POST /bot/send_message status:", r.status_code)
    return r.status_code == 200
print("🤖 Bot Bonjour lancé")
while True:
    try:
        messages = get_messages()
        for m in messages:
            user = m["user"]
            text = m["msg"].strip().lower()
            if "bonjour" in text:
                question = f"Un utilisateur a dit 'bonjour' dans le groupe. Réponds-lui par 'Salut {user} !'"
                print(f"🧠 Question : {question}")
                answer = f"Salut {user} !"
                print(f"🤖 Réponse : {answer}")
                send_message(answer)
        time.sleep(5)
    except Exception as e:
        print("⚠️ Erreur :", e)
        time.sleep(5)"""


"""dans le log nous avons une erreur ⚠️ Erreur : list indices must be integers or slices, not str comment la corriger? Pour corriger cette erreur nous devons nous assurer que nous traitons chaque message comme un dictionnaire. Voici le code corrigé:
"""
import requests
import time
CHAT_URL = "http://localhost:5000/"
USERNAME = "bot"
PASSWORD = "botpassword"
GROUP_ID = 1
session = requests.Session()
# ========= CONNEXION =========
def login():
    r = session.post(f"{CHAT_URL}/login", data={
        "username": USERNAME,
        "password": PASSWORD
    })
    if r.status_code == 200:
        print("🤖 Bot Bonjour connecté")
    else:
        print("⚠️ Échec de la connexion du bot Bonjour")
login()
LAST_ID = 0
def get_messages():
    global LAST_ID
    r = session.get(f"{CHAT_URL}/bot/messages/{GROUP_ID}")
    print("GET /bot/messages status:", r.status_code)
    if r.status_code != 200:
        return []
    msgs = r.json()
    print("DEBUG MESSAGES:", msgs)
    
    new = []
    for m in msgs:
        if m["id"] > LAST_ID:
            new.append(m)
            LAST_ID = m["id"]
    return new
def send_message(msg):
    r = session.post(f"{CHAT_URL}/send", data={
        "group_id": GROUP_ID,
        "msg": msg
    })
    print("POST /bot/send_message status:", r.status_code)
    return r.status_code == 200
print("🤖 Bot Bonjour lancé")
while True:
    try:
        messages = get_messages()
        for m in messages:
            user = m["user"]
            text = m["msg"].strip().lower()
            if "bonjour" in text:
                question = f"Un utilisateur a dit 'bonjour' dans le groupe. Réponds-lui par 'Salut {user} !'"
                print(f"🧠 Question : {question}")
                answer = f"Salut {user} !"
                print(f"🤖 Réponse : {answer}")
                send_message(answer)
        time.sleep(5)
    except Exception as e:
        print("⚠️ Erreur :", e)
        time.sleep(5)