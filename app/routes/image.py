import base64
import io
from flask import jsonify, send_file, abort
from flask.views import MethodView
from flask_smorest import Blueprint
from werkzeug.utils import secure_filename
from app.schemas.schemas import File2Schema, FileSchema, ImageBase64Schema
from app.routes.file_op import allowed_file
import grpc
from app.grpc_server import image_pb2, image_pb2_grpc

bp = Blueprint("image", __name__, description="画像処理API")
allowed_extensions = {"jpg", "jpeg", "bmp", "png", "gif"}

channel = grpc.insecure_channel("localhost:50051")
stub = image_pb2_grpc.ImageProcessorStub(channel)
def grpc_request_image(route, image_bytes):
    req = image_pb2.ImageRequest(image=image_bytes)
    return getattr(stub, route)(req)

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def extract_base_name(class_name):
    idx = class_name.find("Image")
    return class_name[:idx] if idx != -1 else class_name

def get_new_filename(original_name, class_name, ext=None):
    base_name = extract_base_name(class_name)
    name, orig_ext = original_name.rsplit('.', 1)
    return f"{secure_filename(name)}_{base_name}.{ext or orig_ext.lower()}"

def process_image_response(image_input, class_name, is_base64=False):
    if is_base64:
        try:
            image_bytes = base64.b64decode(image_input)
        except Exception:
            abort(400, description="base64のデコードに失敗しました")
    else:
        if not allowed_file(image_input.filename):
            return {"message": "許可されていないファイル形式です"}, 400
        image_bytes = image_input.read()
        filename = image_input.filename

    # 処理種別を class_name から決定
    method = f"Get{extract_base_name(class_name)}"
    try:
        res = grpc_request_image(method, image_bytes)
    except grpc.RpcError as e:
        abort(400, description=e.details())

    if is_base64:
        encoded = base64.b64encode(res.image).decode('utf-8')
        return jsonify({"image": encoded})
    else:
        new_filename = get_new_filename(filename, class_name, ext="jpg")
        return send_file(io.BytesIO(res.image), mimetype='image/jpeg', as_attachment=True, download_name=new_filename)

@bp.route("/gray")
class GrayImage(MethodView):
    @bp.doc(description="アップロード画像をグレースケール変換", requestBody=req_body_schema)
    @bp.arguments(FileSchema, location="files")
    def post(self, data):
        return process_image_response(data["file"], self.__class__.__name__)

@bp.route("/gray/base64")
class GrayImageBase64(MethodView):
    @bp.doc(description="base64画像をグレースケール変換")
    @bp.arguments(ImageBase64Schema)
    def post(self, data):
        return process_image_response(data["image"], self.__class__.__name__, is_base64=True)

@bp.route("/cropFace")
class CropFaceImage(MethodView):
    @bp.doc(description="アップロード画像から顔を抽出", requestBody=req_body_schema)
    @bp.arguments(FileSchema, location="files")
    def post(self, data):
        return process_image_response(data["file"], self.__class__.__name__)

@bp.route("/cropFace/base64")
class CropFaceImageBase64(MethodView):
    @bp.doc(description="base64画像から顔を抽出")
    @bp.arguments(ImageBase64Schema)
    def post(self, data):
        return process_image_response(data["image"], self.__class__.__name__, is_base64=True)

@bp.route("/similarity")
class FaceSimilarityImage(MethodView):
    @bp.doc(description="2つのアップロード画像の顔類似度を計算", requestBody={
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "file": {
                            "type": "string",
                            "format": "binary",
                            "description": "最初の画像ファイル"
                        },
                        "file2": {
                            "type": "string",
                            "format": "binary",
                            "description": "比較対象の画像ファイル"
                        }
                    },
                    "required": ["file", "file2"]
                }
            }
        }
    })
    @bp.arguments(File2Schema, location="files")
    def post(self, data):
        f1 = data["file"].read()
        f2 = data["file2"].read()
        req = image_pb2.FaceSimilarityRequest(image1=f1, image2=f2)
        try:
            res = stub.GetFaceSimilarity(req)
        except grpc.RpcError as e:
            abort(400, description=e.details())
        return jsonify({"similarity": res.similarity})
