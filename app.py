# app.py  –  Main entry point
# Patch matplotlib BEFORE importing face_recognition (App Control policy blocks its DLL).
import sys
import types
for _mod in ["matplotlib", "matplotlib.pyplot", "matplotlib.patches", "matplotlib.colors"]:
    sys.modules.setdefault(_mod, types.ModuleType(_mod))

# Load .env file first so Config reads the right values
from dotenv import load_dotenv
load_dotenv()

import os
import shutil
import logging
from datetime import datetime, timezone

from flask      import Flask, render_template
from config     import Config
from extensions import db, login_manager, csrf

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    # Make sure required folders exist
    for folder in [
        app.config["FACES_FOLDER"],
        app.config["SNAPSHOT_FOLDER"],
        app.config["KNOWN_FACES_FOLDER"],
        "instance",
    ]:
        os.makedirs(folder, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from models import AdminUser

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Register blueprints
    from routes.auth       import auth
    from routes.dashboard  import dashboard
    from routes.people     import people
    from routes.monitoring import monitoring
    from routes.events     import events
    from routes.settings   import settings_bp

    for bp in (auth, dashboard, people, monitoring, events, settings_bp):
        app.register_blueprint(bp)

    # Error pages
    @app.errorhandler(403)
    def e403(e): return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def e404(e): return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def e500(e): return render_template("errors/500.html"), 500

    # Init DB and import known_faces
    with app.app_context():
        db.create_all()
        logger.info("Database tables ready.")
        _import_known_faces(app)

    return app


def _import_known_faces(app):
    """
    Read images from known_faces/ folder on startup.
    Each filename (without extension) is used as the person's name.
    Skips duplicates and images with no detectable face.
    """
    from models import RegisteredPerson
    from services.face_recognition_service import detect_and_encode

    known_dir    = app.config["KNOWN_FACES_FOLDER"]
    faces_folder = app.config["FACES_FOLDER"]
    allowed      = app.config["ALLOWED_EXTENSIONS"]

    if not os.path.isdir(known_dir):
        return

    imported = 0
    for filename in sorted(os.listdir(known_dir)):
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in allowed:
            continue

        name = os.path.splitext(filename)[0]

        # Skip if already in database
        if RegisteredPerson.query.filter_by(name=name).first():
            logger.info("known_faces: '%s' already in DB — skipping.", name)
            continue

        src  = os.path.join(known_dir, filename)
        enc, err = detect_and_encode(src)
        if err:
            logger.warning("known_faces: skipping '%s' — %s", filename, err)
            continue

        # Copy image to faces upload folder with a timestamp prefix
        ts        = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest_name = f"{ts}_{filename}"
        shutil.copy2(src, os.path.join(faces_folder, dest_name))

        person = RegisteredPerson(name=name, image_path=dest_name)
        person.set_encoding(enc)
        db.session.add(person)
        db.session.commit()
        imported += 1
        logger.info("known_faces: imported '%s'.", name)

    if imported:
        logger.info("known_faces: %d new person(s) imported.", imported)


# Application instance (used by `flask run` and `python app.py`)
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)
