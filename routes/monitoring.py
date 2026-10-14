# routes/monitoring.py
# Live webcam monitoring with MJPEG streaming.

import logging
from flask        import (Blueprint, render_template, Response, jsonify,
                           redirect, url_for, flash, current_app)
from flask_login  import login_required
from extensions   import db
from models       import RegisteredPerson, DetectionEvent
from services     import camera_service
from services.event_service import record_event, reset_cooldowns

monitoring = Blueprint("monitoring", __name__)
logger     = logging.getLogger(__name__)


def _make_record_fn(app, snapshot_folder, cooldown):
    """
    Return a closure that records events.
    The closure is passed to generate_frames so it can be called from the
    streaming generator without needing request context.
    """
    def _record(person_id, event_type, frame_bgr):
        with app.app_context():
            record_event(
                person_id       = person_id,
                event_type      = event_type,
                frame_bgr       = frame_bgr,
                snapshot_folder = snapshot_folder,
                cooldown_seconds= cooldown,
                app_config      = app.config,
            )
    return _record


@monitoring.route("/monitoring")
@login_required
def index():
    recent = (DetectionEvent.query
              .order_by(DetectionEvent.detected_at.desc())
              .limit(10).all())
    return render_template(
        "monitoring.html",
        is_running  = camera_service.is_running(),
        latest_result = camera_service.get_latest_result(),
        recent_events = recent,
    )


@monitoring.route("/monitoring/start", methods=["POST"])
@login_required
def start():
    index  = current_app.config["CAMERA_INDEX"]
    ok, msg = camera_service.start_camera(index)
    reset_cooldowns()
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("monitoring.index"))


@monitoring.route("/monitoring/stop", methods=["POST"])
@login_required
def stop():
    camera_service.stop_camera()
    flash("Camera stopped.", "info")
    return redirect(url_for("monitoring.index"))


@monitoring.route("/video_feed")
@login_required
def video_feed():
    """MJPEG stream — called by the <img> tag on the monitoring page."""
    if not camera_service.is_running():
        # Return a 1x1 blank JPEG so the <img> doesn't break
        return Response(status=204)

    persons    = RegisteredPerson.query.all()
    threshold  = current_app.config["FACE_THRESHOLD"]
    every_n    = current_app.config["PROCESS_EVERY_N_FRAMES"]
    snap_folder = current_app.config["SNAPSHOT_FOLDER"]
    cooldown   = current_app.config["EVENT_COOLDOWN"]

    record_fn = _make_record_fn(current_app._get_current_object(),
                                snap_folder, cooldown)

    return Response(
        camera_service.generate_frames(persons, threshold, every_n, record_fn),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@monitoring.route("/monitoring/status")
@login_required
def status():
    """JSON endpoint polled by monitoring.js to update the result label."""
    return jsonify({
        "is_running": camera_service.is_running(),
        "result":     camera_service.get_latest_result(),
    })
