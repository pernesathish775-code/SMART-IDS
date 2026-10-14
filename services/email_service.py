# services/email_service.py
# Sends email alerts for unknown-face events using Gmail SMTP-SSL.
# Credentials are read from environment variables — never logged.

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from datetime             import datetime

logger = logging.getLogger(__name__)


def send_unknown_alert(app_config, event_id, detected_at):
    """
    Send an email notification when an unknown face is detected.

    Returns:
        "sent"   -- email was delivered successfully
        "failed" -- SMTP or authentication error occurred
        "disabled" -- email is not configured
    """
    if not app_config.get("MAIL_ENABLED"):
        return "disabled"

    sender   = app_config.get("MAIL_SENDER", "")
    receiver = app_config.get("MAIL_RECEIVER", "")
    password = app_config.get("MAIL_PASSWORD", "")
    server   = app_config.get("MAIL_SMTP_SERVER", "smtp.gmail.com")
    port     = int(app_config.get("MAIL_SMTP_PORT", 465))

    if not sender or not receiver or not password:
        logger.warning("Email alert skipped: incomplete configuration.")
        return "disabled"

    time_str = detected_at.strftime("%Y-%m-%d %H:%M:%S UTC") if detected_at else "Unknown"

    body = (
        "Smart Identity Detection System — Security Alert\n\n"
        "An unrecognised face was detected.\n\n"
        f"Event ID   : {event_id}\n"
        f"Time (UTC) : {time_str}\n"
        f"Event Type : UNKNOWN\n\n"
        "An unknown face simply means the system could not match the detected\n"
        "face against the registered database. Please review the event in the\n"
        "Detection History page.\n\n"
        "— Smart Identity Detection System"
    )

    msg            = MIMEMultipart()
    msg["Subject"] = f"[ALERT] Unknown Face Detected — Event #{event_id}"
    msg["From"]    = sender
    msg["To"]      = receiver
    msg.attach(MIMEText(body, "plain"))

    try:
        # Use SMTP_SSL for port 465 (Gmail requirement)
        with smtplib.SMTP_SSL(server, port, timeout=10) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        logger.info("Alert email sent for event #%s", event_id)
        return "sent"
    except smtplib.SMTPAuthenticationError:
        logger.error("Email alert failed: authentication error (check app password).")
        return "failed"
    except Exception as e:
        logger.error("Email alert failed: %s", type(e).__name__)
        return "failed"


def send_test_email(app_config):
    """
    Send a test email to verify the configuration.
    Returns (success: bool, message: str).
    """
    if not app_config.get("MAIL_ENABLED"):
        return False, "Email alerts are disabled. Enable them in Settings first."

    sender   = app_config.get("MAIL_SENDER", "")
    receiver = app_config.get("MAIL_RECEIVER", "")
    password = app_config.get("MAIL_PASSWORD", "")
    server   = app_config.get("MAIL_SMTP_SERVER", "smtp.gmail.com")
    port     = int(app_config.get("MAIL_SMTP_PORT", 465))

    if not sender or not receiver or not password:
        return False, "Email configuration is incomplete. Check MAIL_SENDER, MAIL_RECEIVER, MAIL_PASSWORD in .env."

    msg            = MIMEMultipart()
    msg["Subject"] = "Smart Identity System — Test Email"
    msg["From"]    = sender
    msg["To"]      = receiver
    msg.attach(MIMEText(
        "This is a test email from the Smart Identity Detection System.\n"
        "If you received this, email alerts are working correctly.", "plain"
    ))

    try:
        with smtplib.SMTP_SSL(server, port, timeout=10) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        return True, f"Test email sent successfully to {receiver}."
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your Gmail app password in .env."
    except Exception as e:
        return False, f"Email failed: {type(e).__name__}. Check SMTP settings in .env."
