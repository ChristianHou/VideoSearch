# -*- coding: utf-8 -*-

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from .models import Base
from .config import AppConfig


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.db_session = None
    
    def init_database(self, db_path: str = None):
        """初始化数据库"""
        if db_path is None:
            db_path = os.path.join(AppConfig.BASE_DIR, 'video_search.db')
        
        # 创建数据库引擎
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=False  # 设置为True可以看到SQL语句
        )
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建全局会话
        self.db_session = scoped_session(self.SessionLocal)
        
        # 创建所有表
        Base.metadata.create_all(bind=self.engine)
        
        print(f"数据库已初始化: {db_path}")
    
    def get_session(self):
        """获取数据库会话"""
        if self.db_session is None:
            raise RuntimeError("数据库未初始化，请先调用 init_database()")
        return self.db_session
    
    def close_session(self):
        """关闭数据库会话"""
        if self.db_session:
            self.db_session.remove()
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db():
    """获取数据库会话的依赖函数"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    db_manager.init_database()
