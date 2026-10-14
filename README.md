# Smart Identity Detection System
### Facial Recognition and Security Monitoring
**B.Tech Cybersecurity Mini Project**

---

## What This Project Does

A Flask web application that uses your laptop webcam to:
- Detect and identify registered faces in real time
- Label unrecognised faces as **UNKNOWN**
- Send email alerts for unknown detections
- Save snapshots of unknown events
- Log all detection events with filters and CSV export
- Display everything on a dark security dashboard

---

## Quick Start

### Step 1 — Open the project folder
In Terminal, change to the folder where you cloned this repository:
```sh
cd /path/to/smart-identity-flask
```

### Step 2 — Create and activate a virtual environment
On macOS or Linux:
```sh
python3 -m venv .venv
source .venv/bin/activate
```
On Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies
```sh
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS, face recognition depends on `dlib`, which may need Apple's Command Line Tools and CMake to build. Install the Command Line Tools with `xcode-select --install`; if the install reports that CMake is missing, install CMake using your package manager and retry.

### Step 4 — Configure local settings
Copy `.env.example` to `.env` (`cp .env.example .env` on macOS/Linux, or `Copy-Item .env.example .env` in PowerShell) and set a private `SECRET_KEY`. `.env` is local-only and is not included in GitHub. Email alerts remain disabled unless you configure SMTP settings.

### Step 5 — Create the admin account (first time only)
```sh
python create_admin.py
```
Enter a username and password when prompted.

### Step 6 — Start the application
```sh
python app.py
```
You will see:
```
* Running on http://127.0.0.1:5000
```

### Step 7 — Open in a browser
```
http://127.0.0.1:5000
```
Log in with the account you created in Step 5.

---

## Features

| Page | What it does |
|---|---|
| Dashboard | Stats cards, charts, recent events |
| Live Monitoring | Webcam feed, real-time recognition |
| Registered People | Add, view, delete registered faces |
| Detection History | Filter, sort, paginate, export CSV |
| Security Alerts | Unknown-face events with snapshots |
| Settings | Threshold, cooldown, email, password |

---

## Adding Known Faces

Add consented `.jpg` / `.png` photos to your local `known_faces/` folder. Face photos are excluded from GitHub by default; add them separately on each computer.
The filename (without extension) becomes the person's name.

```
known_faces/
  Sathish.jpeg    ← already included
  YourName.jpg    ← add more here
```

Restart `python app.py` to import new faces automatically.
Or use **Registered People → Register Person** in the dashboard.

---

## Email Alerts

Email alerts are disabled by default. Configure SMTP values in your local `.env` file to enable them. To test: open **Settings** → click **Send Test Email**.

---

## Project Structure

```
smart-identity-flask/
├── app.py                        ← Entry point, run this
├── config.py                     ← All settings (reads from .env)
├── extensions.py                 ← Flask extensions (db, login, csrf)
├── models.py                     ← Database models
├── create_admin.py               ← First-time admin setup
├── requirements.txt              ← Python dependencies
├── .env.example                  ← Safe template for local settings
├── known_faces/                  ← Local face photos (not committed)
├── routes/
│   ├── auth.py                   ← Login / logout / setup
│   ├── dashboard.py              ← Dashboard stats
│   ├── people.py                 ← Register / manage people
│   ├── monitoring.py             ← Webcam + MJPEG stream
│   ├── events.py                 ← History, alerts, CSV export
│   └── settings.py               ← Settings page
├── services/
│   ├── face_recognition_service.py  ← Face encoding and matching
│   ├── camera_service.py            ← Webcam lifecycle
│   ├── event_service.py             ← DB events and cooldowns
│   └── email_service.py             ← SMTP email alerts
├── templates/                    ← HTML pages (Jinja2)
├── static/css/style.css          ← Dark navy dashboard styles
├── static/js/monitoring.js       ← Live result polling
├── instance/identity.db          ← SQLite database (auto-created)
└── uploads/                      ← Face images and snapshots
```

---

## Common Errors and Fixes

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt` |
| `dlib` install/build error on macOS | Install Apple's Command Line Tools; install CMake if requested, then retry the requirements install |
| Camera won't open | Check webcam is connected. Try `CAMERA_INDEX=1` in `.env` |
| No face detected on upload | Use a clear, well-lit, front-facing photo |
| Email not sending | Use a Gmail App Password in `.env`, not your Gmail login password |
| `identity.db` missing | Run `python app.py` once — it creates the DB automatically |
| PowerShell blocks `.ps1` activation | Use `.venv\\Scripts\\activate.bat` in Command Prompt instead |

---

## How Face Recognition Works

1. When a person is registered, the system detects the face in the photo and generates **128 numerical features** (a face encoding) using a deep neural network.
2. During live monitoring, the same process runs on each webcam frame.
3. The new face encoding is compared against all registered encodings using **Euclidean distance**.
4. If the distance is below the threshold (default **0.55**), the person is identified.
5. Otherwise the face is labelled **UNKNOWN**.

> Note: Accuracy depends on lighting, angle, and photo quality. The threshold can be adjusted in Settings. This system is for academic demonstration only.

---

## Privacy Notice

- Only register individuals who have given informed consent
- Face encodings are stored locally and not shared externally
- Snapshots of unknown faces are saved in `uploads/snapshots/`
- Delete registrations and snapshots when no longer needed
- This system is **not suitable** for consequential access-control decisions

---

## Viva Questions (15)

1. What library does this project use for face recognition, and how does it work?
2. What is a face encoding and how many values does it contain?
3. What is the recognition threshold and how do you choose a good value?
4. How does the system prevent the same face from creating hundreds of database events?
5. How does Flask stream the webcam feed to the browser?
6. How are passwords stored and why is plaintext storage unsafe?
7. What is CSRF and how does Flask-WTF protect against it?
8. What does UNKNOWN mean in your system? Does it mean the person is dangerous?
9. How does the system handle a webcam that is unavailable?
10. Why are face images served through a Flask route rather than directly from disk?
11. What database does this project use and why is it appropriate for this project?
12. How does Flask-Login protect dashboard routes from unauthenticated access?
13. How does the email alert work? What SMTP settings does it need?
14. What is the purpose of the `known_faces/` folder?
15. What are three real limitations of this face recognition system?
