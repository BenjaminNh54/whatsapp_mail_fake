from flask import Flask, render_template, request, redirect, session, send_from_directory, jsonify
import sqlite3, os, hashlib, time, re

app = Flask(__name__)
app.secret_key = "supersecret"

DB = "chat.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DB INIT ----------------
def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user',
            ban_until INTEGER,
            credits INTEGER DEFAULT 30
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS msgs (
            id INTEGER PRIMARY KEY,
            user TEXT,
            group_id INTEGER,
            msg TEXT,
            file TEXT
        )
        """)

init_db()

# ---------------- UTIL ----------------
def is_admin():
    if "user" not in session:
        return False
    with sqlite3.connect(DB) as c:
        r = c.execute("SELECT role FROM users WHERE username=?", (session["user"],)).fetchone()
    return r and r[0] == "admin"

def check_temp_ban(username):
    with sqlite3.connect(DB) as c:
        r = c.execute("SELECT role, ban_until FROM users WHERE username=?", (username,)).fetchone()

    if not r:
        return False

    role, ban_until = r

    if role == "banned":
        if ban_until is None:
            return True  # ban permanent
        if time.time() >= ban_until:
            with sqlite3.connect(DB) as c:
                c.execute("UPDATE users SET role='user', ban_until=NULL WHERE username=?", (username,))
            return False
        return True
    return False

def parse_duration_to_seconds(text):
    text = text.strip().lower()
    match = re.fullmatch(r"(\d+)(s|mi|h|j|sem|mo|a)", text)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    units = {
        "s": 1,
        "mi": 60,
        "h": 3600,
        "j": 86400,
        "sem": 604800,
        "mo": 2592000,
        "a": 31536000
    }
    return value * units[unit]

def deduct_credits(username):
    """Déduire les crédits en fonction du temps écoulé depuis login_time"""
    elapsed = time.time() - session.get('login_time', time.time())
    credits_to_deduct = int(elapsed / 60)  # 1 crédit par minute
    #Ne pas retirer de credits au admins
    if is_admin():


        credits_to_deduct = 0
    if credits_to_deduct <= 0:
        return True

    with sqlite3.connect(DB) as c:
        current = c.execute("SELECT credits FROM users WHERE username=?", (username,)).fetchone()[0]
        if current < credits_to_deduct:
            return False
        c.execute("UPDATE users SET credits = credits - ? WHERE username=?", (credits_to_deduct, username))
    session['login_time'] = time.time()
    return True

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    if check_temp_ban(username):
        return redirect("/banned")

    if not deduct_credits(username):
        return """
    <form>
        Pas assez de crédits pour accéder au chat. <br>
        <a href="/request_credits">Demander des crédits</a>
    </form>
        """, 403

    with sqlite3.connect(DB) as c:
        groups = c.execute("SELECT * FROM groups").fetchall()
        """Récupérer les crédits restants de l'utilisateur"""
        credits = c.execute("SELECT credits FROM users WHERE username=?", (username,)).fetchone()[0]

    return render_template("chat.html", user=username, groups=groups, credits=credits)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        with sqlite3.connect(DB) as c:
            user = c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        if user:
            session["user"] = username
            session['login_time'] = time.time()
            return redirect("/")
        return "Mauvais login", 401

    return """
    <form method="post">
        <input name="username" placeholder="Login">
        <input name="password" type="password" placeholder="Mot de passe">
        <button>Connexion</button>
    </form>
    <a href="/register">Créer un compte</a>
    """

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        try:
            with sqlite3.connect(DB) as c:
                c.execute("INSERT INTO users(username,password,credits) VALUES(?,?,5000)", (username, password))
            session["user"] = username
            session['login_time'] = time.time()
            return redirect("/")
        except sqlite3.IntegrityError:
            return "Utilisateur déjà existant"

    return """
    <form method="post">
        <input name="username">
        <input name="password" type="password">
        <button>Créer compte</button>
    </form>
    """

@app.route("/banned")
def banned():
    if "user" not in session:
        return redirect("/login")
    return render_template("banned.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/create_group", methods=["POST"])
def create_group():
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO groups(name) VALUES(?)", (request.form["name"],))
    return redirect("/")

@app.route("/msgs/<int:group_id>")
def msgs(group_id):
    if not deduct_credits(session["user"]):
        return """
    <form>
        Pas assez de crédits pour accéder aux messages. <br>
        <a href="/request_credits">Demander des crédits</a>
    </form>
    """, 403
    with sqlite3.connect(DB) as c:
        msgs = c.execute("SELECT user,msg,file FROM msgs WHERE group_id=? ORDER BY id", (group_id,)).fetchall()
    return jsonify(msgs)

@app.route("/send", methods=["POST"])
def send():
    if "user" not in session:
        return "Not logged", 403

    if not deduct_credits(session["user"]):
        return """
        <form>
        Pas assez de crédits pour accéder aux messages. <br>
        <a href="/request_credits">Demander des crédits</a>
        </form>
        """, 403

    file = request.files.get("file")
    filename = None
    if file:
        filename = f"{int.from_bytes(os.urandom(4),'little')}_{file.filename}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO msgs(user,group_id,msg,file) VALUES(?,?,?,?)",
                  (session["user"], request.form["group"], request.form.get("msg",""), filename))

    return "OK"

@app.route("/uploads/<path:path>")
def uploads(path):
    return send_from_directory(UPLOAD_FOLDER, path)

