# routes/settings.py
# Settings page: thresholds, email toggle, password change, test email.

import logging
from flask        import (Blueprint, render_template, request, flash,
                          redirect, url_for, current_app)
from flask_login  import login_required, current_user
from extensions   import db
from models       import AppSetting, AdminUser
from services.email_service import send_test_email

settings_bp = Blueprint("settings_bp", __name__)
logger      = logging.getLogger(__name__)


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        action = request.form.get("action")

        # ── Update recognition settings ───────────────────────────────────────
        if action == "save_settings":
            try:
                threshold = float(request.form.get("threshold", "0.55"))
                cooldown  = int(request.form.get("cooldown", "10"))
                if not (0.1 <= threshold <= 1.0):
                    raise ValueError("Threshold out of range")
                if not (1 <= cooldown <= 3600):
                    raise ValueError("Cooldown out of range")
                AppSetting.set("face_threshold", threshold)
                AppSetting.set("event_cooldown", cooldown)
                # Also update the live config so the change takes effect immediately
                current_app.config["FACE_THRESHOLD"] = threshold
                current_app.config["EVENT_COOLDOWN"]  = cooldown
                flash("Settings saved successfully.", "success")
            except ValueError as e:
                flash(f"Invalid value: {e}", "danger")

        # ── Change password ───────────────────────────────────────────────────
        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw     = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            if not current_user.check_password(current_pw):
                flash("Current password is incorrect.", "danger")
            elif len(new_pw) < 8:
                flash("New password must be at least 8 characters.", "danger")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "danger")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash("Password changed successfully.", "success")
                logger.info("Admin '%s' changed their password.", current_user.username)

        # ── Test email ────────────────────────────────────────────────────────
        elif action == "test_email":
            ok, msg = send_test_email(current_app.config)
            flash(msg, "success" if ok else "danger")

        return redirect(url_for("settings_bp.index"))

    # Read current live settings
    threshold = float(AppSetting.get("face_threshold",
                      current_app.config.get("FACE_THRESHOLD", 0.55)))
    cooldown  = int(AppSetting.get("event_cooldown",
                   current_app.config.get("EVENT_COOLDOWN", 10)))

    return render_template(
        "settings.html",
        threshold    = threshold,
        cooldown     = cooldown,
        mail_enabled = current_app.config.get("MAIL_ENABLED", False),
        mail_sender  = current_app.config.get("MAIL_SENDER", ""),
        mail_receiver= current_app.config.get("MAIL_RECEIVER", ""),
    )
