import base64
import io
import os
import pytest
from app import create_app

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_IMAGE_DIR = os.path.join(BASE_DIR, "tests", "assets")
TEST_IMAGE_NAME = "test_noface.jpg" # 画像ファイル名 test_face.jpg, test_noface.jpg
TEST_IMAGE_PATH = os.path.join(TEST_IMAGE_DIR, TEST_IMAGE_NAME)

@pytest.fixture
def app():
    app = create_app(testing=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_gray_file_upload(client, app):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/image/gray"
    with open(TEST_IMAGE_PATH, "rb") as f:
        data = {
            "file": (io.BytesIO(f.read()), TEST_IMAGE_NAME)
        }
        response = client.post(url, content_type="multipart/form-data", data=data)

    assert response.status_code == 200
    assert response.mimetype.startswith("image/")
    content_disp = response.headers.get("Content-Disposition", "")
    assert "_gray." in content_disp or "_grayscale." in content_disp

def test_gray_base64(client, app):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/image/gray/base64"

    image_b64 = load_image_base64(TEST_IMAGE_PATH)
    response = client.post(url, json={"image": image_b64})

    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert "image" in data
    assert isinstance(data["image"], str)

def test_crop_face_file_upload(client, app):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/image/cropFace"
    with open(TEST_IMAGE_PATH, "rb") as f:
        data = {
            "file": (io.BytesIO(f.read()), TEST_IMAGE_NAME)
        }
        response = client.post(url, content_type="multipart/form-data", data=data)

    # 顔抽出は失敗することもあるので200 or 400許容
    assert response.status_code in (200, 400)
    if response.status_code == 200:
        assert response.mimetype.startswith("image/")

def test_crop_face_base64(client, app):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/image/cropFace/base64"

    image_b64 = load_image_base64(TEST_IMAGE_PATH)
    response = client.post(url, json={"image": image_b64})

    assert response.status_code in (200, 400)
    if response.status_code == 200:
        data = response.get_json()
        assert data is not None
        assert "image" in data
        assert isinstance(data["image"], str)

def test_invalid_file_type(client, app):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/image/gray"
    data = {
        "file": (io.BytesIO(b"not an image"), "test.txt")
    }
    response = client.post(url, content_type="multipart/form-data", data=data)

    assert response.status_code == 400
    json_data = response.get_json()
    assert "許可されていないファイル形式" in json_data.get("message", "")

def test_invalid_base64(client, app):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/image/gray/base64"
    response = client.post(url, json={"image": "not_base64_data"})

    assert response.status_code in (400, 500)
