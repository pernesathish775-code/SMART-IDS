# routes/events.py
# Detection history, security alerts, CSV export, snapshot viewing.

import os
import csv
import io
import logging
from datetime     import datetime, timezone
from flask        import (Blueprint, render_template, request, abort,
                          send_from_directory, current_app,
                          make_response, redirect, url_for)
from flask_login  import login_required
from models       import DetectionEvent, RegisteredPerson

events = Blueprint("events", __name__)
logger = logging.getLogger(__name__)

PAGE_SIZE = 20   # events per page


@events.route("/events")
@login_required
def history():
    q          = request.args.get("q", "").strip()
    event_type = request.args.get("type", "").strip()
    date_from  = request.args.get("from", "").strip()
    date_to    = request.args.get("to",   "").strip()
    sort       = request.args.get("sort", "desc")
    page       = int(request.args.get("page", 1))

    query = DetectionEvent.query

    # Filter by event type
    if event_type in ("RECOGNIZED", "UNKNOWN", "CAMERA_ERROR"):
        query = query.filter_by(event_type=event_type)

    # Filter by date range
    try:
        if date_from:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query   = query.filter(DetectionEvent.detected_at >= dt_from)
        if date_to:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            # Include the entire "to" day
            from datetime import timedelta
            query = query.filter(DetectionEvent.detected_at < dt_to + timedelta(days=1))
    except ValueError:
        pass   # invalid date input — ignore silently

    # Sort
    order = (DetectionEvent.detected_at.desc()
             if sort != "asc" else DetectionEvent.detected_at.asc())
    query = query.order_by(order)

    total    = query.count()
    ev_list  = query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
    pages    = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    return render_template(
        "events.html",
        events     = ev_list,
        page       = page,
        pages      = pages,
        total      = total,
        q          = q,
        event_type = event_type,
        date_from  = date_from,
        date_to    = date_to,
        sort       = sort,
    )


@events.route("/events/<int:event_id>")
@login_required
def detail(event_id):
    event  = DetectionEvent.query.get_or_404(event_id)
    person = RegisteredPerson.query.get(event.person_id) if event.person_id else None
    snapshot_exists = False
    if event.snapshot_path:
        fp = os.path.join(current_app.config["SNAPSHOT_FOLDER"], event.snapshot_path)
        snapshot_exists = os.path.isfile(fp)
    return render_template("event_details.html",
                           event=event, person=person,
                           snapshot_exists=snapshot_exists)


@events.route("/events/snapshot/<path:filename>")
@login_required
def view_snapshot(filename):
    """Serve snapshot images to authenticated users only."""
    folder = current_app.config["SNAPSHOT_FOLDER"]
    fp     = os.path.join(folder, filename)
    if not os.path.isfile(fp):
        abort(404)
    return send_from_directory(folder, filename)


@events.route("/events/export/csv")
@login_required
def export_csv():
    """Export all events as a CSV file."""
    all_events = (DetectionEvent.query
                  .order_by(DetectionEvent.detected_at.desc()).all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Person Name", "Event Type", "Detected At (UTC)",
                     "Snapshot", "Email Status"])

    for ev in all_events:
        name = ev.person.name if ev.person else "UNKNOWN"
        writer.writerow([
            ev.id, name, ev.event_type,
            ev.detected_at.strftime("%Y-%m-%d %H:%M:%S") if ev.detected_at else "",
            "Yes" if ev.snapshot_path else "No",
            ev.email_status or "—",
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=detection_history.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


@events.route("/alerts")
@login_required
def alerts():
    """Security alerts page — unknown-face events only."""
    unknown_events = (DetectionEvent.query
                      .filter_by(event_type="UNKNOWN")
                      .order_by(DetectionEvent.detected_at.desc())
                      .limit(50).all())

    # Check which snapshots actually exist on disk
    snap_folder = current_app.config["SNAPSHOT_FOLDER"]
    for ev in unknown_events:
        ev._snap_ok = (
            bool(ev.snapshot_path) and
            os.path.isfile(os.path.join(snap_folder, ev.snapshot_path))
        )

    return render_template("alerts.html", events=unknown_events)
