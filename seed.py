# seed.py
from app import create_app
from app.extensions import db
from app.models.models import User, Sensor, SensorType, SensorStatus
import bcrypt
from datetime import datetime

def seed_users():
    app = create_app()
    app.app_context().push()  # Flaskアプリコンテキストを有効化

    if User.query.filter_by(userid="admin").first():
        print("adminユーザーはすでに存在します。")
    else:
        hashed_pw = bcrypt.hashpw("adminpass".encode(), bcrypt.gensalt()).decode()
        admin = User(userid="admin", userpass=hashed_pw)    
        db.session.add(admin)
        db.session.commit()
        print("adminユーザーを登録しました。")

    if Sensor.query.first():
        print("センサーのデータはすでに存在します。")
    else:
        dummy = Sensor(
            device_id="face_dist_001",
            type=SensorType.face_dist,
            data={
                "value": 100.02,
                "unit": "cm",
                "latitude": 35.6895,
                "longitude": 139.6917
            },
            timestamp=datetime.now(),
            status=SensorStatus.on
        )
        db.session.add(dummy)
        db.session.commit()
        print("センサーのダミーデータを登録しました。")

    print("✅seed.pyが完了しました。")

if __name__ == "__main__":
    seed_users()
