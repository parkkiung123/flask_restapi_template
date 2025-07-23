import base64
import io
import cv2
import numpy as np
from flask import jsonify, send_file, abort, current_app
from flask.views import MethodView
from flask_smorest import Blueprint
from werkzeug.utils import secure_filename

from app.schemas.schemas import FileSchema, ImageBase64Schema
from app.works.imgproc import ImgProcessor
from app.routes.file_op import allowed_file

bp = Blueprint("image", __name__, description="画像処理API")

shared_img_processor = ImgProcessor()
allowed_extensions = {"jpg", "jpeg", "bmp", "png", "gif"}

# 処理種別マッピング
PROCESSORS = {
    "GrayScale": shared_img_processor.get_grayscale,
    "CropFace": shared_img_processor.get_face_crop
}

# multipart/form-data 用 schema 記述
req_body_schema = {
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "顔を含む画像ファイル"
                    }
                },
                "required": ["file"]
            }
        }
    }
}

# 画像処理を実行
def get_processed_frame(stream, class_name: str):
    idx = class_name.find("Image")
    base_name = class_name[:idx] if idx != -1 else class_name 
    processor = PROCESSORS.get(base_name)
    if not processor:
        abort(400, description="不明な処理です")
    return processor(stream)

# OpenCV画像をBase64に変換
def image_to_base64(image, ext="jpg"):
    success, buffer = cv2.imencode(f".{ext}", image)
    if not success:
        raise ValueError("画像のエンコードに失敗しました")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")

# base64をOpenCV画像に変換
def base64_to_image(image_base64: str):
    try:
        img_data = base64.b64decode(image_base64)
        np_arr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        current_app.logger.error(f"base64デコードエラー: {e}")
        return None

# ファイル or base64 による画像処理レスポンス
def process_image_response(image_input, class_name: str, is_base64=False):
    try:
        if is_base64:
            frame = base64_to_image(image_input)
            if frame is None:
                return {"message": "画像の読み込みに失敗しました"}, 400
            # メモリストリームに変換
            _, img_bytes = cv2.imencode(".jpg", frame)
            stream = io.BytesIO(img_bytes.tobytes())
        else:
            file = image_input
            if not allowed_file(file.filename, allowed_extensions):
                return {"message": "許可されていないファイル形式です"}, 400
            stream = file.stream

        # 処理実行
        result_frame = get_processed_frame(stream, class_name)
        if result_frame is None:
            return {"message": "画像処理に失敗しました"}, 400

        if is_base64:
            frame_b64 = image_to_base64(result_frame, "jpg")
            return jsonify({"image": frame_b64})
        else:
            ext = image_input.filename.rsplit(".", 1)[1].lower()
            ext = "jpg" if ext == "jpeg" else ext
            encode_ext = f".{ext}"

            success, buffer = cv2.imencode(encode_ext, result_frame)
            if not success:
                raise ValueError("画像のエンコードに失敗しました")
            img_io = io.BytesIO(buffer.tobytes())

            base_name = class_name.replace("Image", "").lower()
            filename = secure_filename(image_input.filename)
            name, _ = filename.rsplit(".", 1)
            new_filename = f"{name}_{base_name}.{ext}"

            return send_file(
                img_io,
                mimetype=f"image/{ext}",
                as_attachment=True,
                download_name=new_filename
            )
    except Exception as e:
        current_app.logger.error(f"画像処理エラー ({class_name}): {e}")
        return {"message": "画像処理中にエラーが発生しました"}, 500

# ========== API 定義 ==========

@bp.route("/gray")
class GrayScaleImage(MethodView):
    @bp.doc(description="アップロード画像をグレースケール変換", requestBody=req_body_schema)
    @bp.arguments(FileSchema, location="files")
    def post(self, data):
        return process_image_response(data["file"], self.__class__.__name__, is_base64=False)

@bp.route("/gray/base64")
class GrayScaleImageBase64(MethodView):
    @bp.doc(description="base64画像をグレースケール変換")
    @bp.arguments(ImageBase64Schema)
    def post(self, data):
        return process_image_response(data["image"], self.__class__.__name__, is_base64=True)

@bp.route("/cropFace")
class CropFaceImage(MethodView):
    @bp.doc(description="アップロード画像から顔を抽出", requestBody=req_body_schema)
    @bp.arguments(FileSchema, location="files")
    def post(self, data):
        return process_image_response(data["file"], self.__class__.__name__, is_base64=False)

@bp.route("/cropFace/base64")
class CropFaceImageBase64(MethodView):
    @bp.doc(description="base64画像から顔を抽出")
    @bp.arguments(ImageBase64Schema)
    def post(self, data):
        return process_image_response(data["image"], self.__class__.__name__, is_base64=True)
