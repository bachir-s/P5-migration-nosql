from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("MONGO_DB_NAME")


def role_exists(db, role_name):
    try:
        roles_info = db.command("rolesInfo", 1)
        existing_roles = [role["role"] for role in roles_info.get("roles", [])]
        return role_name in existing_roles
    except Exception:
        return False


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
        if role_exists(db, role_name):
            print(f"Rôle existe déjà : {role_name}")
            continue

        try:
            db.command({
                "createRole": role_name,
                "privileges": [{
                    "resource": {"db": DB_NAME, "collection": ""},
                    "actions": actions
                }],
                "roles": [],
                "mechanisms": ["SCRAM-SHA-256"]
            })
            print(f"Rôle créé : {role_name}")

        except Exception as e:
            print(f"Erreur création rôle {role_name}: {e}")
