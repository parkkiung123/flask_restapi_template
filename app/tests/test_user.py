import os
import pytest
from flask_jwt_extended import create_access_token
from app.models.models import User
from app.extensions import db
from datetime import timedelta
from app import create_app
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_IMAGE_DIR = os.path.join(BASE_DIR, "tests", "assets")
TEST_IMAGE_NAME = "test_noface.jpg" # 画像ファイル名 test_face.jpg, test_noface.jpg
TEST_IMAGE_PATH = os.path.join(TEST_IMAGE_DIR, TEST_IMAGE_NAME)

@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    """DBにテスト用ユーザーを作成"""
    user = User(userid="testuser", name="unknown", userpass="hashedpassword123")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def access_token(test_user):
    """JWTトークンを生成（ユーザーIDで）"""    
    return create_access_token(
        identity=str(test_user.id),
        expires_delta=timedelta(minutes=1))

def test_user_list(client, app, test_user, access_token):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/user/list"

    response = client.get(url, headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert any(u["userid"] == "testuser" for u in json_data)

def test_add_user(client, app):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/user/add"

    # 画像ファイルを用意（空のpngファイル）
    with open(TEST_IMAGE_PATH, "rb") as f:
        dummy_image = io.BytesIO(f.read())

    data = {
        "userid": "newuser",
        "name": "New User",
        "userpass": "securepass123",
        "facephoto": (dummy_image, TEST_IMAGE_NAME)
    }

    response = client.post(
        url,
        data=data,
        content_type='multipart/form-data',
    )

    print(response.get_data(as_text=True))  # デバッグ用

    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data["userid"] == "newuser"
    assert json_data["name"] == "New User"
    if TEST_IMAGE_NAME == "test_noface.jpg":
        assert json_data["facephoto"] is None
    elif TEST_IMAGE_NAME == "test_face.jpg":
        assert json_data["facephoto"] is not None

    # DB上の確認
    user_in_db = User.query.filter_by(userid="newuser").first()
    assert user_in_db is not None
    assert user_in_db.name == "New User"
    if TEST_IMAGE_NAME == "test_noface.jpg":
        assert user_in_db.facephoto is None
    elif TEST_IMAGE_NAME == "test_face.jpg":
        assert user_in_db.facephoto is not None