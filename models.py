# models.py  –  SQLAlchemy ORM models
import json
from datetime          import datetime, timezone
from extensions        import db
from flask_login       import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_user"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, plaintext):
        self.password_hash = generate_password_hash(plaintext)

    def check_password(self, plaintext):
        return check_password_hash(self.password_hash, plaintext)


class RegisteredPerson(db.Model):
    __tablename__ = "registered_person"
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(128), nullable=False)
    identifier    = db.Column(db.String(64), nullable=True)
    face_encoding = db.Column(db.Text, nullable=False)
    image_path    = db.Column(db.String(256), nullable=True)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    events        = db.relationship("DetectionEvent", backref="person", lazy=True)

    def set_encoding(self, encoding_array):
        self.face_encoding = json.dumps(encoding_array.tolist())

    def get_encoding(self):
        return json.loads(self.face_encoding)


class DetectionEvent(db.Model):
    __tablename__ = "detection_event"
    id            = db.Column(db.Integer, primary_key=True)
    person_id     = db.Column(db.Integer, db.ForeignKey("registered_person.id"),
                               nullable=True, index=True)
    event_type    = db.Column(db.String(32), nullable=False, index=True)
    detected_at   = db.Column(db.DateTime, nullable=False,
                               default=lambda: datetime.now(timezone.utc), index=True)
    snapshot_path = db.Column(db.String(256), nullable=True)
    email_status  = db.Column(db.String(32), default="not_sent")
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class AppSetting(db.Model):
    __tablename__ = "app_setting"
    id            = db.Column(db.Integer, primary_key=True)
    setting_key   = db.Column(db.String(64), unique=True, nullable=False, index=True)
    setting_value = db.Column(db.String(256), nullable=True)

    @staticmethod
    def get(key, default=None):
        row = AppSetting.query.filter_by(setting_key=key).first()
        return row.setting_value if row else default

    @staticmethod
    def set(key, value):
        row = AppSetting.query.filter_by(setting_key=key).first()
        if row:
            row.setting_value = str(value)
        else:
            db.session.add(AppSetting(setting_key=key, setting_value=str(value)))
        db.session.commit()
