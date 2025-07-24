import io
from PIL import Image

service_name = "file"

def create_test_image_bytes():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_upload_text_file(client, upload_folder, api_prefix):
    url = f"{api_prefix}/{service_name}/text"
    data = {
        "file": (io.BytesIO(b"sample text content"), "example.txt")
    }
    response = client.post(url, content_type="multipart/form-data", data=data)

    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["message"] == "アップロード成功"
    assert res_json["filename"] == "example.txt"

    saved_file = upload_folder / "text" / "example.txt"
    assert saved_file.exists()
    assert saved_file.read_text() == "sample text content"

def test_upload_disallowed_text_file(client, api_prefix):
    url = f"{api_prefix}/{service_name}/text"
    data = {
        "file": (io.BytesIO(b"wrong extension"), "example.exe")
    }
    response = client.post(url, content_type="multipart/form-data", data=data)

    assert response.status_code == 400
    assert response.get_json()["message"] == "許可されていないファイル形式です"

def test_upload_empty_file_text(client, api_prefix):
    url = f"{api_prefix}/{service_name}/text"
    data = {
        "file": (io.BytesIO(b""), "")
    }
    response = client.post(url, content_type="multipart/form-data", data=data)

    assert response.status_code == 400
    assert response.get_json()["message"] == "ファイルが選択されていません"

def test_upload_valid_image_file(client, upload_folder, api_prefix):
    url = f"{api_prefix}/{service_name}/image"

    image_bytes = create_test_image_bytes()
    data = {
        "file": (io.BytesIO(image_bytes), "valid_image.png")
    }

    response = client.post(url, content_type="multipart/form-data", data=data)
    assert response.status_code == 201

    res_json = response.get_json()
    assert res_json["message"] == "アップロード成功"
    assert res_json["filename"] == "valid_image.png"

    saved_file = upload_folder / "image" / "valid_image.png"
    assert saved_file.exists()

def test_upload_invalid_image_file(client, upload_folder, api_prefix):
    url = f"{api_prefix}/{service_name}/image"

    # 画像ではないバイナリを画像ファイル名でアップロード
    fake_image_bytes = b"this is not a real image file"
    data = {
        "file": (io.BytesIO(fake_image_bytes), "fake_image.png")
    }

    response = client.post(url, content_type="multipart/form-data", data=data)
    assert response.status_code == 400

    res_json = response.get_json()
    assert res_json["message"] == "無効な画像ファイルです"

    saved_file = upload_folder / "image" / "fake_image.png"
    assert not saved_file.exists()  # ファイルは保存されていないはず

def test_upload_disallowed_extension(client, api_prefix):
    url = f"{api_prefix}/{service_name}/image"

    data = {
        "file": (io.BytesIO(b"dummy content"), "image.txt")  # 拡張子が許可されていない
    }

    response = client.post(url, content_type="multipart/form-data", data=data)
    assert response.status_code == 400
    assert response.get_json()["message"] == "許可されていないファイル形式です"

def test_upload_empty_file_image(client, api_prefix):
    url = f"{api_prefix}/{service_name}/image"

    data = {
        "file": (io.BytesIO(b""), "")  # ファイル名空
    }

    response = client.post(url, content_type="multipart/form-data", data=data)
    assert response.status_code == 400
    assert response.get_json()["message"] == "ファイルが選択されていません"