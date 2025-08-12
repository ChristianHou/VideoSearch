# -*- coding: utf-8 -*-

from flask import Flask, render_template
from flask_cors import CORS

from .config import AppConfig
from .database import init_db
from .routes.auth import auth_bp
from .routes.tasks import tasks_bp
from .routes.scheduled_tasks import scheduled_tasks_bp
from .routes.utils import utils_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(AppConfig)

    # CORS
    CORS(app)

    # 初始化数据库
    with app.app_context():
        init_db()

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp, url_prefix='/api')
    app.register_blueprint(scheduled_tasks_bp, url_prefix='/api')
    app.register_blueprint(utils_bp, url_prefix='/api')

    # 首页
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
