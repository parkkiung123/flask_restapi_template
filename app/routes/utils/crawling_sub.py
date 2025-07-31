from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import zipfile
import glob
import re
import base64
from bs4 import BeautifulSoup
from flask import abort, send_file
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Weather, WeatherAll
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
    
# MangaDexMulti, MangaDexSingle
def sanitize_filename(name):
    # ホワイトスペースを除去
    name = re.sub(r'\s+', '', name)
    # ファイル名として使えない文字を除去（Windowsの場合）
    name = re.sub(r'[\\/:"*?<>|]+', '', name)
    return name

def get_page_info(driver, base_url, max_wait_time):  
    driver.get(base_url)
    try:
        def all_elements_present(driver):
            try:
                page = driver.find_element(By.CSS_SELECTOR, "div.reader--meta.page")
                title = driver.find_element(By.CSS_SELECTOR, "a.reader--header-manga")
                chapter = driver.find_element(By.CSS_SELECTOR, "div.reader--meta.chapter")
                return all([page.text.strip(), title.text.strip(), chapter.text.strip()])
            except Exception:
                return False

        WebDriverWait(driver, max_wait_time).until(all_elements_present)

        # 要素を改めて取得
        page_text = driver.find_element(By.CSS_SELECTOR, "div.reader--meta.page").text.strip()
        title_text = driver.find_element(By.CSS_SELECTOR, "a.reader--header-manga").text.strip()
        chapter_text = driver.find_element(By.CSS_SELECTOR, "div.reader--meta.chapter").text.strip()

        # 1. ページ数（例: "Pg. 1 / 21" → 21）
        match = re.search(r'/\s*(\d+)', page_text)
        max_page = int(match.group(1)) if match else None

        # 2. タイトル（例: "Dragon Ball GT" → "DragonBallGT"）
        clean_title = sanitize_filename(title_text)

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

def save_blob_image(driver, img_dir, img_element, file_prefix, page_num):
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
    img_path = os.path.join(img_dir, f"{file_prefix}_{page_num}.jpg")
    with open(img_path, "wb") as f:
        f.write(img_data)
    print(f"ページ{page_num}の画像を保存しました: {img_path}")

def wait_for_visible_blob_image(driver, timeout):
    def is_visible_blob_img(driver):
        imgs = driver.find_elements(By.CSS_SELECTOR, "img[src^='blob:']")
        visible_imgs = [
            img for img in imgs
            if "display:none" not in (img.get_attribute("style") or "").replace(" ", "").lower()
        ]
        return visible_imgs if visible_imgs else False

    # visible な blob: 画像が1つ以上現れるまで待つ
    return WebDriverWait(driver, timeout).until(is_visible_blob_img)