@app.route("/bot/messages/<int:group_id>")
def bot_messages(group_id):
    with sqlite3.connect(DB) as c:
        rows = c.execute(
            "SELECT id, user, msg FROM msgs WHERE group_id=? ORDER BY id",
            (group_id,)
        ).fetchall()
    return jsonify(rows)
#route pour ajouter les credits aux utilisateurs
@app.route("/api/add_credits", methods=["POST"])
def api_add_credits():
    data = request.json
    username = data.get("username")
    amount = int(data.get("amount", 0))

    with sqlite3.connect(DB) as c:
        c.execute("UPDATE users SET credits = credits + ? WHERE username=?", (amount, username))
    return jsonify({"status": "ok", "new_credits": amount})

# ---------------- DEMANDE DE CRÉDITS ----------------
@app.route("/request_credits", methods=["GET", "POST"])
def request_credits():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if not message:
            return "Message vide", 400

        # Stocker le message dans la table msgs avec group_id=NULL ou spéciale
        with sqlite3.connect(DB) as c:
            c.execute(
                "INSERT INTO msgs(user, group_id, msg, file) VALUES(?,?,?,?)",
                (session["user"], None, f"Demande de crédits: {message}", None)
            )
        return "Votre demande a été envoyée à l'admin !"

    return render_template("request_credits.html", user=session["user"])

# ---------------- ADMIN : demandes de crédits ----------------
@app.route("/admin/credit_requests")
def credit_requests():
    if not is_admin():
        return "Accès refusé", 403

    with sqlite3.connect(DB) as c:
        # On récupère tous les messages où group_id IS NULL (demandes de crédits)
        requests = c.execute("SELECT id, user, msg FROM msgs WHERE group_id IS NULL").fetchall()

    return render_template("admin_credit_requests.html", requests=requests)

@app.route("/admin/approve_credit/<int:msg_id>", methods=["POST"])
def approve_credit(msg_id):
    if not is_admin():
        return "Accès refusé", 403

    with sqlite3.connect(DB) as c:
        row = c.execute("SELECT user FROM msgs WHERE id=? AND group_id IS NULL", (msg_id,)).fetchone()
        if not row:
            return "Demande introuvable", 404

        username = row[0]
        # Ajouter 50 crédits (modifiable)
        c.execute("UPDATE users SET credits = credits + 50 WHERE username=?", (username,))
        # Supprimer le message de demande
        c.execute("DELETE FROM msgs WHERE id=?", (msg_id,))

    return redirect("/admin/credit_requests")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin_panel():
    if not is_admin():
        return "Accès refusé", 403

    with sqlite3.connect(DB) as c:
        users = c.execute("SELECT id, username, role, ban_until, credits FROM users").fetchall()
        groups = c.execute("SELECT id, name FROM groups").fetchall()

    return render_template("admin.html", users=users, groups=groups)

@app.route("/admin/ban_user/<int:user_id>", methods=["POST"])
def ban_user(user_id):
    if not is_admin():
        return "Accès refusé", 403
    with sqlite3.connect(DB) as c:
        c.execute("UPDATE users SET role='banned', ban_until=NULL WHERE id=?", (user_id,))
    return redirect("/admin")

@app.route("/admin/tempban_user/<int:user_id>", methods=["POST"])
def tempban_user(user_id):
    if not is_admin():
        return "Accès refusé", 403

    duration = request.form.get("duration", "")
    seconds = parse_duration_to_seconds(duration)
    if not seconds:
        return "Durée invalide", 400

    ban_until = int(time.time()) + seconds
    with sqlite3.connect(DB) as c:
        c.execute("UPDATE users SET role='banned', ban_until=? WHERE id=?", (ban_until, user_id))
    return redirect("/admin")

@app.route("/admin/unban_user/<int:user_id>", methods=["POST"])
def unban_user(user_id):
    if not is_admin():
        return "Accès refusé", 403
    with sqlite3.connect(DB) as c:
        c.execute("UPDATE users SET role='user', ban_until=NULL WHERE id=?", (user_id,))
    return redirect("/admin")

@app.route("/admin/change_role/<int:user_id>", methods=["POST"])
def change_role(user_id):
    if not is_admin():
        return "Accès refusé", 403
    with sqlite3.connect(DB) as c:
        role = c.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()[0]
        new = "admin" if role != "admin" else "user"
        c.execute("UPDATE users SET role=? WHERE id=?", (new, user_id))
    return redirect("/admin")

@app.route("/admin/delete_msgs/<int:group_id>", methods=["POST"])
def delete_msgs(group_id):
    if not is_admin():
        return "Accès refusé", 403
    with sqlite3.connect(DB) as c:
        c.execute("DELETE FROM msgs WHERE group_id=?", (group_id,))
    return redirect("/admin")

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if not is_admin():
        return "Accès refusé", 403
    with sqlite3.connect(DB) as c:
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
    return redirect("/admin")

@app.route("/admin/delete_group/<int:group_id>", methods=["POST"])
def delete_group(group_id):
    if not is_admin():
        return "Accès refusé", 403
    with sqlite3.connect(DB) as c:
        c.execute("DELETE FROM groups WHERE id=?", (group_id,))
    return redirect("/admin")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)

#Anti-Sleep :
URL="https://whatsapp-mail-fake.onrender.com/login"
import threading
def anti_sleep():
    while True:
        try:
            requests.get(URL)
        except:
            pass
        time.sleep(300)  # toutes les 5 minutes
threading.Thread(target=anti_sleep, daemon=True).start()
