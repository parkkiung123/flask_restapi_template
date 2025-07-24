import base64
import io
import os

# grpc_serverの起動が必要

service_name = "image"

def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_gray_file_upload(client, api_prefix, test_image_path):
    url = f"{api_prefix}/{service_name}/gray"
    filename = os.path.basename(test_image_path)
    with open(test_image_path, "rb") as f:
        data = {
            "file": (io.BytesIO(f.read()), filename)
        }
        response = client.post(url, content_type="multipart/form-data", data=data)

    assert response.status_code == 200
    assert response.mimetype.startswith("image/")
    content_disp = response.headers.get("Content-Disposition", "")
    assert "_Gray." in content_disp

def test_gray_base64(client, api_prefix, test_image_path):
    url = f"{api_prefix}/{service_name}/gray/base64"

    image_b64 = load_image_base64(test_image_path)
    response = client.post(url, json={"image": image_b64})

    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert "image" in data
    assert isinstance(data["image"], str)

def test_crop_face_file_upload(client, api_prefix, test_image_path):
    url = f"{api_prefix}/{service_name}/cropFace"
    filename = os.path.basename(test_image_path)
    with open(test_image_path, "rb") as f:
        data = {
            "file": (io.BytesIO(f.read()), filename)
        }
        response = client.post(url, content_type="multipart/form-data", data=data)

    assert response.status_code in (200, 400)
    if response.status_code == 200:
        assert response.mimetype.startswith("image/")

def test_crop_face_base64(client, api_prefix, test_image_path):
    url = f"{api_prefix}/{service_name}/cropFace/base64"

    image_b64 = load_image_base64(test_image_path)
    response = client.post(url, json={"image": image_b64})

    assert response.status_code in (200, 400)
    if response.status_code == 200:
        data = response.get_json()
        assert data is not None
        assert "image" in data
        assert isinstance(data["image"], str)

def test_invalid_file_type(client, api_prefix):
    url = f"{api_prefix}/{service_name}/gray"
    data = {
        "file": (io.BytesIO(b"not an image"), "test.txt")
    }
    response = client.post(url, content_type="multipart/form-data", data=data)

    assert response.status_code == 400
    json_data = response.get_json()
    assert "許可されていないファイル形式" in json_data.get("message", "")

def test_invalid_base64(client, api_prefix):
    url = f"{api_prefix}/{service_name}/gray/base64"
    response = client.post(url, json={"image": "not_base64_data"})

    assert response.status_code in (400, 500)
