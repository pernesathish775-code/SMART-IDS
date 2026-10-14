# services/face_recognition_service.py
# All face-detection and face-recognition logic lives here.
# Routes call these functions; they never touch the camera directly.

import face_recognition
import numpy as np
import logging

logger = logging.getLogger(__name__)


def detect_and_encode(image_path):
    """
    Load an image file, detect faces, and return the encoding.

    Returns:
        (encoding, error_message)
        encoding       -- numpy array of 128 floats, or None on failure
        error_message  -- human-readable problem description, or None on success
    """
    try:
        image = face_recognition.load_image_file(image_path)
    except Exception as e:
        logger.error("Could not read image file: %s", image_path)
        return None, "Could not read the image file."

    locations = face_recognition.face_locations(image)

    if len(locations) == 0:
        return None, "No face was detected in the image. Please use a clear front-facing photo."

    if len(locations) > 1:
        return None, (
            f"{len(locations)} faces were detected. "
            "Please upload a photo containing exactly one face."
        )

    encodings = face_recognition.face_encodings(image, locations)
    if not encodings:
        return None, "Could not generate a face encoding. Please try a different photo."

    return encodings[0], None


def identify_face(frame_rgb, registered_people, threshold):
    """
    Given a single video frame (RGB numpy array), detect all faces in it
    and match each one against the registered database.

    registered_people -- list of RegisteredPerson ORM objects

    Returns:
        list of dicts with keys:
            name       -- person's name or "UNKNOWN"
            person_id  -- integer id or None
            distance   -- float (lower = closer match)
            location   -- (top, right, bottom, left) bounding box
    """
    results = []

    if not registered_people:
        # No registered faces to compare against
        face_locations = face_recognition.face_locations(frame_rgb)
        for loc in face_locations:
            results.append({"name": "UNKNOWN", "person_id": None,
                             "distance": 1.0, "location": loc})
        return results

    # Build comparison arrays from registered encodings
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
            logger.warning("Skipping person id=%s: bad encoding", person.id)

    if not known_encodings:
        return results

    # Detect faces in this frame
    face_locations  = face_recognition.face_locations(frame_rgb)
    face_encodings  = face_recognition.face_encodings(frame_rgb, face_locations)

    for location, encoding in zip(face_locations, face_encodings):
        distances = face_recognition.face_distance(known_encodings, encoding)
        best_idx  = int(np.argmin(distances))
        best_dist = float(distances[best_idx])

        if best_dist <= threshold:
            results.append({
                "name":      known_names[best_idx],
                "person_id": known_ids[best_idx],
                "distance":  best_dist,
                "location":  location,
            })
        else:
            results.append({
                "name":      "UNKNOWN",
                "person_id": None,
                "distance":  best_dist,
                "location":  location,
            })

    return results
