import sys
import json
from datetime import datetime
import bcrypt
from app import create_app
from app.extensions import db
from app.models.models import CityTemperature, User, Sensor, SensorType, City

# ユーザーのシーデータを登録
def seed_users():
    if User.query.filter_by(userid="admin").first():
        print("adminユーザーはすでに存在します。")
    else:
        hashed_pw = bcrypt.hashpw("adminpass".encode(), bcrypt.gensalt()).decode()
        admin = User(userid="admin", name="管理者", userpass=hashed_pw)
        db.session.add(admin)
        db.session.commit()
        print("adminユーザーを登録しました。")

    print("✅seed_usersが完了しました。")

# センサーのシーデータを登録
def seed_sensor():
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
            status=1
        )
        db.session.add(dummy)
        db.session.commit()
        print("センサーのダミーデータを登録しました。")

    print("✅seed_sensorが完了しました。")

def seed_cities():
    # JSONファイルからデータを読み込む
    with open("test_data/city_data.json", "r", encoding="utf-8") as f:
        city_data = json.load(f)

    for city_name, data in city_data.items():
        # すでに同じ都市が存在するかチェック
        existing_city = City.query.filter_by(city=city_name).first()

        if existing_city:
            print(f"{city_name} はすでに存在します。")
        else:
            # Cityデータを作成
            new_city = City(
                city=city_name,
                coordinates=data['coordinates'],
                temperature_url=data['temperature_url']
            )

            # DBセッションに追加
            db.session.add(new_city)
            print(f"{city_name} をCityテーブルに追加しました。")

    # コミットしてデータベースに保存
    db.session.commit()
    print("✅seed_citiesが完了しました。")

def seed_city_temperature():
    if CityTemperature.query.first():
        print("都市温度のデータはすでに存在します。")
    else:
        # 例として、"Tokyo"という都市のIDを取得する
        city_name = "Tokyo"
        city = City.query.filter_by(city=city_name).first()

        if city:
            # Cityが存在する場合、CityTemperatureのデータを作成
            city_temperature_data = {
                "value": 25.4,  # 温度
                "unit": "℃"     # 単位
            }

            new_temperature = CityTemperature(
                city_id=city.id,  # 外部キーでCityのIDを参照
                temperature=city_temperature_data,  # 温度データ
                timestamp=datetime.now(),  # 温度データの取得日時
            )

            # DBセッションに追加
            db.session.add(new_temperature)
            db.session.commit()

            print(f"{city_name} の温度データをCityTemperatureテーブルに追加しました。")
        else:
            print(f"{city_name} はCityテーブルに存在しません。")
    print("✅seed_city_temperatureが完了しました。")

if __name__ == "__main__":
    # コマンドライン引数で "test" を受け取ったらテストモード
    # test_mode = "test" in sys.argv
    app = create_app()
    app.app_context().push()
    seed_users()
    seed_sensor()
    seed_cities()
    seed_city_temperature()
