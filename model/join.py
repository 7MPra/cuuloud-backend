from engine.settings import db, ma
from datetime import datetime


class Join(db.Model):
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, unique=True)
    user_id = db.Column(db.String(length=255), primary_key=True)
    room_id = db.Column(db.String(length=255), primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __tablename__ = 'join'


class JoinSchema(ma.Schema):
    class Meta:
        fields = ("id", "user_id", "room_id", "created_at")
