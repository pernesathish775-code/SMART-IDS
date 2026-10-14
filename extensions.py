# extensions.py
# Flask extensions are created here without being bound to an app.
# This avoids circular imports between app.py and the route/service modules.

from flask_sqlalchemy import SQLAlchemy
from flask_login      import LoginManager
from flask_wtf.csrf   import CSRFProtect

db            = SQLAlchemy()
login_manager = LoginManager()
csrf          = CSRFProtect()

login_manager.login_view             = "auth.login"
login_manager.login_message          = "Please log in to access this page."
login_manager.login_message_category = "warning"
