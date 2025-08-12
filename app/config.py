# -*- coding: utf-8 -*-

import os


class AppConfig:
    SECRET_KEY = os.environ.get('APP_SECRET_KEY', 'your-secret-key-here-change-in-production')

    # OAuth/YouTube配置
    GOOGLE_CLIENT_SECRETS_FILE = os.environ.get(
        'GOOGLE_CLIENT_SECRETS_FILE',
        './config/client_secret_266922945282-56si2sbprgovgrltnighba3u5av9a56n.apps.googleusercontent.com.json'
    )
    YT_SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
    YT_API_SERVICE_NAME = 'youtube'
    YT_API_VERSION = 'v3'
    
    # 数据库配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'video_search.db'))
    
    # 定时任务配置
    SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'true').lower() == 'true'
