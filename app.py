from flask import Flask, render_template, request, redirect, session, send_from_directory, jsonify
import sqlite3, os, hashlib

app = Flask(__name__)
app.secret_key = "supersecret"
DB = "chat.db"
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DB INIT ----------------
def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS groups (
                        id INTEGER PRIMARY KEY, name TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS msgs (
                        id INTEGER PRIMARY KEY, user TEXT, group_id INTEGER, msg TEXT, file TEXT)""")
init_db()

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    with sqlite3.connect(DB) as c:
        groups = c.execute("SELECT * FROM groups").fetchall()
    return render_template("chat.html", user=session["user"], groups=groups)
    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        with sqlite3.connect(DB) as c:
            user = c.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password)).fetchone()
        if user:
            session["user"] = username
            return redirect("/")
        else:
            return "Mauvais login"
    return """
    <form method="post">
    <link rel="stylesheet" href="/static/style.css">
        <input name="username" placeholder="Login">
        <input name="password" type="password" placeholder="Mot de passe">
        <button>Connexion</button>
    </form>
    <a href="/register" style="color:red">Créer un compte</a>
    """

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method=="POST":
        username = request.form["username"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        try:
            with sqlite3.connect(DB) as c:
                c.execute("INSERT INTO users(username,password) VALUES(?,?)",(username,password))
            session["user"]=username
            return redirect("/")
        except sqlite3.IntegrityError:
            return "Utilisateur déjà existant"
    return """
    <form method="post">
    <link rel="stylesheet" href="/static/style.css">
        <input name="username" placeholder="Login">
        <input name="password" type="password" placeholder="Mot de passe">
        <button>Créer compte</button>
    </form>
    <a href="/login" style="color:red">Se connecter</a>
    """

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/login")

@app.route("/create_group", methods=["POST"])
def create_group():
    name = request.form["name"]
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO groups(name) VALUES(?)",(name,))
    return redirect("/")

@app.route("/msgs/<int:group_id>")
def msgs(group_id):
    with sqlite3.connect(DB) as c:
        messages = c.execute("SELECT user,msg,file FROM msgs WHERE group_id=? ORDER BY id", (group_id,)).fetchall()
    return jsonify(messages)

@app.route("/send", methods=["POST"])
def send():
    if "user" not in session:
        return "Not logged", 403
    user = session["user"]
    group_id = request.form.get("group")
    msg = request.form.get("msg","")
    f = request.files.get("file")
    filename = None
    if f:
        filename = f"{int.from_bytes(os.urandom(4),'little')}_{f.filename}"
        f.save(os.path.join(UPLOAD_FOLDER,filename))
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO msgs(user,group_id,msg,file) VALUES(?,?,?,?)",(user,group_id,msg,filename))
    return "OK"

@app.route("/uploads/<path:path>")
def uploads(path):
    return send_from_directory(UPLOAD_FOLDER,path)

# ---------------- RUN ----------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
    
    