'''import requests
import time

# ========= CONFIG =========
CHAT_URL = "http://127.0.0.1:5000"
USERNAME = "bot"
PASSWORD = "botpassword"
GROUP_ID = 1

HF_MODEL = "bigscience/bloomz-560m"

CHECK_INTERVAL = 3  # secondes entre chaque lecture
LAST_MESSAGE_ID = 0  # pour éviter les doublons

# ========= CONNEXION CHAT =========
session = requests.Session()
login = session.post(f"{CHAT_URL}/login", data={
    "username": USERNAME,
    "password": PASSWORD
})

if login.status_code != 200:
    print("❌ Connexion au chat impossible")
    exit()

print("✅ Bot connecté au chat")

# ========= APPEL IA =========
def ask_ai(prompt):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 80,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    r = requests.post(
        f"https://api-inference.huggingface.co/models/{HF_MODEL}",
        headers=headers,
        json=payload,
        timeout=30
    )

    data = r.json()

    if isinstance(data, list):
        return data[0]["generated_text"].replace(prompt, "").strip()

    return "Désolé, je bug 🤖"

# ========= LECTURE DES MESSAGES =========
def get_messages():
    global LAST_MESSAGE_ID

    r = session.get(f"{CHAT_URL}/messages/{GROUP_ID}")
    if r.status_code != 200:
        return []

    messages = r.json()
    print("DEBUG MESSAGES:", messages)
    new_msgs = []

    for msg in messages:
        if msg["id"] > LAST_MESSAGE_ID:
            new_msgs.append(msg)
            LAST_MESSAGE_ID = msg["id"]

    return new_msgs

# ========= ENVOI MESSAGE =========
def send_message(text):
    session.post(f"{CHAT_URL}/send", data={
        "group": GROUP_ID,
        "msg": text
    })

# ========= BOUCLE PRINCIPALE =========
print("🤖 Bot IA actif (mentionne @bot)")

while True:
    try:
        messages = get_messages()

        for msg in messages:
            author = msg["username"]
            content = msg["msg"]

            # ignore ses propres messages
            if author == USERNAME:
                continue

            if "bot" in content.lower():
                question = content.replace("bot", "").strip()

                if not question:
                    continue

                print(f"🧠 Question : {question}")
                answer = ask_ai(question)
                print(f"🤖 Réponse : {answer}")

                send_message(answer)

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("⚠️ Erreur :", e)
        time.sleep(5)
'''

import requests
import time

CHAT_URL = "http://127.0.0.1:5000"
USERNAME = "bot"
PASSWORD = "botpassword"
GROUP_ID = 1

session = requests.Session()

# LOGIN
r = session.post(f"{CHAT_URL}/login", data={
    "username": USERNAME,
    "password": PASSWORD
})

print("LOGIN STATUS:", r.status_code)
print("COOKIES:", session.cookies.get_dict())

LAST_ID = 0

def get_messages():
    global LAST_ID

    r = session.get(f"{CHAT_URL}/messages", params={"group": GROUP_ID})
    print("GET /messages status:", r.status_code)

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

print("🤖 Bot lancé")

while True:
    msgs = get_messages()
    time.sleep(2)
