# app/routes/crawling.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import zipfile
import glob
import shutil
import re
import base64
import concurrent
from flask import abort, jsonify, current_app, send_file, after_this_request
from flask_smorest import Blueprint
from flask.views import MethodView
import yt_dlp
from app.models.models import City
from app.schemas.schemas import MangaDexSchema, WeatherSchema, YoutubeDownloaderSchema
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
    
@bp.route("/youtube")
class YoutubeDownloader(MethodView):
    @bp.doc(description="MangaDexのchapterIdから該当チャプターのマンガをダウンロード")
    @bp.arguments(YoutubeDownloaderSchema, location="json")
    @bp.response(200, description="マンガのダウンロードに成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def post(self, data):
        url = data["url"]
        # 保存先ディレクトリを作成
        save_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "youtube")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_filename = f"downloaded_video_{timestamp}.mp4"
        output_path = os.path.join(save_dir, output_filename)
        # yt-dlpオプション
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': output_path,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            # ファイルが存在するかチェックして返す
            if os.path.exists(output_path):
                return send_file(output_path, as_attachment=True, mimetype='video/mp4')
            else:
                abort(404, description="動画ファイルが見つかりません。")
        except Exception as e:
            return {"error": f"ダウンロードに失敗しました: {str(e)}"}, 400


@bp.route("/mangadex")
class MangaDex(MethodView):
    base_url = "https://mangadex.org/chapter"
    max_wait_time = 5 # 秒

    def sanitize_filename(self, name):
        # ホワイトスペースを除去
        name = re.sub(r'\s+', '', name)
        # ファイル名として使えない文字を除去（Windowsの場合）
        name = re.sub(r'[\\/:"*?<>|]+', '', name)
        return name

    def get_page_info(self, driver, base_url):    
        driver.get(base_url)
        try:
            # ページ情報が出るまで待機
            WebDriverWait(driver, self.max_wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.reader--meta.page"))
            )

            # 各要素を取得
            page_text = driver.find_element(By.CSS_SELECTOR, "div.reader--meta.page").text.strip()
            title_text = driver.find_element(By.CSS_SELECTOR, "a.reader--header-manga").text.strip()
            chapter_text = driver.find_element(By.CSS_SELECTOR, "div.reader--meta.chapter").text.strip()

            # 1. ページ数（例: "Pg. 1 / 21" → 21）
            match = re.search(r'/\s*(\d+)', page_text)
            max_page = int(match.group(1)) if match else None

            # 2. タイトル（例: "Dragon Ball GT" → "DragonBallGT"）
            clean_title = self.sanitize_filename(title_text)

            # 3. チャプター（例: "Vol. 1, Ch. 1" → "Vol1Ch1"）
            clean_chapter = re.sub(r'[\s.,]', '', chapter_text)

            return {
                "page": max_page,
                "title": clean_title,
                "chapter": clean_chapter
            }

        except Exception as e:
            print("❌ 要素取得に失敗:", e)
            return None

    def save_blob_image(self, driver, img_element, file_prefix, page_num):
        # JavaScriptでCanvasに描画してBase64データ取得
        script = """
        var img = arguments[0];
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/jpeg').split(',')[1];
        """
        base64_str = driver.execute_script(script, img_element)
        img_data = base64.b64decode(base64_str)
        img_path = os.path.join(self.img_dir, f"{file_prefix}_{page_num}.jpg")
        with open(img_path, "wb") as f:
            f.write(img_data)
        print(f"ページ{page_num}の画像を保存しました: {img_path}")

    def wait_for_blob_image_loaded(self, driver, timeout):
        WebDriverWait(driver, timeout).until(
            lambda d: any(
                img.get_attribute("src").startswith("blob:") and
                d.execute_script("return arguments[0].complete && arguments[0].naturalWidth > 0;", img)
                for img in d.find_elements(By.TAG_NAME, "img")
            )
        )

    @bp.doc(description="MangaDexのchapterIdから該当チャプターのマンガをダウンロード")
    @bp.arguments(MangaDexSchema, location="json")
    @bp.response(200, description="マンガのダウンロードに成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def post(self, data):        
        self.upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "mangadex")
        base_url = self.base_url + "/" + data["chapterId"]
        # Chrome headless設定
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)

        page_info = self.get_page_info(driver, base_url)
        if not page_info:
            print("ページ情報取得できず終了")
            driver.quit()
            abort(400, description="ページ情報取得できず終了")
        
        file_prefix = f'{page_info["title"]}_{page_info["chapter"]}'        
        self.img_dir = os.path.join(self.upload_folder, "images")
        os.makedirs(self.img_dir, exist_ok=True)
        zip_path = os.path.join(self.img_dir, f"{file_prefix}.zip")
        if os.path.exists(zip_path):
            driver.quit()
            return send_file(zip_path, as_attachment=True, mimetype='application/zip')

        for page_num in range(1, page_info["page"] + 1):
            url = f"{base_url}/{page_num}"
            driver.get(url)

            try:
                selector_text = "img[src^='blob:']"
                WebDriverWait(driver, self.max_wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector_text))
                )
                self.wait_for_blob_image_loaded(driver, self.max_wait_time)

                visible_blob_imgs = driver.find_elements(By.CSS_SELECTOR, selector_text)
                visible_blob_imgs = [
                    img for img in visible_blob_imgs
                    if "display:none" not in (img.get_attribute("style") or "").replace(" ", "").lower()
                ]

                if len(visible_blob_imgs) == 1:
                    self.save_blob_image(driver, visible_blob_imgs[0], file_prefix, page_num)
                else:
                    print(f"ページ{page_num}: 表示されているblob画像が1個ではありません。{len(visible_blob_imgs)}個見つかりました。")
                    html_dir = os.path.join(self.upload_folder, "htmls")
                    os.makedirs(html_dir, exist_ok=True)
                    html_path = os.path.join(html_dir, f"{file_prefix}_{page_num}.html")
                    with open(html_path, "w", encoding="utf-8") as f:
                        for img in visible_blob_imgs:
                            outer_html = img.get_attribute("outerHTML")
                            f.write(outer_html + "\n")
                    print(f"ページ {page_num} のvisible_blob_imgsのHTMLを保存しました: {html_path}")

            except Exception as e:
                print(f"ページ{page_num}の画像取得失敗:", e)
                driver.quit()
                abort(400, description=f"ページ{page_num}の画像取得失敗")

        driver.quit()

        # jpgファイルをZIPにまとめる
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for jpg_file in glob.glob(os.path.join(self.img_dir, "*.jpg")):
                zipf.write(jpg_file, os.path.basename(jpg_file))
        try:
            for filename in os.listdir(self.img_dir):
                file_path = os.path.join(self.img_dir, filename)
                # ZIPファイルは削除しない
                if file_path == zip_path:
                    continue
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            print("jpgファイル削除完了")
        except Exception as e:
            print(f"jpgファイル削除エラー: {e}")
            abort(404, description="jpgファイル削除エラー")

        if os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, mimetype='application/zip')
        else:
            abort(404, description="ZIPファイルが見つかりません。")

