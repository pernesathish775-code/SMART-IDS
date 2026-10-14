# routes/auth.py
# Login, logout, and first-run admin setup.

import logging
from datetime        import datetime, timezone
from flask           import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login     import login_user, logout_user, login_required, current_user
from extensions      import db
from models          import AdminUser

auth = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

# Simple in-memory rate limiter: ip -> [attempt_timestamps]
_login_attempts = {}
MAX_ATTEMPTS    = 5
LOCKOUT_SECONDS = 60


def _is_locked_out(ip):
    now     = datetime.now(timezone.utc).timestamp()
    history = _login_attempts.get(ip, [])
    # Keep only attempts within the lockout window
    recent  = [t for t in history if now - t < LOCKOUT_SECONDS]
    _login_attempts[ip] = recent
    return len(recent) >= MAX_ATTEMPTS


def _record_attempt(ip):
    now = datetime.now(timezone.utc).timestamp()
    _login_attempts.setdefault(ip, []).append(now)


def _clear_attempts(ip):
    _login_attempts.pop(ip, None)


# ── Setup (first-run admin creation) ──────────────────────────────────────────

@auth.route("/setup", methods=["GET", "POST"])
def setup():
    """Create the first administrator account. Disabled once one exists."""
    if AdminUser.query.first():
        flash("Admin account already exists. Please log in.", "info")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm",  "").strip()

        if not username or not password:
            flash("Username and password are required.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
        else:
            admin = AdminUser(username=username)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            flash("Admin account created. You can now log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("setup.html")


# ── Login ──────────────────────────────────────────────────────────────────────

@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    # Redirect to setup if no admin exists yet
    if not AdminUser.query.first():
        return redirect(url_for("auth.setup"))

    if request.method == "POST":
        ip       = request.remote_addr
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if _is_locked_out(ip):
            flash(f"Too many failed attempts. Please wait {LOCKOUT_SECONDS} seconds.", "danger")
            return render_template("login.html")

        admin = AdminUser.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin, remember=False)
            _clear_attempts(ip)
            logger.info("Admin '%s' logged in.", username)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        else:
            _record_attempt(ip)
            logger.warning("Failed login attempt for username '%s' from %s", username, ip)
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


# ── Logout ─────────────────────────────────────────────────────────────────────

@auth.route("/logout")
@login_required
def logout():
    logger.info("Admin '%s' logged out.", current_user.username)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
