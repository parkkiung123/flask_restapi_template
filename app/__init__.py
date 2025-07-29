import logging
from flask import Flask
from app.extensions import db, migrate, jwt, api, cors
from app.routes.user import bp as user_bp
from app.routes.auth import bp as auth_bp
from app.routes.sensor import bp as sensor_bp
from app.routes.file_op import bp as file_bp
from app.routes.image import bp as img_proc_bp
from app.config import Config, TestConfig

def create_app(testing=False):
    app = Flask(__name__)
    if testing:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)  

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    api.init_app(app)
    cors.init_app(app, origins=["http://localhost:8080", "http://localhost:8081"])

    url_prefix = app.config["API_URL_PREFIX"]
    api.register_blueprint(user_bp, url_prefix=f"{url_prefix}/user")
    api.register_blueprint(auth_bp, url_prefix=f"{url_prefix}/auth")
    api.register_blueprint(sensor_bp, url_prefix=f"{url_prefix}/sensor")
    api.register_blueprint(file_bp, url_prefix=f"{url_prefix}/file")
    api.register_blueprint(img_proc_bp, url_prefix=f"{url_prefix}/image")

    # ログレベルとフォーマットを調整
    app.logger.setLevel(logging.INFO)
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        app.logger.addHandler(handler)

    # # HTTPS設定
    # if not app.debug:  # デバッグモードではhttpsにしない
    #     app.run(ssl_context=('server.crt', 'server.key'))

    return app
