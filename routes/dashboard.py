# routes/dashboard.py
# Main dashboard — statistics, charts, recent events.

from flask        import Blueprint, render_template, jsonify, current_app
from flask_login  import login_required
from sqlalchemy   import func
from extensions   import db
from models       import RegisteredPerson, DetectionEvent
from services.camera_service import is_running as camera_is_running
import json
from datetime import datetime, timezone, timedelta

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/")
@dashboard.route("/dashboard")
@login_required
def index():
    # ── Stats cards ───────────────────────────────────────────────────────────
    total_people     = RegisteredPerson.query.count()
    total_events     = DetectionEvent.query.count()
    recognized_count = DetectionEvent.query.filter_by(event_type="RECOGNIZED").count()
    unknown_count    = DetectionEvent.query.filter_by(event_type="UNKNOWN").count()

    # Recent events (last 10)
    recent_events = (DetectionEvent.query
                     .order_by(DetectionEvent.detected_at.desc())
                     .limit(10).all())

    # Latest unknown events (last 5)
    unknown_events = (DetectionEvent.query
                      .filter_by(event_type="UNKNOWN")
                      .order_by(DetectionEvent.detected_at.desc())
                      .limit(5).all())

    # ── Chart data: detections per day for last 7 days ────────────────────────
    days   = []
    counts = []
    today  = datetime.now(timezone.utc).date()

    for i in range(6, -1, -1):
        day      = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        day_end   = day_start + timedelta(days=1)
        count     = (DetectionEvent.query
                     .filter(DetectionEvent.detected_at >= day_start,
                             DetectionEvent.detected_at <  day_end)
                     .count())
        days.append(day.strftime("%d %b"))
        counts.append(count)

    camera_status = "Running" if camera_is_running() else "Stopped"
    mail_enabled  = current_app.config.get("MAIL_ENABLED", False)

    return render_template(
        "dashboard.html",
        total_people     = total_people,
        total_events     = total_events,
        recognized_count = recognized_count,
        unknown_count    = unknown_count,
        recent_events    = recent_events,
        unknown_events   = unknown_events,
        chart_days       = json.dumps(days),
        chart_counts     = json.dumps(counts),
        recognized_chart = recognized_count,
        unknown_chart    = unknown_count,
        camera_status    = camera_status,
        mail_enabled     = mail_enabled,
    )
