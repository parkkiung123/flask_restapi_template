import cv2
from flask import current_app, request
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.routes.image import shared_img_processor
from app.schemas.schemas import UserListResScheme, UserSchema
from app.models.models import User
from app.extensions import db
import io
import bcrypt

bp = Blueprint("user", __name__, description="ユーザーAPI")

@bp.route("/list")
class UserList(MethodView):
    # クラス全体を保護したい
    # decorators = [jwt_required()]    
    # 保護されたルート
    @jwt_required()
    @bp.response(200, UserListResScheme(many=True))
    def get(self):
        """保護されたルート（JWT 必須）"""
        user_id = get_jwt_identity()
        current_app.logger.info(f"アクセス中のユーザーID: {user_id}")
        return User.query.all()

@bp.route("/add")
class UserAdd(MethodView):
    @bp.arguments(UserSchema, location="form")  # JSONではなくフォームのデータを取得
    @bp.response(201, UserSchema)
    def post(self, data):
        # パスワードハッシュ化
        hashed_pw = bcrypt.hashpw(data["userpass"].encode("utf-8"), bcrypt.gensalt())
        data["userpass"] = hashed_pw.decode("utf-8")

        # ファイルは request.files から取り出す
        file = request.files.get('facephoto')
        if file:
            photo_arr = shared_img_processor.get_face_crop(file.stream)
            if photo_arr is None:
                photo_data = None
            success, encoded_image = cv2.imencode('.png', photo_arr)
            if not success:
                raise ValueError("画像のエンコードに失敗しました")
            else:
                photo_data = encoded_image
        else:
            photo_data = None

        user = User(**data, facephoto=photo_data)
        db.session.add(user)
        db.session.commit()
        return user