# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# 东八区时区
EAST_8_TZ = timezone(timedelta(hours=8))

def get_east8_time():
    """获取东八区当前时间"""
    return datetime.now(EAST_8_TZ)


class Task(Base):
    """任务表"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)
    query = Column(String(500), nullable=False)
    max_results = Column(Integer, default=25)
    published_after = Column(String(50))
    published_before = Column(String(50))
    region_code = Column(String(10))
    relevance_language = Column(String(10))
    video_duration = Column(String(20))
    video_definition = Column(String(20))
    video_embeddable = Column(Boolean)
    video_license = Column(String(20))
    video_syndicated = Column(Boolean)
    video_type = Column(String(20))
    order_by = Column(String(20), default='relevance')  # 新增：排序方式 (relevance, date, viewCount, rating, title, videoCount)
    status = Column(String(20), default='pending', index=True)
    created_at = Column(DateTime, default=get_east8_time)
    updated_at = Column(DateTime, default=get_east8_time, onupdate=get_east8_time)
    
    # 关联定时任务
    scheduled_tasks = relationship("ScheduledTask", back_populates="task", cascade="all, delete-orphan")
    # 关联执行结果
    execution_results = relationship("ExecutionResult", back_populates="task", cascade="all, delete-orphan")


class ScheduledTask(Base):
    """定时任务表"""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    schedule_type = Column(String(20), nullable=False)  # 'interval', 'daily', 'weekly', 'monthly'
    interval_minutes = Column(Integer)  # 间隔分钟数（用于interval类型）
    schedule_time = Column(String(10))  # 执行时间，格式：HH:MM
    schedule_days = Column(String(100))  # 执行日期，格式：1,2,3,4,5,6,7（周一到周日）
    schedule_date = Column(String(10))  # 执行日期，格式：DD（每月第几天）
    is_active = Column(Boolean, default=True)
    next_run = Column(DateTime)
    created_at = Column(DateTime, default=get_east8_time)
    updated_at = Column(DateTime, default=get_east8_time, onupdate=get_east8_time)
    
    # 关联任务
    task = relationship("Task", back_populates="scheduled_tasks")
    # 关联执行结果
    execution_results = relationship("ScheduledExecutionResult", back_populates="scheduled_task", cascade="all, delete-orphan")


class ExecutionResult(Base):
    """任务执行结果表"""
    __tablename__ = 'execution_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    status = Column(String(20), nullable=False)  # 'success', 'failed'
    started_at = Column(DateTime, default=get_east8_time)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    result_data = Column(JSON)
    videos_count = Column(Integer, default=0)
    
    # 关联任务
    task = relationship("Task", back_populates="execution_results")


class ScheduledExecutionResult(Base):
    """定时任务执行结果表"""
    __tablename__ = 'scheduled_execution_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scheduled_task_id = Column(Integer, ForeignKey('scheduled_tasks.id'), nullable=False)
    status = Column(String(20), nullable=False)  # 'running', 'success', 'failed'
    started_at = Column(DateTime, default=get_east8_time)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    result_data = Column(JSON)  # JSON格式的搜索结果
    videos_count = Column(Integer, default=0)
    
    # 关联定时任务
    scheduled_task = relationship("ScheduledTask", back_populates="execution_results")


class VideoInfo(Base):
    """视频信息表"""
    __tablename__ = 'video_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(50), nullable=False, index=True)
    title = Column(String(500))
    description = Column(Text)
    channel_title = Column(String(200))
    channel_id = Column(String(50))
    published_at = Column(DateTime)
    thumbnails = Column(JSON)
    duration = Column(String(20))
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    tags = Column(JSON)
    category_id = Column(String(20))
    default_language = Column(String(10))
    default_audio_language = Column(String(10))
    created_at = Column(DateTime, default=get_east8_time)
    
    # 翻译相关字段
    translated_title = Column(String(500))  # 翻译后的标题
    translated_description = Column(Text)   # 翻译后的描述
    translation_updated_at = Column(DateTime)  # 翻译更新时间
    
    # 关联执行结果
    execution_results = relationship("VideoExecutionResult", back_populates="video", cascade="all, delete-orphan")


class VideoExecutionResult(Base):
    """视频与执行结果的关联表"""
    __tablename__ = 'video_execution_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey('video_info.id'), nullable=False)
    execution_result_id = Column(Integer, ForeignKey('execution_results.id'), nullable=True)  # 普通任务执行结果
    scheduled_execution_result_id = Column(Integer, ForeignKey('scheduled_execution_results.id'), nullable=True)  # 定时任务执行结果
    rank = Column(Integer)  # 在搜索结果中的排名
    
    # 关联
    video = relationship("VideoInfo", back_populates="execution_results")
    execution_result = relationship("ExecutionResult")
    scheduled_execution_result = relationship("ScheduledExecutionResult")
    
    # 确保至少有一个执行结果ID
    __table_args__ = (
        CheckConstraint(
            '(execution_result_id IS NOT NULL AND scheduled_execution_result_id IS NULL) OR '
            '(execution_result_id IS NULL AND scheduled_execution_result_id IS NOT NULL)',
            name='check_execution_result_xor'
        ),
    )


class AuthCredentials(Base):
    """认证凭证表"""
    __tablename__ = 'auth_credentials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, default='default')  # 用户ID，支持多用户
    token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_uri = Column(String, nullable=False)
    client_id = Column(String, nullable=False)
    client_secret = Column(String, nullable=False)
    scopes = Column(Text, nullable=False)  # JSON格式的作用域列表
    expires_at = Column(DateTime)  # 令牌过期时间
    is_active = Column(Boolean, default=True)  # 是否活跃
    created_at = Column(DateTime, default=get_east8_time)
    updated_at = Column(DateTime, default=get_east8_time, onupdate=get_east8_time)
    
    def is_expired(self):
        """检查凭证是否已过期"""
        if not self.expires_at:
            return False
        # 确保使用相同的时区格式进行比较
        current_time = datetime.now(EAST_8_TZ)
        if self.expires_at.tzinfo is None:
            # 如果过期时间没有时区信息，假设是UTC时间
            from datetime import timezone
            expires_at_utc = self.expires_at.replace(tzinfo=timezone.utc)
            return current_time >= expires_at_utc
        else:
            # 如果过期时间有时区信息，直接比较
            return current_time >= self.expires_at
    
    def needs_refresh(self):
        """检查是否需要刷新凭证（提前5分钟刷新）"""
        if not self.expires_at:
            return False
        # 确保使用相同的时区格式进行比较
        current_time = datetime.now(EAST_8_TZ)
        refresh_time = self.expires_at - timedelta(minutes=5)
        
        if self.expires_at.tzinfo is None:
            # 如果过期时间没有时区信息，假设是UTC时间
            from datetime import timezone
            expires_at_utc = self.expires_at.replace(tzinfo=timezone.utc)
            refresh_time_utc = expires_at_utc - timedelta(minutes=5)
            return current_time >= refresh_time_utc
        else:
            # 如果过期时间有时区信息，直接比较
            return current_time >= refresh_time


class Event(Base):
    """事件管理表"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment='事件名称')
    event_type = Column(String(50), nullable=False, comment='事件类型：国际会议或峰会、高级领导人访问、国际热点事件')
    countries = Column(JSON, comment='涉及国家列表')
    domains = Column(JSON, comment='涉及领域列表：政治、经济、科技、军事、文化等')
    keywords = Column(JSON, comment='关键词列表：国家名称、领导人名称等')
    focus_points = Column(JSON, comment='关注点列表：纪录片、领导人讲话、官方媒体视频资料')
    involves_china = Column(Boolean, default=False, comment='是否直接涉及中国')
    start_date = Column(DateTime, comment='开始日期')
    end_date = Column(DateTime, comment='结束日期')
    description = Column(Text, comment='事件描述')
    created_at = Column(DateTime, default=get_east8_time)
    updated_at = Column(DateTime, default=get_east8_time, onupdate=get_east8_time)
    
    # 关联定时任务
    event_scheduled_tasks = relationship("EventScheduledTask", back_populates="event")


