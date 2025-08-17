# -*- coding: utf-8 -*-

from flask import Flask, render_template
from flask_cors import CORS

from .config import AppConfig
from .database import init_db
from .routes.auth import auth_bp
from .routes.tasks import tasks_bp
from .routes.scheduled_tasks import scheduled_tasks_bp
from .routes.utils import utils_bp
from .routes.events import events_bp


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
    
    # 初始化DeepSeek AI服务
    if AppConfig.DEEPSEEK_ENABLED:
        try:
            from .services.deepseek_service import init_deepseek_service
            init_deepseek_service()
        except Exception as e:
            print(f"DeepSeek AI服务初始化失败: {e}")

    # 注册蓝图
    try:
        print("正在注册蓝图...")
        app.register_blueprint(auth_bp)
        print("✅ auth_bp 注册成功")
        
        app.register_blueprint(tasks_bp, url_prefix='/api')
        print("✅ tasks_bp 注册成功")
        
        app.register_blueprint(scheduled_tasks_bp, url_prefix='/api')
        print("✅ scheduled_tasks_bp 注册成功")
        
        app.register_blueprint(utils_bp, url_prefix='/api')
        print("✅ utils_bp 注册成功")
        
        app.register_blueprint(events_bp, url_prefix='/api')
        print("✅ events_bp 注册成功")
        
        print(f"蓝图注册完成，总共 {len(app.url_map._rules)} 个路由规则")
        
    except Exception as e:
        print(f"❌ 蓝图注册失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    # 首页
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # 事件管理页面
    @app.route('/events')
    def events():
        return render_template('events.html')

    return app
