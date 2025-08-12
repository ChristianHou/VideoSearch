# -*- coding: utf-8 -*-

import uuid
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import schedule

from .database import db_manager
from .models import ScheduledTask, ExecutionResult, ScheduledExecutionResult, Task
from .services.youtube_service import youtube_service
from .utils.auth_utils import global_credential_store
from .models import VideoInfo

# 东八区时区
EAST_8_TZ = timezone(timedelta(hours=8))

def get_east8_time():
    """获取东八区当前时间"""
    return datetime.now(EAST_8_TZ)


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.stop_event = threading.Event()
    
    def start(self):
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        self.stop_event.clear()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        print("定时任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        self.stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("定时任务调度器已停止")
    
    def _run_scheduler(self):
        """调度器主循环"""
        while self.running and not self.stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                print(f"调度器运行错误: {e}")
                time.sleep(5)
    
    def add_scheduled_task(self, scheduled_task: ScheduledTask):
        """添加定时任务到调度器"""
        try:
            if scheduled_task.schedule_type == 'interval':
                self._schedule_interval_task(scheduled_task)
            elif scheduled_task.schedule_type == 'daily':
                self._schedule_daily_task(scheduled_task)
            elif scheduled_task.schedule_type == 'weekly':
                self._schedule_weekly_task(scheduled_task)
            elif scheduled_task.schedule_type == 'monthly':
                self._schedule_monthly_task(scheduled_task)
            
            print(f"定时任务已添加到调度器: {scheduled_task.id}")
        except Exception as e:
            print(f"添加定时任务到调度器失败: {e}")
    
    def remove_scheduled_task(self, scheduled_task_id: int):
        """从调度器移除定时任务"""
        try:
            schedule.clear(scheduled_task_id)
            print(f"定时任务已从调度器移除: {scheduled_task_id}")
        except Exception as e:
            print(f"从调度器移除定时任务失败: {e}")
    
    def _schedule_interval_task(self, scheduled_task: ScheduledTask):
        """调度间隔任务"""
        def job():
            self._execute_scheduled_task(scheduled_task)
            # 重新调度下一次执行
            schedule.every(scheduled_task.interval_minutes).minutes.do(job).tag(scheduled_task.id)
        
        # 立即执行一次
        schedule.every(scheduled_task.interval_minutes).minutes.do(job).tag(scheduled_task.id)
    
    def _schedule_daily_task(self, scheduled_task: ScheduledTask):
        """调度每日任务"""
        def job():
            self._execute_scheduled_task(scheduled_task)
        
        schedule.every().day.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
    
    def _schedule_weekly_task(self, scheduled_task: ScheduledTask):
        """调度每周任务"""
        def job():
            self._execute_scheduled_task(scheduled_task)
        
        days = [int(d) for d in scheduled_task.schedule_days.split(',')]
        for day in days:
            if day == 1:
                schedule.every().monday.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
            elif day == 2:
                schedule.every().tuesday.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
            elif day == 3:
                schedule.every().wednesday.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
            elif day == 4:
                schedule.every().thursday.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
            elif day == 5:
                schedule.every().friday.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
            elif day == 6:
                schedule.every().saturday.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
            elif day == 7:
                schedule.every().sunday.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
    
    def _schedule_monthly_task(self, scheduled_task: ScheduledTask):
        """调度每月任务"""
        def job():
            self._execute_scheduled_task(scheduled_task)
        
        # 每月指定日期执行
        schedule.every().month.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
    
    def _execute_scheduled_task(self, scheduled_task: ScheduledTask):
        """执行定时任务"""
        print(f"执行定时任务: {scheduled_task.id}")
        
        # 创建执行结果记录
        execution_result = ScheduledExecutionResult(
            scheduled_task_id=scheduled_task.id,
            started_at=get_east8_time(),
            status='running'
        )
        
        db = db_manager.get_session()
        try:
            db.add(execution_result)
            db.commit()
            
            # 重新查询任务信息，避免懒加载问题
            scheduled_task_refresh = db.query(ScheduledTask).filter(ScheduledTask.id == scheduled_task.id).first()
            if not scheduled_task_refresh:
                raise Exception("定时任务不存在")
            
            # 获取关联的搜索任务信息
            search_task = db.query(Task).filter(Task.id == scheduled_task_refresh.task_id).first()
            
            if not search_task:
                raise Exception("关联的搜索任务不存在")
            
            # 调试：打印搜索任务的详细信息
            print(f"定时任务 {scheduled_task.id} 关联的搜索任务:")
            print(f"  任务ID: {search_task.id}")
            print(f"  查询关键词: {search_task.query}")
            print(f"  最大结果: {search_task.max_results}")
            print(f"  发布时间范围: {search_task.published_after} 至 {search_task.published_before}")
            print(f"  地区: {search_task.region_code}")
            print(f"  语言: {search_task.relevance_language}")
            print(f"  视频时长: {search_task.video_duration}")
            print(f"  视频质量: {search_task.video_definition}")
            print(f"  视频类型: {search_task.video_type}")
            
            # 执行搜索任务 - 使用真实的YouTube API
            try:
                # 从数据库获取认证凭证
                if not global_credential_store.is_authenticated(user_id='default'):
                    error_msg = "没有可用的YouTube API认证凭证，请先进行OAuth认证"
                    print(f"定时任务 {scheduled_task.id} 认证失败: {error_msg}")
                    raise Exception(error_msg)
                
                # 获取凭证并认证YouTube服务
                credentials = global_credential_store.get_credentials(user_id='default')
                if not credentials:
                    error_msg = "无法获取认证凭证对象"
                    print(f"定时任务 {scheduled_task.id} 认证失败: {error_msg}")
                    raise Exception(error_msg)
                
                if not youtube_service.authenticate(credentials):
                    error_msg = "YouTube API认证失败，可能是凭证已过期"
                    print(f"定时任务 {scheduled_task.id} 认证失败: {error_msg}")
                    raise Exception(error_msg)
                
                print(f"定时任务 {scheduled_task.id} 认证成功，开始执行搜索...")
                
                # 记录搜索参数
                print(f"定时任务 {scheduled_task.id} 搜索参数:")
                print(f"  关键词: {search_task.query}")
                print(f"  最大结果: {search_task.max_results}")
                print(f"  发布时间范围: {search_task.published_after} 至 {search_task.published_before}")
                print(f"  地区: {search_task.region_code}")
                print(f"  语言: {search_task.relevance_language}")
                print(f"  视频时长: {search_task.video_duration}")
                print(f"  视频质量: {search_task.video_definition}")
                print(f"  视频类型: {search_task.video_type}")
                
                # 调用真实的YouTube API执行搜索
                result = youtube_service.search_videos(
                    query=search_task.query,
                    max_results=search_task.max_results,
                    published_after=search_task.published_after,
                    published_before=search_task.published_before,
                    region_code=search_task.region_code,
                    relevance_language=search_task.relevance_language,
                    video_duration=search_task.video_duration,
                    video_definition=search_task.video_definition,
                    video_embeddable=search_task.video_embeddable,
                    video_license=search_task.video_license,
                    video_syndicated=search_task.video_syndicated,
                    video_type=search_task.video_type,
                )
                
                if result.get('success'):
                    # 搜索成功，更新执行结果
                    execution_result.status = 'success'
                    execution_result.completed_at = get_east8_time()
                    execution_result.error_message = None
                    execution_result.result_data = result['data']
                    execution_result.videos_count = result['data'].get('pageInfo', {}).get('totalResults', 0)
                    
                    # 保存视频信息
                    if 'items' in result['data']:
                        for i, video_data in enumerate(result['data']['items']):
                            try:
                                # 保存视频基本信息
                                video_id = video_data.get('id', {}).get('videoId')
                                if not video_id:
                                    continue
                                
                                # 检查视频是否已存在
                                existing_video = db.query(VideoInfo).filter(VideoInfo.video_id == video_id).first()
                                if existing_video:
                                    video_info = existing_video
                                else:
                                    # 创建新的视频信息
                                    snippet = video_data.get('snippet', {})
                                    statistics = video_data.get('statistics', {})
                                    
                                    video_info = VideoInfo(
                                        video_id=video_id,
                                        title=snippet.get('title'),
                                        description=snippet.get('description'),
                                        channel_title=snippet.get('channelTitle'),
                                        channel_id=snippet.get('channelId'),
                                        published_at=datetime.fromisoformat(snippet.get('publishedAt').replace('Z', '+00:00')).replace(tzinfo=EAST_8_TZ) if snippet.get('publishedAt') else None,
                                        thumbnails=snippet.get('thumbnails'),
                                        duration=snippet.get('duration'),
                                        view_count=int(statistics.get('viewCount', 0)) if statistics.get('viewCount') else 0,
                                        like_count=int(statistics.get('likeCount', 0)) if statistics.get('likeCount') else 0,
                                        comment_count=int(statistics.get('commentCount', 0)) if statistics.get('commentCount') else 0,
                                        tags=snippet.get('tags'),
                                        category_id=snippet.get('categoryId'),
                                        default_language=snippet.get('defaultLanguage'),
                                        default_audio_language=snippet.get('defaultAudioLanguage')
                                    )
                                    db.add(video_info)
                                    db.flush()
                                
                                # 创建视频执行结果关联
                                from .models import VideoExecutionResult
                                video_execution = VideoExecutionResult(
                                    video_id=video_info.id,
                                    scheduled_execution_result_id=execution_result.id,
                                    rank=i + 1
                                )
                                db.add(video_execution)
                            except Exception as video_error:
                                print(f"保存视频信息失败: {video_error}")
                                continue
                    
                    db.commit()
                    print(f"定时任务 {scheduled_task.id} 执行成功，找到 {execution_result.videos_count} 个视频")
                    
                else:
                    # 搜索失败
                    error_msg = result.get('error', '未知错误')
                    execution_result.status = 'failed'
                    execution_result.completed_at = get_east8_time()
                    execution_result.error_message = error_msg
                    execution_result.result_data = None
                    execution_result.videos_count = 0
                    db.commit()
                    print(f"定时任务 {scheduled_task.id} 搜索失败: {error_msg}")
                
            except Exception as e:
                # 执行过程中出现异常
                error_msg = f"定时任务执行失败: {str(e)}"
                execution_result.status = 'failed'
                execution_result.completed_at = get_east8_time()
                execution_result.error_message = error_msg
                execution_result.result_data = None
                execution_result.videos_count = 0
                db.commit()
                print(f"定时任务 {scheduled_task.id} 执行异常: {error_msg}")
                
        except Exception as e:
            # 数据库操作异常
            try:
                execution_result.status = 'failed'
                execution_result.completed_at = get_east8_time()
                execution_result.error_message = f"数据库操作失败: {str(e)}"
                execution_result.result_data = None
                execution_result.videos_count = 0
                db.commit()
            except:
                db.rollback()
            print(f"定时任务 {scheduled_task.id} 数据库操作失败: {str(e)}")
        finally:
            db.close()
        
        print(f"定时任务执行完成: {scheduled_task.id}")
    
    def load_existing_tasks(self):
        """加载数据库中已存在的定时任务"""
        try:
            db = db_manager.get_session()
            existing_tasks = db.query(ScheduledTask).filter(ScheduledTask.is_active == True).all()
            
            for task in existing_tasks:
                self.add_scheduled_task(task)
            
            print(f"已加载 {len(existing_tasks)} 个定时任务")
            db.close()
        except Exception as e:
            print(f"加载定时任务失败: {e}")


# 全局调度器实例
task_scheduler = TaskScheduler()


def start_scheduler():
    """启动定时任务调度器"""
    task_scheduler.start()
    task_scheduler.load_existing_tasks()


def stop_scheduler():
    """停止定时任务调度器"""
    task_scheduler.stop()
