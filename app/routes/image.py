import base64
import io
import cv2
from flask import jsonify, send_file, abort, current_app
from flask.views import MethodView
from flask_smorest import Blueprint
import numpy as np
from werkzeug.utils import secure_filename
from app.schemas.schemas import FileSchema, ImageBase64Schema
from app.works.imgproc import ImgProcessor
from app.routes.file_op import allowed_file

bp = Blueprint("image", __name__, description="画像処理API")

shared_img_processor = ImgProcessor()
allowed = {"jpg", "jpeg", "bmp", "png", "gif"}
reqBody = {
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

def get_processed_frame(stream, class_name):
    idx = class_name.find("Image")
    base_name = class_name[:idx] if idx != -1 else class_name  # "CropFace"
    if base_name == "GrayScale":
        frame = shared_img_processor.get_grayscale(stream)
    elif base_name == "CropFace":
        frame = shared_img_processor.get_face_crop(stream)
    else:
        abort(400, description="不明な処理です")
    return frame

def file2res(file, class_name):
    if not allowed_file(file.filename, allowed):
        return {"message": "許可されていないファイル形式です"}, 400
    try:
        frame = get_processed_frame(file.stream, class_name)

        # ファイル拡張子取得とフォーマット決定
        ext = file.filename.rsplit(".", 1)[1].lower()
        ext = "jpg" if ext == "jpeg" else ext  # OpenCVはjpegではなくjpgを使う
        encode_ext = f".{ext}"

        # OpenCVで画像をエンコード
        success, buffer = cv2.imencode(encode_ext, frame)
        if not success:
            raise ValueError("画像のエンコードに失敗しました")

        img_io = io.BytesIO(buffer.tobytes())

        # 新しいファイル名
        filename = secure_filename(file.filename)
        name, _ = filename.rsplit(".", 1)
        if class_name == "GrayScaleImage":
            new_filename = f"{name}_gray.{ext}"
        elif class_name == "CropFaceImage":
            new_filename = f"{name}_crop.{ext}"

        return send_file(
            img_io,
            mimetype=f"image/{ext}",
            as_attachment=True,
            download_name=new_filename
        )
    except Exception as e:
        current_app.logger.error(f"画像処理エラー: {e}")
        return {"message": "画像処理中にエラーが発生しました"}, 500
    
def base64_to_image(image_base64: str):
    try:
        img_data = base64.b64decode(image_base64)
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        current_app.logger.error(f"base64デコードエラー: {e}")
        return None

def image_to_base64(image, ext="jpg"):
    success, buffer = cv2.imencode(f".{ext}", image)
    if not success:
        raise ValueError("画像のエンコードに失敗しました")
    img_bytes = buffer.tobytes()
    return base64.b64encode(img_bytes).decode("utf-8")
    
def base64ToRes(image_b64, class_name):
    try:
        frame = base64_to_image(image_b64)
        if frame is None:
            return {"message": "画像の読み込みに失敗しました"}, 400

        # streamの代わりにメモリバイナリとして渡す
        img_bytes = cv2.imencode(".jpg", frame)[1].tobytes()
        img_stream = io.BytesIO(img_bytes)

        frame = get_processed_frame(img_stream, class_name)

        if frame is None:
            return {"message": "顔が検出されませんでした"}, 400

        frame_b64 = image_to_base64(frame, "jpg")
        return jsonify({"image": frame_b64})
    except Exception as e:
        current_app.logger.error(f"base64画像処理エラー: {e}")
        return {"message": "画像処理中にエラーが発生しました"}, 500

@bp.route("/gray")
class GrayScaleImage(MethodView):
    @bp.doc(
        description="画像をアップロードしてグレースケール変換を行い、変換後の画像を返します",
        requestBody=reqBody
    )
    @bp.arguments(FileSchema, location="files")
    def post(self, data):
        file = data["file"]
        return file2res(file, self.__class__.__name__)

@bp.route("/gray/base64")
class GrayScaleImageBase64(MethodView):
    @bp.doc(description="base64形式の画像を受け取りグレースケール変換したbase64画像を返します")
    @bp.arguments(ImageBase64Schema)
    def post(self, data):
        return base64ToRes(data["image"], self.__class__.__name__)

@bp.route("/cropFace")
class CropFaceImage(MethodView):
    @bp.doc(
        description="画像をアップロードして顔検出を行い、顔部分だけを切り抜いた画像を返します",
        requestBody=reqBody
    )
    @bp.arguments(FileSchema, location="files")
    def post(self, data):
        file = data["file"]
        return file2res(file, self.__class__.__name__)
    
@bp.route("/cropFace/base64")
class CropFaceImageBase64(MethodView):
    @bp.doc(description="base64形式の画像を受け取り顔を切り抜いたbase64画像を返します")
    @bp.arguments(ImageBase64Schema)
    def post(self, data):
        return base64ToRes(data["image"], self.__class__.__name__)

