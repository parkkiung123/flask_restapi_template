from flask import abort, current_app, request
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas.schemas import UserListResScheme, UserSchema
from app.models.models import User
from app.extensions import db
import grpc
import bcrypt
from app.routes.image import grpc_request_image

bp = Blueprint("user", __name__, description="ユーザーAPI")

def hash_password(plain_password: str) -> str:
    """パスワードをハッシュ化する"""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def process_face_photo(file):
    """顔写真ファイルを gRPC 経由で送信して結果を取得"""
    if not file:
        return None
    try:
        image_bytes = file.read()
        res = grpc_request_image("GetCropFace", image_bytes)
        return res.image if res and res.image else None
    except grpc.RpcError as e:
        abort(400, description=f"画像処理エラー: {e.details()}")

@bp.route("/list")
class UserList(MethodView):
    @jwt_required()
    @bp.doc(description="JWT が必要なユーザー一覧取得エンドポイント")
    @bp.response(200, UserListResScheme(many=True))
    def get(self):
        user_id = get_jwt_identity()
        current_app.logger.info(f"[UserList] アクセス中のユーザーID: {user_id}")
        return User.query.all()

@bp.route("/add")
class UserAdd(MethodView):
    @bp.doc(description="フォームからユーザー情報を受け取り、新規ユーザーを追加")
    @bp.arguments(UserSchema, location="form")  # フォーム送信
    @bp.response(201, UserSchema)
    def post(self, data):
        current_app.logger.debug(f"[UserAdd] 受信データ: {data}")

        # パスワードをハッシュ化
        data["userpass"] = hash_password(data["userpass"])

        # 顔写真処理
        file = request.files.get('facephoto')
        facephoto = process_face_photo(file)

        # ユーザー作成とDB保存
        user = User(**data, facephoto=facephoto)
        db.session.add(user)
        db.session.commit()

        current_app.logger.info(f"[UserAdd] ユーザー {user.userid} を追加しました")
        return user
