import os
import tempfile
import pytest
from app import create_app, db
from flask_jwt_extended import create_access_token
from datetime import timedelta
from app.models.models import User
import bcrypt

# ベースディレクトリ（tests/ の親 = プロジェクトルート）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_IMAGE_DIR = os.path.join(BASE_DIR, "tests", "assets")
TEST_IMAGE_NAME = "test_noface.jpg"

@pytest.fixture
def app():
    app = create_app(testing=True)
    
    # テスト時に一時アップロードフォルダを使用
    tmpdir = tempfile.TemporaryDirectory()
    app.config["UPLOAD_FOLDER"] = tmpdir.name

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        tmpdir.cleanup()

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
    """テスト用ユーザーを作成"""
    password = bcrypt.hashpw("testpass".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(userid="testuser", name="testname", userpass=password)
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def access_token(test_user):
    """JWTトークンを生成（ユーザーIDで）"""    
    return create_access_token(
        identity=str(test_user.id),
        expires_delta=timedelta(minutes=1))

@pytest.fixture
def upload_folder(tmp_path, app):
    """UPLOAD_FOLDERを一時ディレクトリに設定"""
    app.config["UPLOAD_FOLDER"] = tmp_path
    return tmp_path