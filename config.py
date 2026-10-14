# config.py
# All settings are read from environment variables (loaded from .env by app.py).
# Never hardcode secrets here.

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY              = os.environ.get("SECRET_KEY", "dev-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED        = True

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "identity.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── File Uploads ──────────────────────────────────────────────────────────
    FACES_FOLDER       = os.path.join(BASE_DIR, "uploads", "faces")
    SNAPSHOT_FOLDER    = os.path.join(BASE_DIR, "uploads", "snapshots")
    KNOWN_FACES_FOLDER = os.path.join(BASE_DIR, "known_faces")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024          # 10 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

    # ── Face Recognition ──────────────────────────────────────────────────────
    # How close two face encodings must be to count as a match.
    # Lower value = stricter.  0.55 is a reasonable starting point.
    # Accuracy is NOT perfect — lighting, angle, and image quality all affect it.
    FACE_THRESHOLD         = float(os.environ.get("FACE_THRESHOLD", "0.55"))
    EVENT_COOLDOWN         = int(os.environ.get("EVENT_COOLDOWN", "10"))
    PROCESS_EVERY_N_FRAMES = int(os.environ.get("PROCESS_EVERY_N_FRAMES", "3"))

    # ── Email ─────────────────────────────────────────────────────────────────
    MAIL_ENABLED     = os.environ.get("MAIL_ENABLED", "false").lower() == "true"
    MAIL_SMTP_SERVER = os.environ.get("MAIL_SMTP_SERVER", "smtp.gmail.com")
    MAIL_SMTP_PORT   = int(os.environ.get("MAIL_SMTP_PORT", "465"))
    MAIL_SENDER      = os.environ.get("MAIL_SENDER", "")
    MAIL_PASSWORD    = os.environ.get("MAIL_PASSWORD", "")   # never logged
    MAIL_RECEIVER    = os.environ.get("MAIL_RECEIVER", "")

    # ── Camera ────────────────────────────────────────────────────────────────
    CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))
