# app/routes/crawling.py
import concurrent
from flask import jsonify
from flask_smorest import Blueprint
from flask.views import MethodView
from app.models.models import City
from app.schemas.schemas import WeatherSchema
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
        
        # 並列処理で複数都市の天気情報を取得
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 各都市の天気情報を非同期で取得
            results = executor.map(get_temperature_by_url, [city.temperature_url for city in cities])
        
        # 並列処理で返された結果をリストに追加
        for city, temperature in zip(cities, results):
            if temperature:  # 温度が取得できた場合のみ追加
                weather_data.append({
                    "city": city.city,
                    "lat": city.coordinates.get("latitude"),  # 緯度を取得
                    "lon": city.coordinates.get("longitude"),  # 経度を取得
                    "temperature": temperature,  # 温度情報
                })

        return weather_data, 200


@bp.route("/lotto10")
class Lotto10(MethodView):
    @bp.doc(description="韓国のロト6の最新10個の当選番号")
    @bp.response(200, description="当選番号の取得に成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def get(self):
        # selenium ヘッドレスChrome設定
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        
        driver.get("https://superkts.com/lotto/recent/10")
        # 例：最大10秒間、article.result.list が見つかるまで待つ
        wait = WebDriverWait(driver, 10)
        article = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.result.list")))

        # すべての<tr>を取得
        trs = article.find_elements(By.TAG_NAME, "tr")

        results = []

        # 3番目〜12番目（インデックス2〜11）をループ
        for tr in trs[2:12]:
            tds = tr.find_elements(By.TAG_NAME, "td")
            numbers = [td.text.strip() for td in tds if td.text.strip().isdigit()]
            
            if len(numbers) >= 8:
                # 最初の数字が回数、そのあとの7つが当選番号
                draw_num = numbers[0]
                draw_values = list(dict.fromkeys(map(int, numbers[1:8])))
                results.append({int(draw_num): draw_values})

        driver.quit()

        return jsonify(results), 200
