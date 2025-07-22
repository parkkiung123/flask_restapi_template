# seed.py
import sys
from datetime import datetime
import bcrypt

from app import create_app
from app.extensions import db
from app.models.models import User, Sensor, SensorType, SensorStatus

def seed_users(test_mode=False):
    app = create_app(testing=test_mode)
    app.app_context().push()  # Flaskアプリコンテキストを有効化

    if test_mode:
        db.drop_all()
        db.create_all()
        print("テスト環境のため、DBを再作成しました。")

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
    # コマンドライン引数で "test" を受け取ったらテストモード
    test_mode = "test" in sys.argv
    seed_users(test_mode=test_mode)
