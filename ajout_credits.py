import sqlite3

DB = "chat.db"

def main():
    action = input("Voulez-vous ajouter ou retirer des crédits ? (ajouter/retirer) : ").strip().lower()
    if action not in ("ajouter", "retirer"):
        print("Action invalide.")
        return

    username = input("Nom de l'utilisateur : ").strip()
    amount = input("Nombre de crédits à modifier (ex: 5000) : ").strip()
    if not amount.isdigit():
        print("Nombre invalide.")
        return
    amount = int(amount)

    if action == "retirer":
        amount = -amount

    with sqlite3.connect(DB) as c:
        # Vérifier si l'utilisateur existe
        r = c.execute("SELECT credits FROM users WHERE username=?", (username,)).fetchone()
        if not r:
            print(f"L'utilisateur '{username}' n'existe pas.")
            return

        new_credits = max(0, r[0] + amount)  # éviter crédits négatifs
        c.execute("UPDATE users SET credits=? WHERE username=?", (new_credits, username))
        print(f"Crédits de '{username}' modifiés : maintenant {new_credits} crédits.")

if __name__ == "__main__":
    main()