class EventScheduledTask(Base):
    """事件与定时任务的关联表"""
    __tablename__ = 'event_scheduled_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    scheduled_task_id = Column(Integer, ForeignKey('scheduled_tasks.id'), nullable=False)
    created_at = Column(DateTime, default=get_east8_time)
    
    # 关联关系
    event = relationship("Event", back_populates="event_scheduled_tasks")
    scheduled_task = relationship("ScheduledTask")

class CrawlWebsite(Base):
    """爬取网站表"""
    __tablename__ = 'crawl_websites'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment='网站名称')
    url = Column(String(500), nullable=False, comment='网站URL')
    description = Column(Text, comment='网站描述')
    crawl_pattern = Column(String(500), comment='爬取模式/规则')
    crawl_config = Column(Text, comment='爬取配置（JSON格式）')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class CrawlTask(Base):
    """爬取任务表"""
    __tablename__ = 'crawl_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment='任务名称')
    website_id = Column(Integer, ForeignKey('crawl_websites.id'), nullable=False, comment='关联网站ID')
    task_type = Column(String(50), default='manual', comment='任务类型：manual(手动), scheduled(定时)')
    status = Column(String(50), default='pending', comment='任务状态：pending(待执行), running(执行中), completed(已完成), failed(失败)')
    crawl_config = Column(Text, comment='爬取配置(JSON格式)')
    scheduled_time = Column(DateTime, comment='计划执行时间')
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    total_videos = Column(Integer, default=0, comment='爬取到的视频总数')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    website = relationship('CrawlWebsite', backref='tasks')

