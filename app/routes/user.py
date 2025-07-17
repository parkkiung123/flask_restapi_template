from flask import current_app
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas.schemas import UserSchema
from app.models.models import User
from app.extensions import db
import bcrypt

bp = Blueprint("user", __name__, description="ユーザーAPI")

@bp.route("")
class UserList(MethodView):
    # クラス全体を保護したい
    # decorators = [jwt_required()]
    
    # 保護されたルート
    @jwt_required()
    @bp.response(200, UserSchema(many=True))
    def get(self):
        user_id = get_jwt_identity()
        current_app.logger.info(f"アクセス中のユーザーID: {user_id}")
        return User.query.all()

    @bp.arguments(UserSchema)
    @bp.response(201, UserSchema)
    def post(self, data):
        # パスワードをハッシュ化
        hashed_pw = bcrypt.hashpw(data["userpass"].encode("utf-8"), bcrypt.gensalt())
        data["userpass"] = hashed_pw.decode("utf-8")  # デコードして文字列として保存
        user = User(**data)
        db.session.add(user)
        db.session.commit()
        return user
