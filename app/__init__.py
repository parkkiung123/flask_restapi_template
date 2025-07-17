import logging
from flask import Flask
from app.extensions import db, migrate, jwt, api, cors
from app.routes.user import bp as user_bp
from app.routes.auth import bp as auth_bp
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    api.init_app(app)
    cors.init_app(app, origins=["http://localhost:5173"])

    url_prefix = app.config["API_URL_PREFIX"]
    api.register_blueprint(user_bp, url_prefix=f"{url_prefix}/user")
    api.register_blueprint(auth_bp, url_prefix=f"{url_prefix}/auth")

    # ログレベルとフォーマットを調整
    app.logger.setLevel(logging.INFO)
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        app.logger.addHandler(handler)

    return app