class CrawlVideo(Base):
    """爬取视频信息表"""
    __tablename__ = 'crawl_videos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('crawl_tasks.id'), nullable=False, comment='关联任务ID')
    website_id = Column(Integer, ForeignKey('crawl_websites.id'), nullable=False, comment='关联网站ID')
    video_title = Column(String(500), nullable=False, comment='视频标题')
    video_url = Column(String(1000), nullable=False, comment='视频链接')
    video_description = Column(Text, comment='视频简介')
    thumbnail_url = Column(String(1000), comment='缩略图URL')
    duration = Column(String(100), comment='视频时长')
    upload_date = Column(String(100), comment='上传日期')
    view_count = Column(String(100), comment='观看次数')
    like_count = Column(String(100), comment='点赞数')
    # 双语字段
    translated_title = Column(String(500), comment='翻译后的标题')
    translated_description = Column(Text, comment='翻译后的简介')
    language = Column(String(10), default='zh-CN', comment='翻译语言')
    crawl_time = Column(DateTime, default=datetime.utcnow, comment='爬取时间')
    
    # 关联关系
    task = relationship('CrawlTask', backref='videos')
    website = relationship('CrawlWebsite', backref='videos')

class CrawlScheduledTask(Base):
    """爬取定时任务表"""
    __tablename__ = 'crawl_scheduled_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment='定时任务名称')
    website_id = Column(Integer, ForeignKey('crawl_websites.id'), nullable=False, comment='关联网站ID')
    schedule_type = Column(String(50), nullable=False, comment='调度类型：interval(间隔), cron(定时)')
    schedule_value = Column(String(100), nullable=False, comment='调度值：间隔时间或cron表达式')
    is_active = Column(Boolean, default=True, comment='是否启用')
    last_run = Column(DateTime, comment='上次运行时间')
    next_run = Column(DateTime, comment='下次运行时间')
    total_runs = Column(Integer, default=0, comment='总运行次数')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    website = relationship('CrawlWebsite', backref='scheduled_tasks')
