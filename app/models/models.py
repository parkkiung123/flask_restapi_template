# app/models/user.py
from app.extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(100), unique=True, nullable=False)
    userpass = db.Column(db.String(100), nullable=False)  # ハッシュ済みパスワードを保存
