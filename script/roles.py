from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("MONGO_DB_NAME")

def create_roles(db):
    roles = [
        ("DataModifier", ["find", "insert", "update", "remove"]),
        ("StructureGestion", ["find", "createCollection", "createIndex", "dropIndex"]),
        ("UsersAdmin", ["createUser", "dropUser", "grantRole", "revokeRole"]),
        ("Gestionnaire", ["find", "insert", "update"]),
        ("Utilisateur", ["find"]),
        ("Consultant", [])
    ]

    for role_name, actions in roles:
        try:
            db.command({
                "createRole": role_name,
                "privileges": [{
                    "resource": {"db": DB_NAME, "collection": ""},  # ← correct
                    "actions": actions
                }],
                "roles": []
            })
            print(f"Rôle créé : {role_name}")

        except Exception as e:
            print(f"Erreur création rôle {role_name}: {e}")
