# seed.py
from app import create_app
from app.extensions import db
from app.models.models import User
import bcrypt

def seed_users():
    app = create_app()
    app.app_context().push()  # Flaskアプリコンテキストを有効化

    # すでにadminがいるかチェック
    if User.query.filter_by(userid="admin").first():
        print("adminユーザーはすでに存在します。")
        return

    # パスワードをハッシュ化
    hashed_pw = bcrypt.hashpw("adminpass".encode(), bcrypt.gensalt()).decode()

    # ユーザー作成
    admin = User(userid="admin", userpass=hashed_pw)

    db.session.add(admin)
    db.session.commit()
    print("✅ adminユーザーを作成しました。")

if __name__ == "__main__":
    seed_users()
