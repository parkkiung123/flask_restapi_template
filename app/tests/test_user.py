import os
from app.models.models import User
from app.extensions import db
import io

def test_user_list(client, api_prefix, access_token):
    url = f"{api_prefix}/user/list"

    response = client.get(url, headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert any(u["userid"] == "testuser" for u in json_data)

def test_add_user(client, api_prefix, test_image_path):
    url = f"{api_prefix}/user/add"
    test_image_name = os.path.basename(test_image_path)

    with open(test_image_path, "rb") as f:
        test_image_bytes = io.BytesIO(f.read())

    data = {
        "userid": "newuser",
        "name": "New User",
        "userpass": "securepass123",
        "facephoto": (test_image_bytes, test_image_name)
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
    if test_image_name == "test_noface.jpg":
        assert json_data["facephoto"] is None
    elif test_image_name == "test_face.jpg":
        assert json_data["facephoto"] is not None

    # DB上の確認
    user_in_db = User.query.filter_by(userid="newuser").first()
    assert user_in_db is not None
    assert user_in_db.name == "New User"
    if test_image_name == "test_noface.jpg":
        assert user_in_db.facephoto is b""
    elif test_image_name == "test_face.jpg":
        assert user_in_db.facephoto is not None