# app/routes/crawling.py
import concurrent
from flask_smorest import Blueprint
from flask.views import MethodView
from app.models.models import City
from app.schemas.schemas import WeatherSchema
from bs4 import BeautifulSoup
import requests

bp = Blueprint("crawling", __name__, description="クローリングルート")

def get_temperature_by_url(temperature_url):
    try:
        # ヘッダーを指定してGETリクエストを送る
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(temperature_url, headers=headers)
        response.raise_for_status()  # ステータスコードが200以外の場合、例外を発生させる

    except requests.exceptions.RequestException as e:
        print(f"URLへのアクセス中にエラーが発生しました: {e}")
        print("ウェブサイトの構造が変更されたか、アクセスがブロックされている可能性があります。")
        return None

    # BeautifulSoupを使ってHTMLを解析
    soup = BeautifulSoup(response.text, 'html.parser')
    header_inner_div = soup.find('div', class_='header-inner')

    if header_inner_div:
        header_temp_span = header_inner_div.find('span', class_='header-temp')

        if header_temp_span:
            return header_temp_span.get_text(strip=True)  # 温度を返す
        else:
            print("警告: <div class=\"header-inner\"> 内に <span class=\"header-temp\"> が見つかりませんでした。")
            return None
    else:
        print("エラー: <div class=\"header-inner\"> が見つかりませんでした。")
        return None

@bp.route("/weather/<string:city>")
class Weather(MethodView):
    @bp.doc(description="天気情報の取得")
    @bp.response(200, WeatherSchema, description="天気情報の取得に成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def get(self, city):
        _city = city.lower().title()
        target_city = City.query.filter_by(city=_city).first()
        if not target_city:
            print(f"エラー: {_city} の都市がCityテーブルに存在しません。")
            return None
        weather_info = {
            "city": _city,
            "temperature": get_temperature_by_url(target_city.temperature_url),
        }
        return weather_info, 200

@bp.route("/weatherAll")
class WeatherAll(MethodView):
    @bp.doc(description="複数都市の天気情報を一度に取得")
    @bp.response(200, WeatherSchema(many=True), description="複数都市の天気情報を取得に成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def get(self):
        weather_data = []

        # Cityテーブルからすべての都市を取得
        cities = City.query.all()
        # city: temperature_url のペアを辞書に格納
        url_dict = {city.city: city.temperature_url for city in cities}
        
        # 並列処理で複数都市の天気情報を取得
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 各都市の天気情報を非同期で取得
            results = executor.map(get_temperature_by_url, url_dict.values())
        
        # 並列処理で返された結果をリストに追加
        for city, temperature in zip(url_dict.keys(), results):
            if temperature:  # 温度が取得できた場合のみ追加
                weather_data.append({
                    "city": city,
                    "temperature": temperature,
                })

        return weather_data, 200
