from engine.settings import db, ma
from datetime import datetime


class User(db.Model):
    id = db.Column(db.String(length=255), primary_key=True, unique=True)
    password = db.Column(db.String(length=255))
    name = db.Column(db.Unicode(length=255))
    email = db.Column(db.Unicode(length=255), unique=True)
    icon = db.Column(db.Unicode(length=255))
    verified = db.Column(db.Boolean(), default=False)
    ip = db.Column(db.String(length=15))

    invitation_times_limit = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __tablename__ = 'user'


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "icon", "created_at")
