import pytest
from flask_jwt_extended import create_access_token
from app.models.models import User
from app.extensions import db
from datetime import timedelta
from app import create_app

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
    user = User(userid="testuser", userpass="hashedpassword123")
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

def test_add_user(client, app, access_token):
    prefix = app.config.get("API_URL_PREFIX", "")
    url = f"{prefix}/user/add"

    new_user_data = {
        "userid": "newuser",
        "userpass": "securepass123"
    }

    response = client.post(url, json=new_user_data, headers={
        "Authorization": f"Bearer {access_token}",
    })

    print(response.get_data(as_text=True))  # デバッグ用

    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data["userid"] == new_user_data["userid"]

    # DB上でも確認
    user_in_db = User.query.filter_by(userid="newuser").first()
    assert user_in_db is not None
    assert user_in_db.userid == "newuser"