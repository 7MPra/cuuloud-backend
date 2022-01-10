from engine.settings import db, ma
from datetime import datetime


class Invite(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(length=255))
    email = db.Column(db.String(length=255))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __tablename__ = 'invite'


class InviteSchema(ma.Schema):
    class Meta:
        fields = ("user_id", "email", "created_at")
