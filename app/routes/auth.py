# app/routes/auth.py
from flask_smorest import Blueprint
from flask.views import MethodView
from app.schemas.schemas import LoginSchema
from app.models.models import User
from flask_jwt_extended import create_access_token
from datetime import timedelta
import bcrypt

bp = Blueprint("auth", __name__, description="認証ルート")

@bp.route("/login")
class Login(MethodView):
    @bp.arguments(LoginSchema)
    @bp.response(200)
    def post(self, data):
        userid = data["userid"]
        userpass = data["userpass"]

        user = User.query.filter_by(userid=userid).first()
        if user is None:
            return {"message": "ユーザーが存在しません"}, 401

        if not bcrypt.checkpw(userpass.encode("utf-8"), user.userpass.encode("utf-8")):
            return {"message": "パスワードが正しくありません"}, 401

        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1),
        )
        return {"access_token": access_token}, 200
