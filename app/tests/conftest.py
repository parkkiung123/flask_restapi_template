import os
import pytest
from app import create_app, db
from flask_jwt_extended import create_access_token
from datetime import timedelta
from app.models.models import User

# ベースディレクトリ（tests/ の親 = プロジェクトルート）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_IMAGE_DIR = os.path.join(BASE_DIR, "tests", "assets")
TEST_IMAGE_NAME = "test_noface.jpg"

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
def api_prefix(app):
    return app.config.get("API_URL_PREFIX", "")

@pytest.fixture
def test_image_path():
    return os.path.join(TEST_IMAGE_DIR, TEST_IMAGE_NAME)

@pytest.fixture
def test_user():
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