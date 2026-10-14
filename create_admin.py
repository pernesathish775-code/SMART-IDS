# create_admin.py
# Run this script ONCE to create the first administrator account.
# Usage:  python create_admin.py

import sys
import types

# Patch matplotlib before face_recognition loads (App Control policy fix)
for _m in ["matplotlib", "matplotlib.pyplot", "matplotlib.patches", "matplotlib.colors"]:
    sys.modules.setdefault(_m, types.ModuleType(_m))

from dotenv import load_dotenv
load_dotenv()

from app        import create_app
from extensions import db
from models     import AdminUser

app = create_app()

with app.app_context():
    if AdminUser.query.first():
        print("An admin account already exists.")
        print("Log in at http://127.0.0.1:5000/login")
        sys.exit(0)

    print("=== Create Admin Account ===")
    username = input("Username: ").strip()

    import getpass
    password = getpass.getpass("Password (min 8 characters): ")
    confirm  = getpass.getpass("Confirm password: ")

    if not username or not password:
        print("Username and password cannot be empty.")
        sys.exit(1)

    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    admin = AdminUser(username=username)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    print(f"\nAdmin account '{username}' created successfully.")
    print("Open http://127.0.0.1:5000 in Chrome and log in.")
