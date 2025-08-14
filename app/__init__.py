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

    # 初始化飞书服务
    if AppConfig.FEISHU_ENABLED:
        try:
            from .services.feishu_service import init_feishu_service
            init_feishu_service(
                app_id=AppConfig.FEISHU_APP_ID,
                app_secret=AppConfig.FEISHU_APP_SECRET,
                chat_id=AppConfig.FEISHU_CHAT_ID
            )
        except Exception as e:
            print(f"飞书服务初始化失败: {e}")

    # 初始化翻译服务
    if AppConfig.VOLC_ENABLED:
        try:
            from .services.translate_service import init_translate_service
            init_translate_service()
        except Exception as e:
            print(f"翻译服务初始化失败: {e}")

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