@bp.route("/mangadex_multiproc")
class MangaDexMultiProc(MethodView):
    base_url = "https://mangadex.org/chapter"
    max_wait_time = 5 # 秒

    def sanitize_filename(self, name):
        # ホワイトスペースを除去
        name = re.sub(r'\s+', '', name)
        # ファイル名として使えない文字を除去（Windowsの場合）
        name = re.sub(r'[\\/:"*?<>|]+', '', name)
        return name
    
    def wait_for_js_complete(self, driver, timeout=1):
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        # 追加でAJAXなどの完了を待つ（jQueryがある場合）
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script('return window.jQuery != undefined && jQuery.active == 0')
            )
        except:
            # jQueryが無ければ無視して続行
            pass

    def get_page_info(self, driver, base_url):    
        driver.get(base_url)
        try:
            # ページ情報が出るまで待機
            WebDriverWait(driver, self.max_wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.reader--meta.page"))
            )

            # 各要素を取得
            page_text = driver.find_element(By.CSS_SELECTOR, "div.reader--meta.page").text.strip()
            title_text = driver.find_element(By.CSS_SELECTOR, "a.reader--header-manga").text.strip()
            chapter_text = driver.find_element(By.CSS_SELECTOR, "div.reader--meta.chapter").text.strip()

            # 1. ページ数（例: "Pg. 1 / 21" → 21）
            match = re.search(r'/\s*(\d+)', page_text)
            max_page = int(match.group(1)) if match else None

            # 2. タイトル（例: "Dragon Ball GT" → "DragonBallGT"）
            clean_title = self.sanitize_filename(title_text)

            # 3. チャプター（例: "Vol. 1, Ch. 1" → "Vol1Ch1"）
            clean_chapter = re.sub(r'[\s.,]', '', chapter_text)

            return {
                "page": max_page,
                "title": clean_title,
                "chapter": clean_chapter
            }

        except Exception as e:
            print("❌ 要素取得に失敗:", e)
            return None

    def save_blob_image(self, driver, img_element, file_prefix, page_num):
        # JavaScriptでCanvasに描画してBase64データ取得
        script = """
        var img = arguments[0];
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/jpeg').split(',')[1];
        """
        base64_str = driver.execute_script(script, img_element)
        img_data = base64.b64decode(base64_str)
        img_path = os.path.join(self.img_dir, f"{file_prefix}_{page_num}.jpg")
        with open(img_path, "wb") as f:
            f.write(img_data)
        print(f"ページ{page_num}の画像を保存しました: {img_path}")

    def wait_for_blob_image_loaded(self, driver, timeout):
        WebDriverWait(driver, timeout).until(
            lambda d: any(
                img.get_attribute("src").startswith("blob:") and
                d.execute_script("return arguments[0].complete && arguments[0].naturalWidth > 0;", img)
                for img in d.find_elements(By.TAG_NAME, "img")
            )
        )

    def process_page(self, page_num, base_url, file_prefix):
        # プロセスごとにdriver生成⇒非効率
        url = f"{base_url}/{page_num}"
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        try:
            selector_text = "img[src^='blob:']"
            # 下記、マルチだとたまに失敗する(??)
            # WebDriverWait(driver, self.max_wait_time).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, selector_text))
            # )
            # self.wait_for_blob_image_loaded(driver, self.max_wait_time)
            self.wait_for_js_complete(driver, 5) # timeoutに余裕を持って取得

            visible_blob_imgs = driver.find_elements(By.CSS_SELECTOR, selector_text)
            visible_blob_imgs = [
                img for img in visible_blob_imgs
                if "display:none" not in (img.get_attribute("style") or "").replace(" ", "").lower()
            ]

            if len(visible_blob_imgs) == 1:
                self.save_blob_image(driver, visible_blob_imgs[0], file_prefix, page_num)
            else:
                print(f"ページ{page_num}: 表示されているblob画像が1個ではありません。{len(visible_blob_imgs)}個見つかりました。")
                html_dir = os.path.join(self.upload_folder, "htmls")
                os.makedirs(html_dir, exist_ok=True)
                html_path = os.path.join(html_dir, f"{file_prefix}_{page_num}.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    for img in visible_blob_imgs:
                        outer_html = img.get_attribute("outerHTML")
                        f.write(outer_html + "\n")
                print(f"ページ {page_num} のvisible_blob_imgsのHTMLを保存しました: {html_path}")

        except Exception as e:
            print(f"ページ{page_num}の画像取得失敗:", e)
        driver.quit()

    @bp.doc(description="mangadexのマルチプロセスバージョン")
    @bp.arguments(MangaDexSchema, location="json")
    @bp.response(200, description="マンガのダウンロードに成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def post(self, data):
        """高性能のCPUが必要"""        
        self.upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "mangadex")
        base_url = self.base_url + "/" + data["chapterId"]
        # Chrome headless設定
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)

        page_info = self.get_page_info(driver, base_url)
        if not page_info:
            print("ページ情報取得できず終了")
            driver.quit()
            abort(400, description="ページ情報取得できず終了")
        
        file_prefix = f'{page_info["title"]}_{page_info["chapter"]}'        
        self.img_dir = os.path.join(self.upload_folder, "images")
        os.makedirs(self.img_dir, exist_ok=True)
        zip_path = os.path.join(self.img_dir, f"{file_prefix}.zip")
        if os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, mimetype='application/zip')        
        driver.quit()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for page_num in range(1, page_info["page"] + 1):
                futures.append(executor.submit(self.process_page, page_num, base_url, file_prefix))
            for future in as_completed(futures):
                print(future.result())       

        # jpgファイルをZIPにまとめる
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for jpg_file in glob.glob(os.path.join(self.img_dir, "*.jpg")):
                zipf.write(jpg_file, os.path.basename(jpg_file))
        try:
            for filename in os.listdir(self.img_dir):
                file_path = os.path.join(self.img_dir, filename)
                # ZIPファイルは削除しない
                if file_path == zip_path:
                    continue
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            print("jpgファイル削除完了")
        except Exception as e:
            print(f"jpgファイル削除エラー: {e}")
            abort(404, description="jpgファイル削除エラー")

        if os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, mimetype='application/zip')
        else:
            abort(404, description="ZIPファイルが見つかりません。")