from engine.settings import db, ma
from datetime import datetime


class Verify(db.Model):
    token = db.Column(db.String(length=255), primary_key=True, unique=True)
    user_id = db.Column(db.String(length=255), unique=True)
    
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __tablename__ = 'verify'


class VerifySchema(ma.Schema):
    class Meta:
        fields = ("id", "token", "user_id", "created_at")
