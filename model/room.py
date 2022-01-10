from engine.settings import db, ma
from datetime import datetime


class Room(db.Model):
    id = db.Column(db.String(length=255), primary_key=True, unique=True)
    name = db.Column(db.Unicode(length=255))
    host_id = db.Column(db.String(length=255))
    host_name = db.Column(db.String(length=255))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __tablename__ = 'room'


class RoomSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "host_id", "host_name", "created_at")
