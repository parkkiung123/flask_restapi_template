# app/models/user.py
from app.extensions import db
import enum
from sqlalchemy import func, Enum
from sqlalchemy.dialects.postgresql import JSON

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(100), unique=True, nullable=False)
    userpass = db.Column(db.String(100), nullable=False)  # ハッシュ済みパスワードを保存

class SensorType(enum.Enum):
    """
    jsonの説明
        face_dist (例)
            - value : 100.02
            - unit : cm
            - latitude : 35.6895
            - longitude : 139.6917
        temperature (例)
            - value : 30.5
            - unit : Celsius (Celsius, Fahrenheit)
            - latitude : 35.6895
            - longitude : 139.6917
    """
    face_dist = "face_dist"
    temperature = "temperature"

class SensorStatus(enum.Enum):
    off = 0
    on = 1

class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    type = db.Column(Enum(SensorType), nullable=False)
    data = db.Column(JSON, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    status = db.Column(Enum(SensorStatus), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Sensor id={self.id} type={self.type.value} status={self.status.name} timestamp={self.timestamp}>"