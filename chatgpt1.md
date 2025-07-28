素晴らしい目的です！
以下に、\*\*Flask + Flask-Smorest + SQLAlchemy + JWT + Marshmallow構成でのREST APIテンプレート（ボイラープレート）\*\*を一から組み立てる方法を紹介します。

---

## ✅ ゴール：REST API テンプレート構成（自作）

構成は以下のようになります：

```
flask-rest-api-template/
├── app/
│   ├── __init__.py         # create_app()定義
│   ├── config.py           # 環境設定
│   ├── extensions.py       # db, jwt, api など
│   ├── models/
│   │   └── user.py         # Userモデル
│   ├── routes/
│   │   └── user.py         # Userルート（Blueprint）
│   ├── controllers/
│   │   └── user_controller.py # ロジック
│   └── schemas/
│       └── user_schema.py  # marshmallowスキーマ
├── migrations/             # Alembic用
├── .env                    # 環境変数（JWTキーなど）
├── requirements.txt        # 必要パッケージ
├── run.py                  # 実行エントリポイント
└── README.md
```

---

## ✅ 手順で構築する

---

### ① 必要パッケージのインストール

```bash
pip install flask flask-smorest flask-sqlalchemy flask-migrate flask-jwt-extended marshmallow webargs python-dotenv
```

---

### ② `run.py`（起動スクリプト）

```python
# run.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
```

---

### ③ `app/__init__.py`（アプリ生成）

```python
from flask import Flask
from app.extensions import db, migrate, jwt, api
from app.routes.user import bp as user_bp
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    api.init_app(app)

    api.register_blueprint(user_bp, url_prefix="/api/users")

    return app
```

---

### ④ `app/extensions.py`（Flask拡張まとめ）

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_smorest import Api

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
api = Api()
```

---

### ⑤ `app/config.py`（設定）

```python
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///data.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    API_TITLE = "REST API Template"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
```

---

### ⑥ `app/models/user.py`（SQLAlchemyモデル）

```python
from app.extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
```

---

### ⑦ `app/schemas/user_schema.py`（marshmallowスキーマ）

```python
from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
```

---

### ⑧ `app/controllers/user_controller.py`（ビジネスロジック）

```python
from app.models.user import User
from app.extensions import db

class UserController:
    @staticmethod
    def get_all():
        return User.query.all()

    @staticmethod
    def create(data):
        user = User(**data)
        db.session.add(user)
        db.session.commit()
        return user
```

---

### ⑨ `app/routes/user.py`（エンドポイント定義）

```python
from flask_smorest import Blueprint
from flask.views import MethodView
from app.controllers.user_controller import UserController
from app.schemas.user_schema import UserSchema

bp = Blueprint("users", __name__, description="User APIs")

@bp.route("/")
class UserList(MethodView):
    @bp.response(200, UserSchema(many=True))
    def get(self):
        return UserController.get_all()

    @bp.arguments(UserSchema)
    @bp.response(201, UserSchema)
    def post(self, data):
        return UserController.create(data)
```

---

### ⑩ `.env`（環境変数）

```env
JWT_SECRET_KEY=your_very_secret_key
DATABASE_URI=sqlite:///data.db
```

---

### ⑪ `requirements.txt`

```txt
flask
flask-smorest
flask-sqlalchemy
flask-migrate
flask-jwt-extended
marshmallow
webargs
python-dotenv
```

---

### ⑫ 初期化コマンド（初回だけ）

```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

---

## ✅ 完成後の確認

* `python run.py` で起動
* `http://localhost:5000/docs` にアクセス → Swagger UI が表示
* `/api/users/` に `GET`, `POST` リクエストが可能

---

## 🧩 拡張していくなら…

* 認証（ログイン/ユーザー登録）
* エラーハンドリング共通化
* モジュール分離（auth, tasks など）
* Docker対応
* CI/CD対応

---

## 📦 テンプレートが欲しければ

この構成を GitHub にテンプレートとして上げた形にしても提供できます。
もし「リポジトリ形式で欲しい」「FastAPI 版も見てみたい」など要望があれば気軽に言ってください！
