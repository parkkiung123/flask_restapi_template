from flask_jwt_extended import decode_token

service_name = "auth"

def test_login_success(client, api_prefix, test_user):
    url = f"{api_prefix}/{service_name}/login"
    response = client.post(url, json={
        "userid": "testuser",
        "userpass": "testpass"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data

    # アクセストークンのデコード確認（オプション）
    decoded = decode_token(data["access_token"])
    assert decoded["sub"] == str(test_user.id)

def test_login_wrong_password(client, api_prefix, test_user):
    url = f"{api_prefix}/{service_name}/login"
    response = client.post(url, json={
        "userid": "testuser",
        "userpass": "wrongpass"
    })
    assert response.status_code == 401
    assert response.get_json()["message"] == "パスワードが正しくありません"

def test_login_nonexistent_user(client, api_prefix):
    url = f"{api_prefix}/{service_name}/login"
    response = client.post(url, json={
        "userid": "nonexistent",
        "userpass": "any"
    })
    assert response.status_code == 401
    assert response.get_json()["message"] == "ユーザーが存在しません"
