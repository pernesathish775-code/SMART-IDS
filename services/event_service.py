# services/event_service.py
# Creates and manages DetectionEvent records.
# Cooldown logic lives here to prevent duplicate DB writes.

import os
import cv2
import logging
from datetime  import datetime, timezone
from extensions import db
from models    import DetectionEvent
from services.email_service import send_unknown_alert

logger = logging.getLogger(__name__)

# In-memory cooldown tracker: maps "person_id or UNKNOWN" -> last event timestamp
_last_event_time = {}


def should_record(key, cooldown_seconds):
    """
    Return True if enough time has passed since the last event for this key.
    key is the person's id (int) or the string "UNKNOWN".
    """
    now  = datetime.now(timezone.utc).timestamp()
    last = _last_event_time.get(key, 0)
    return (now - last) >= cooldown_seconds


def record_event(person_id, event_type, frame_bgr, snapshot_folder,
                 cooldown_seconds, app_config):
    """
    Save a detection event to the database.
    Saves a snapshot image for UNKNOWN events when snapshot_folder exists.
    Sends an email alert for UNKNOWN events when email is configured.
    Returns the new DetectionEvent or None if cooldown suppressed it.
    """
    cooldown_key = person_id if person_id is not None else "UNKNOWN"

    if not should_record(cooldown_key, cooldown_seconds):
        return None   # cooldown not yet expired — skip

    _last_event_time[cooldown_key] = datetime.now(timezone.utc).timestamp()

    snapshot_path = None

    # Save a snapshot for UNKNOWN events
    if event_type == "UNKNOWN" and frame_bgr is not None and snapshot_folder:
        try:
            os.makedirs(snapshot_folder, exist_ok=True)
            ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"unknown_{ts}.jpg"
            filepath = os.path.join(snapshot_folder, filename)
            cv2.imwrite(filepath, frame_bgr)
            # Store only the filename — not an absolute path
            snapshot_path = filename
        except Exception as e:
            logger.error("Could not save snapshot: %s", type(e).__name__)

    event = DetectionEvent(
        person_id     = person_id,
        event_type    = event_type,
        detected_at   = datetime.now(timezone.utc),
        snapshot_path = snapshot_path,
        email_status  = "not_sent",
    )
    db.session.add(event)
    db.session.commit()

    # Send email for UNKNOWN events
    if event_type == "UNKNOWN":
        status = send_unknown_alert(app_config, event.id, event.detected_at)
        event.email_status = status
        db.session.commit()

    logger.info("Event recorded: %s (id=%s)", event_type, event.id)
    return event


def reset_cooldowns():
    """Clear all cooldown timers — useful when monitoring restarts."""
    _last_event_time.clear()
