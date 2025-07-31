# app/routes/crawling.py
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
import zipfile
import glob
import concurrent
from flask import abort, jsonify, current_app, send_file
from flask_smorest import Blueprint
from flask.views import MethodView
import requests
import yt_dlp
from app.models.models import City
from app.routes.utils.crawling_sub import get_temperature_by_url, mangadex_chap_downloader_multi, mangadex_chap_downloader_single
from app.schemas.schemas import MangaDexChapSchema, MangaDexVolSchema, WeatherSchema, YoutubeDownloaderSchema

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

bp = Blueprint("crawling", __name__, description="クローリングルート")

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


@bp.route("/mangadex_chap")
class MangaDexChapMulti(MethodView):
    base_url = "https://mangadex.org/chapter"
    max_wait_time = 5 # 秒
    @bp.doc(description="MangaDexのchapterIdから該当チャプターのマンガをダウンロード(マルチプロセス)")
    @bp.arguments(MangaDexChapSchema, location="json")
    @bp.response(200, description="マンガのダウンロードに成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def post(self, data):
        """CPUコア数の半分で実行される"""        
        upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "mangadex")
        base_url = self.base_url + "/" + data["chapterId"]        
        # ヘッドレスChromeの設定
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        return mangadex_chap_downloader_multi(options, upload_folder, base_url, self.max_wait_time)


@bp.route("/mangadex_chap_singleproc")
class MangaDexChapSingle(MethodView):
    base_url = "https://mangadex.org/chapter"
    max_wait_time = 5 # 秒
    img_dir = ""
    @bp.doc(description="MangaDexのchapterIdから該当チャプターのマンガをダウンロード(シングルプロセス)")
    @bp.arguments(MangaDexChapSchema, location="json")
    @bp.response(200, description="マンガのダウンロードに成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def post(self, data):
        upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "mangadex")
        base_url = self.base_url + "/" + data["chapterId"]        
        # ヘッドレスChromeの設定
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)
        return mangadex_chap_downloader_single(driver, upload_folder, base_url, self.max_wait_time)

@bp.route("/mangadex_vol")
class MangaDexVolMulti(MethodView):
    base_chap_url = "https://mangadex.org/chapter"
    base_feed_url = "https://api.mangadex.org/manga/{}/feed"
    max_wait_time = 5 # 秒
    img_dir = ""
    @bp.doc(description="MangaDexのmangaIdから該当するvolがあればすべてのチャプターをダウンロード")
    @bp.arguments(MangaDexVolSchema, location="json")
    @bp.response(200, description="マンガのダウンロードに成功した場合")
    @bp.alt_response(400, description="無効なリクエスト")
    def post(self, data):
        manga_id = data["mangaId"]
        target_volume = str(data["vol"])

        url = self.base_feed_url.format(manga_id)

        try:
            response = requests.get(url)
            response.raise_for_status()
            feed = response.json()
        except Exception as e:
            abort(400, description=f"MangaDex APIエラー: {str(e)}")

        # volume と type が一致するチャプターを抽出
        matching_chapters = [
            item for item in feed.get("data", [])
            if item.get("type") == "chapter"
            and item["attributes"].get("volume") == target_volume
            and item["attributes"].get("chapter") is not None
        ]

        if not matching_chapters:
            return {"message": f"Volume {target_volume} のチャプターが見つかりませんでした。"}, 200

        # 最初の scanlation_group ID を取得
        first_group_id = None
        for item in matching_chapters:
            for rel in item.get("relationships", []):
                if rel["type"] == "scanlation_group":
                    first_group_id = rel["id"]
                    break
            if first_group_id:
                break

        if not first_group_id:
            abort(400, description="scanlation_group ID が見つかりませんでした。")

        # scanlation_group が一致するチャプターを抽出
        selected_chapters = [
            item for item in matching_chapters
            if any(rel.get("type") == "scanlation_group" and rel.get("id") == first_group_id
                   for rel in item.get("relationships", []))
        ]

        # chapter番号でソート（数値または少数として扱う）
        def parse_chapter(ch):
            try:
                return float(ch["attributes"].get("chapter"))
            except (TypeError, ValueError):
                return float('inf')  # ソート末尾に送る

        selected_chapters.sort(key=parse_chapter)

        chapter_ids = [ch["id"] for ch in selected_chapters]

        upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "mangadex")
              
        # ヘッドレスChromeの設定
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

        max_workers = max(os.cpu_count() // 2, 1)
        total_chapters = len(chapter_ids)
        chaps_per_worker = (total_chapters + max_workers - 1) // max_workers  # 割り切れない場合も対応

        # 各ワーカーが行う処理
        def worker_task(start_idx, end_idx):
            driver = webdriver.Chrome(options=options)
            try:
                for chapter_id in chapter_ids[start_idx:end_idx]:                    
                    base_url = self.base_chap_url + "/" + chapter_id
                    mangadex_chap_downloader_single(driver, upload_folder, base_url, self.max_wait_time, gen_zip=False, driver_quit=False)
            finally:
                driver.quit()

        # 並列実行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(max_workers):
                start_idx = i * chaps_per_worker
                end_idx = min((i + 1) * chaps_per_worker, total_chapters)
                if start_idx >= end_idx:
                    break  # 不要なワーカーを作らない
                futures.append(executor.submit(worker_task, start_idx, end_idx))
            # 全てのスレッドの完了を待つ（オプション）
            for future in futures:
                future.result()

        img_dir = os.path.join(upload_folder, "images")
        jpg_files = glob.glob(os.path.join(img_dir, "*.jpg"))
        zipfile_name = os.path.basename(jpg_files[0]).split("_")[0] + f"_Vol{target_volume}"
        zip_path = os.path.join(img_dir, f"{zipfile_name}.zip")

        # jpgファイルをZIPにまとめる
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for jpg_file in jpg_files:
                zipf.write(jpg_file, os.path.basename(jpg_file))

        if os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, mimetype='application/zip')
        else:
            abort(404, description="ZIPファイルが見つかりません。")
