# routes/people.py
# Register, view, and delete people in the face database.

import os
import logging
from datetime     import datetime, timezone
from flask        import (Blueprint, render_template, redirect, url_for,
                          flash, request, current_app, send_from_directory, abort)
from flask_login  import login_required
from werkzeug.utils import secure_filename
from extensions   import db
from models       import RegisteredPerson
from services.face_recognition_service import detect_and_encode

people = Blueprint("people", __name__)
logger = logging.getLogger(__name__)


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


@people.route("/people")
@login_required
def list_people():
    q      = request.args.get("q", "").strip()
    query  = RegisteredPerson.query
    if q:
        query = query.filter(RegisteredPerson.name.ilike(f"%{q}%"))
    persons = query.order_by(RegisteredPerson.created_at.desc()).all()
    return render_template("people.html", persons=persons, search=q)


@people.route("/people/add", methods=["GET", "POST"])
@login_required
def add_person():
    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        identifier = request.form.get("identifier", "").strip()
        file       = request.files.get("face_image")

        # ── Validation ────────────────────────────────────────────────────────
        if not name:
            flash("Name is required.", "danger")
            return render_template("add_person.html")

        if not file or file.filename == "":
            flash("Please upload a face image.", "danger")
            return render_template("add_person.html")

        if not _allowed_file(file.filename):
            flash("Only JPG and PNG images are accepted.", "danger")
            return render_template("add_person.html")

        # ── Save file safely ──────────────────────────────────────────────────
        faces_folder = current_app.config["FACES_FOLDER"]
        os.makedirs(faces_folder, exist_ok=True)

        safe_name = secure_filename(file.filename)
        ts        = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename  = f"{ts}_{safe_name}"
        filepath  = os.path.join(faces_folder, filename)
        file.save(filepath)

        # ── Detect and encode face ────────────────────────────────────────────
        encoding, error = detect_and_encode(filepath)

        if error:
            os.remove(filepath)   # clean up unusable file
            flash(f"Face detection failed: {error}", "danger")
            return render_template("add_person.html")

        # ── Save to database ──────────────────────────────────────────────────
        person = RegisteredPerson(
            name       = name,
            identifier = identifier or None,
            image_path = filename,
        )
        person.set_encoding(encoding)
        db.session.add(person)
        db.session.commit()

        flash(f"'{name}' has been registered successfully.", "success")
        logger.info("Registered new person: %s (id=%s)", name, person.id)
        return redirect(url_for("people.list_people"))

    return render_template("add_person.html")


@people.route("/people/<int:person_id>")
@login_required
def person_detail(person_id):
    person = RegisteredPerson.query.get_or_404(person_id)
    return render_template("person_detail.html", person=person)


@people.route("/people/<int:person_id>/delete", methods=["POST"])
@login_required
def delete_person(person_id):
    person = RegisteredPerson.query.get_or_404(person_id)

    # Delete the face image file
    if person.image_path:
        fp = os.path.join(current_app.config["FACES_FOLDER"], person.image_path)
        if os.path.exists(fp):
            os.remove(fp)

    db.session.delete(person)
    db.session.commit()
    flash(f"'{person.name}' has been removed from the database.", "success")
    logger.info("Deleted person: %s", person.name)
    return redirect(url_for("people.list_people"))


@people.route("/uploads/faces/<path:filename>")
@login_required
def serve_face_image(filename):
    """Serve face images only to authenticated admins."""
    return send_from_directory(current_app.config["FACES_FOLDER"], filename)
