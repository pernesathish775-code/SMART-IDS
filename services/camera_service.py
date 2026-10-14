# services/camera_service.py
# Manages the webcam lifecycle and MJPEG frame generation.
# Only one camera instance is open at a time (protected by a threading.Lock).

import cv2
import threading
import logging
import numpy as np
import face_recognition
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Shared camera state ───────────────────────────────────────────────────────
_lock        = threading.Lock()
_capture     = None    # cv2.VideoCapture instance
_is_running  = False
_frame_count = 0       # counts frames since camera started

# Latest annotated frame as JPEG bytes (updated by the processing thread)
_latest_jpeg = None
_latest_jpeg_lock = threading.Lock()

# Latest recognition result text
_latest_result = "Camera not started"


def start_camera(camera_index):
    """Open the webcam. Returns (success: bool, message: str)."""
    global _capture, _is_running, _frame_count, _latest_result

    with _lock:
        if _is_running:
            return True, "Camera is already running."

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return False, (
                "Could not open the webcam. "
                "Check that it is connected and not in use by another application."
            )

        _capture    = cap
        _is_running = True
        _frame_count = 0
        _latest_result = "Initialising…"

    logger.info("Camera started (index=%s)", camera_index)
    return True, "Camera started."


def stop_camera():
    """Release the webcam and reset state."""
    global _capture, _is_running, _latest_result, _latest_jpeg

    with _lock:
        if _capture is not None:
            _capture.release()
            _capture = None
        _is_running    = False
        _latest_result = "Camera stopped."
        with _latest_jpeg_lock:
            _latest_jpeg = None

    logger.info("Camera stopped.")


def is_running():
    return _is_running


def get_latest_result():
    return _latest_result


def generate_frames(registered_people, threshold, process_every_n,
                    record_event_fn):
    """
    Generator that yields MJPEG frames for the /video_feed route.

    registered_people  -- list of RegisteredPerson ORM objects
    threshold          -- face matching distance threshold
    process_every_n    -- run recognition on every Nth frame
    record_event_fn    -- callable(person_id, event_type, frame_bgr)
    """
    global _frame_count, _latest_result

    import face_recognition as fr

    # Build cached encoding arrays
    known_encodings = []
    known_names     = []
    known_ids       = []

    for person in registered_people:
        try:
            enc = np.array(person.get_encoding())
            known_encodings.append(enc)
            known_names.append(person.name)
            known_ids.append(person.id)
        except Exception:
            pass

    while _is_running:
        with _lock:
            if _capture is None or not _capture.isOpened():
                break
            ok, frame = _capture.read()

        if not ok:
            logger.warning("Failed to read frame from camera.")
            break

        _frame_count += 1

        # Only run recognition on every Nth frame
        if _frame_count % process_every_n == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations  = fr.face_locations(rgb)
            encodings  = fr.face_encodings(rgb, locations)

            label_text = "No face detected"

            for location, encoding in zip(locations, encodings):
                top, right, bottom, left = location

                if known_encodings:
                    distances = fr.face_distance(known_encodings, encoding)
                    best_idx  = int(np.argmin(distances))
                    best_dist = float(distances[best_idx])
                else:
                    best_dist = 1.0

                if known_encodings and best_dist <= threshold:
                    name      = known_names[best_idx]
                    person_id = known_ids[best_idx]
                    color     = (0, 220, 60)      # green
                    label_text = f"RECOGNIZED: {name}"
                    record_event_fn(person_id, "RECOGNIZED", frame)
                else:
                    name      = "UNKNOWN"
                    person_id = None
                    color     = (30, 30, 220)     # red
                    label_text = "UNKNOWN"
                    record_event_fn(None, "UNKNOWN", frame)

                # Draw bounding box and name
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            _latest_result = label_text

        # Timestamp watermark
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, ts, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)

        # Encode frame as JPEG
        ok2, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok2:
            continue

        jpeg_bytes = jpeg.tobytes()
        with _latest_jpeg_lock:
            _latest_jpeg = jpeg_bytes

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
        )