def process_page(driver, max_wait_time, img_dir, upload_folder, page_num, base_url, file_prefix):
    url = f"{base_url}/{page_num}"
    driver.get(url)
    try:
        selector_text = "img[src^='blob:']"
        wait_for_visible_blob_image(driver, max_wait_time)

        visible_blob_imgs = driver.find_elements(By.CSS_SELECTOR, selector_text)
        visible_blob_imgs = [
            img for img in visible_blob_imgs
            if "display:none" not in (img.get_attribute("style") or "").replace(" ", "").lower()
        ]

        if len(visible_blob_imgs) == 1:
            save_blob_image(driver, img_dir, visible_blob_imgs[0], file_prefix, page_num)
        else:
            print(f"ページ{page_num}: 表示されているblob画像が1個ではありません。{len(visible_blob_imgs)}個見つかりました。")
            html_dir = os.path.join(upload_folder, "htmls")
            os.makedirs(html_dir, exist_ok=True)
            html_path = os.path.join(html_dir, f"{file_prefix}_{page_num}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                for img in visible_blob_imgs:
                    outer_html = img.get_attribute("outerHTML")
                    f.write(outer_html + "\n")
            print(f"ページ {page_num} のvisible_blob_imgsのHTMLを保存しました: {html_path}")

    except Exception as e:
        print(f"ページ{page_num}の画像取得失敗:", e)

def get_zip_and_delete_jpgs(zip_path, img_dir):
    # ZIP作成
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for jpg_file in glob.glob(os.path.join(img_dir, "*.jpg")):
            zipf.write(jpg_file, os.path.basename(jpg_file))
    # jpg削除（ZIP残す）
    try:
        for filename in os.listdir(img_dir):
            file_path = os.path.join(img_dir, filename)
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

def mangadex_chap_downloader_multi(options, upload_folder, base_url, max_wait_time, gen_zip=True):
    # 最初のドライバでページ情報取得
    driver = webdriver.Chrome(options=options)
    page_info = get_page_info(driver, base_url, max_wait_time)
    if not page_info:
        print("ページ情報取得できず終了")
        driver.quit()
        abort(400, description="ページ情報取得できず終了")
    driver.quit()

    file_prefix = f'{page_info["title"]}_{page_info["chapter"]}'
    img_dir = os.path.join(upload_folder, "images")
    os.makedirs(img_dir, exist_ok=True)
    zip_path = os.path.join(img_dir, f"{file_prefix}.zip")

    if gen_zip:
        if os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, mimetype='application/zip')

    max_workers = max(os.cpu_count() // 2, 1)
    total_pages = page_info["page"]
    pages_per_worker = (total_pages + max_workers - 1) // max_workers  # 切り上げ

    def worker_task(start_page, end_page):
        local_driver = webdriver.Chrome(options=options)
        results = []
        for page_num in range(start_page, end_page + 1):
            result = process_page(local_driver, max_wait_time, img_dir, upload_folder, page_num, base_url, file_prefix)
            results.append(result)
        local_driver.quit()
        return results

    # 並列実行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(max_workers):
            start = i * pages_per_worker + 1
            end = min((i + 1) * pages_per_worker, total_pages)
            if start > end:
                break
            futures.append(executor.submit(worker_task, start, end))

    print("並列ダウンロード処理終了")

    if gen_zip:
        return get_zip_and_delete_jpgs(zip_path, img_dir)

def mangadex_chap_downloader_single(driver, upload_folder, base_url, max_wait_time, gen_zip=True, driver_quit=True):
    page_info = get_page_info(driver, base_url, max_wait_time)
    if not page_info:
        print("ページ情報取得できず終了")
        if driver_quit:
            driver.quit()
        abort(400, description="ページ情報取得できず終了")
    
    file_prefix = f'{page_info["title"]}_{page_info["chapter"]}'        
    img_dir = os.path.join(upload_folder, "images")
    os.makedirs(img_dir, exist_ok=True)
    zip_path = os.path.join(img_dir, f"{file_prefix}.zip")

    if gen_zip:
        if os.path.exists(zip_path):
            if driver_quit:
                driver.quit()
            return send_file(zip_path, as_attachment=True, mimetype='application/zip')

    for page_num in range(1, page_info["page"] + 1):
        url = f"{base_url}/{page_num}"
        driver.get(url)

        try:
            wait_for_visible_blob_image(driver, max_wait_time)

            selector_text = "img[src^='blob:']"
            visible_blob_imgs = driver.find_elements(By.CSS_SELECTOR, selector_text)
            visible_blob_imgs = [
                img for img in visible_blob_imgs
                if "display:none" not in (img.get_attribute("style") or "").replace(" ", "").lower()
            ]

            if len(visible_blob_imgs) == 1:
                save_blob_image(driver, img_dir, visible_blob_imgs[0], file_prefix, page_num)
            else:
                print(f"ページ{page_num}: 表示されているblob画像が1個ではありません。{len(visible_blob_imgs)}個見つかりました。")
                html_dir = os.path.join(upload_folder, "htmls")
                os.makedirs(html_dir, exist_ok=True)
                html_path = os.path.join(html_dir, f"{file_prefix}_{page_num}.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    for img in visible_blob_imgs:
                        outer_html = img.get_attribute("outerHTML")
                        f.write(outer_html + "\n")
                print(f"ページ {page_num} のvisible_blob_imgsのHTMLを保存しました: {html_path}")

        except Exception as e:
            print(f"ページ{page_num}の画像取得失敗:", e)
            if driver_quit:
                driver.quit()
            abort(400, description=f"ページ{page_num}の画像取得失敗")

    if driver_quit:
        driver.quit()

    if gen_zip:
        return get_zip_and_delete_jpgs(zip_path, img_dir)