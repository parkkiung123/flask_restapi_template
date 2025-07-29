# app/models/user.py
from app.extensions import db
import enum
from sqlalchemy import func, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
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
    
# Cityテーブル
class City(db.Model):
    __tablename__ = 'city'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), unique=True, nullable=False)  # 都市名
    coordinates = db.Column(JSON, nullable=False)  # 緯度と経度 (例: {"latitude": 37.5665, "longitude": 126.9783})
    temperature_url = db.Column(db.String(300), nullable=False)  # 天気情報のURL

    # CityTemperature テーブルとのリレーション
    temperatures = relationship("CityTemperature", backref="city", lazy=True)

    def __repr__(self):
        return f"<City id={self.id} city={self.city} coordinates={self.coordinates}>"

# CityTemperatureテーブル
class CityTemperature(db.Model):
    __tablename__ = 'city_temperature'

    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, ForeignKey('city.id'), nullable=False)  # 外部キーとしてcityテーブルを参照
    temperature = db.Column(JSON, nullable=True)  # 温度 (例: {"value": 37.5, "unit": "℃"})
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)  # 温度データの取得時刻
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)  # レコード作成日時
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)  # レコード更新日時

    def __repr__(self):
        return f"<CityTemperature id={self.id} city_id={self.city_id} temperature={self.temperature} timestamp={self.timestamp}>"