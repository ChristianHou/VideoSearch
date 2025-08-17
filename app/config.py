# -*- coding: utf-8 -*-

import os
from pathlib import Path


class AppConfig:
    """应用配置类 - 安全地从环境变量读取配置"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('APP_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("APP_SECRET_KEY 环境变量未设置，请在 .env 文件中配置")
    
    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent
    
    # OAuth/YouTube配置
    GOOGLE_CLIENT_SECRETS_FILE = os.environ.get(
        'GOOGLE_CLIENT_SECRETS_FILE',
        str(BASE_DIR / 'config' / 'client_secret.json')
    )
    YT_SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
    YT_API_SERVICE_NAME = 'youtube'
    YT_API_VERSION = 'v3'
    
    # 数据库配置
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'video_search.db'))
    
    # 定时任务配置
    SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'true').lower() == 'true'
    
    # 飞书配置
    FEISHU_APP_ID = os.environ.get('FEISHU_APP_ID')
    FEISHU_APP_SECRET = os.environ.get('FEISHU_APP_SECRET')
    FEISHU_CHAT_ID = os.environ.get('FEISHU_CHAT_ID')
    FEISHU_ENABLED = os.environ.get('FEISHU_ENABLED', 'true').lower() == 'true'
    
    # 火山引擎翻译配置
    VOLC_ACCESS_KEY = os.environ.get('VOLC_ACCESS_KEY')
    VOLC_SECRET_KEY = os.environ.get('VOLC_SECRET_KEY')
    VOLC_ENABLED = os.environ.get('VOLC_ENABLED', 'true').lower() == 'true'
    
    # DeepSeek AI配置
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    DEEPSEEK_ENABLED = os.environ.get('DEEPSEEK_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def validate_config(cls):
        """验证必要的配置项"""
        required_configs = []
        
        if cls.FEISHU_ENABLED:
            if not cls.FEISHU_APP_ID:
                required_configs.append('FEISHU_APP_ID')
            if not cls.FEISHU_APP_SECRET:
                required_configs.append('FEISHU_APP_SECRET')
            if not cls.FEISHU_CHAT_ID:
                required_configs.append('FEISHU_CHAT_ID')
        
        if cls.VOLC_ENABLED:
            if not cls.VOLC_ACCESS_KEY:
                required_configs.append('VOLC_ACCESS_KEY')
            if not cls.VOLC_SECRET_KEY:
                required_configs.append('VOLC_SECRET_KEY')
        
        if cls.DEEPSEEK_ENABLED:
            if not cls.DEEPSEEK_API_KEY:
                required_configs.append('DEEPSEEK_API_KEY')
        
        if required_configs:
            raise ValueError(f"以下必要的配置项未设置: {', '.join(required_configs)}")
        
        return True
    
    @classmethod
    def get_config_summary(cls):
        """获取配置摘要（不包含敏感信息）"""
        return {
            'database_path': cls.DATABASE_PATH,
            'scheduler_enabled': cls.SCHEDULER_ENABLED,
            'feishu_enabled': cls.FEISHU_ENABLED,
            'volc_enabled': cls.VOLC_ENABLED,
            'deepseek_enabled': cls.DEEPSEEK_ENABLED,
            'google_oauth_file': cls.GOOGLE_CLIENT_SECRETS_FILE
        }


# 配置验证
try:
    AppConfig.validate_config()
    print("✅ 配置验证通过")
except ValueError as e:
    print(f"❌ 配置验证失败: {e}")
    print("请检查 .env 文件中的配置项")
    raise
