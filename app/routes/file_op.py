# app/routes/file.py

import os
from flask.views import MethodView
from flask_smorest import Blueprint
from flask import current_app
from werkzeug.utils import secure_filename
from app.schemas.schemas import FileSchema  # ← スキーマを読み込み

bp = Blueprint("file", __name__, url_prefix="/file", description="ファイル操作")

def allowed_file(filename, extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions

def save_file(file, subfolder, allowed_extensions):
    if file.filename == '':
        return {"message": "ファイルが選択されていません"}, 400

    if not allowed_file(file.filename, allowed_extensions):
        return {"message": "許可されていないファイル形式です"}, 400

    filename = secure_filename(file.filename)
    upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return {"message": "アップロード成功", "filename": filename}, 201

# テキストファイル用エンドポイント
@bp.route("/text")
class TextUpload(MethodView):
    @bp.doc(
        description="テキストファイルをアップロードします（'txt', 'csv', 'json'）",
        requestBody={
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "アップロードするファイル"
                            }
                        },
                        "required": ["file"]
                    }
                }
            }
        }
    )
    @bp.arguments(FileSchema, location="files")
    def post(self, data):
        file = data["file"]
        allowed = {"txt", "csv", "json"}
        return save_file(file, "text", allowed)

# 画像ファイル用エンドポイント
@bp.route("/image")
class ImageUpload(MethodView):
    @bp.doc(
        description="画像ファイルをアップロードします（'jpg', 'bmp', 'png', 'gif'）",
        requestBody={
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "アップロードするファイル"
                            }
                        },
                        "required": ["file"]
                    }
                }
            }
        }
    )
    @bp.arguments(FileSchema, location="files")
    def post(self, data):
        file = data["file"]
        allowed = {"jpg", "bmp", "png", "gif"}
        return save_file(file, "image", allowed)
