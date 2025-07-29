# app/models/user.py
from app.extensions import db
import enum
from sqlalchemy import func, Enum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import LargeBinary  # これがBYTEA相当

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    userpass = db.Column(db.String(100), nullable=False)  # ハッシュ済みパスワードを保存
    facephoto = db.Column(LargeBinary, nullable=True) 

class SensorType(enum.Enum):
    face_dist = "face_dist"
    temperature = "temperature"

class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    type = db.Column(Enum(SensorType), nullable=False)
    data = db.Column(JSON, nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.Integer, nullable=False) # 0 : off, 1 : on
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Sensor id={self.id} type={self.type.value} status={self.status} timestamp={self.timestamp}>"