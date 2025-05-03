import json
import os
def load_users(USERS_FILE):
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_users(users,USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)