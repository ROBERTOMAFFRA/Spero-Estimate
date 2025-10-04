import json, hashlib, os

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def verify_user(username: str, password: str) -> bool:
    users = load_users()
    if username in users:
        return users[username] == hash_password(password)
    return False

def add_user(username: str, password: str) -> bool:
    users = load_users()
    if username in users:
        return False
    users[username] = hash_password(password)
    save_users(users)
    return True

def delete_user(username: str) -> bool:
    users = load_users()
    if username in users:
        users.pop(username)
        save_users(users)
        return True
    return False

def reset_password(username: str, new_password: str) -> bool:
    users = load_users()
    if username in users:
        users[username] = hash_password(new_password)
        save_users(users)
        return True
    return False
