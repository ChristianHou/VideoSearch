# -*- coding: utf-8 -*-

import uuid
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import schedule

from .database import db_manager
from .models import ScheduledTask, ExecutionResult, ScheduledExecutionResult, Task, VideoInfo, VideoExecutionResult
from .services.youtube_service import youtube_service
from .services.feishu_service import get_feishu_service
from .utils.auth_utils import global_credential_store

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
            # 先检查是否已经存在相同ID的任务，如果存在则先移除
            self.remove_scheduled_task(scheduled_task.id)
            
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
    
    def get_scheduled_jobs(self):
        """获取当前调度器中的所有任务"""
        jobs_info = []
        for job in schedule.jobs:
            job_info = {
                'tags': getattr(job, 'tags', []),
                'next_run': getattr(job, 'next_run', None),
                'interval': getattr(job, 'interval', None),
                'unit': getattr(job, 'unit', None)
            }
            jobs_info.append(job_info)
        return jobs_info
    
    def print_scheduled_jobs(self):
        """打印当前调度器中的所有任务信息"""
        jobs = self.get_scheduled_jobs()
        print(f"当前调度器中有 {len(jobs)} 个任务:")
        for i, job in enumerate(jobs):
            print(f"  任务 {i+1}: 标签={job['tags']}, 下次运行={job['next_run']}, 间隔={job['interval']} {job['unit']}")
    
    def remove_scheduled_task(self, scheduled_task_id: int):
        """从调度器移除定时任务"""
        try:
            print(f"移除定时任务前，调度器状态:")
            self.print_scheduled_jobs()
            
            # 清除所有带有该标签的任务
            schedule.clear(scheduled_task_id)
            
            # 额外检查：清除所有可能相关的任务
            # 由于schedule库的限制，我们需要手动检查并清除
            jobs_to_remove = []
            for job in schedule.jobs:
                if hasattr(job, 'tags') and scheduled_task_id in job.tags:
                    jobs_to_remove.append(job)
            
            for job in jobs_to_remove:
                schedule.jobs.remove(job)
            
            print(f"移除定时任务后，调度器状态:")
            self.print_scheduled_jobs()
            print(f"定时任务已从调度器移除: {scheduled_task_id}")
        except Exception as e:
            print(f"从调度器移除定时任务失败: {e}")
    
    def _schedule_interval_task(self, scheduled_task: ScheduledTask):
        """调度间隔任务"""
        def job():
            # 在执行前检查任务状态
            db = None
            try:
                print(f"检查定时任务 {scheduled_task.id} 状态")
                db = db_manager.get_session()
                print(f"定时任务 {scheduled_task.id} 获取数据库会话成功")
                
                task_check = db.query(ScheduledTask).filter(ScheduledTask.id == scheduled_task.id).first()
                if task_check:
                    print(f"定时任务 {scheduled_task.id} 当前状态: is_active = {task_check.is_active}")
                    if task_check.is_active:
                        print(f"定时任务 {scheduled_task.id} 状态正常，开始执行")
                        self.execute_scheduled_task(scheduled_task.id)
                        # 注意：不需要重新调度，schedule库会自动重复执行
                        print(f"定时任务 {scheduled_task.id} 执行完成，等待下次调度")
                    else:
                        print(f"定时任务 {scheduled_task.id} 已被禁用，跳过执行")
                        # 任务被禁用时，从调度器中移除
                        self.remove_scheduled_task(scheduled_task.id)
                else:
                    print(f"定时任务 {scheduled_task.id} 查询失败")
            except Exception as e:
                print(f"检查定时任务状态时出错: {e}")
            finally:
                # 确保数据库会话被正确关闭
                if db:
                    try:
                        db.close()
                        print(f"定时任务 {scheduled_task.id} 状态检查会话已关闭")
                    except Exception as close_error:
                        print(f"关闭数据库会话时出错: {close_error}")
        
        # 使用schedule库的重复执行功能，不需要手动重新调度
        schedule.every(scheduled_task.interval_minutes).minutes.do(job).tag(scheduled_task.id)
        print(f"定时任务 {scheduled_task.id} 已调度，间隔: {scheduled_task.interval_minutes} 分钟")
    
    def _schedule_daily_task(self, scheduled_task: ScheduledTask):
        """调度每日任务"""
        def job():
            self.execute_scheduled_task(scheduled_task.id)
        
        schedule.every().day.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
    
    def _schedule_weekly_task(self, scheduled_task: ScheduledTask):
        """调度每周任务"""
        def job():
            self.execute_scheduled_task(scheduled_task.id)
        
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
            self.execute_scheduled_task(scheduled_task.id)
        
        # 每月指定日期执行
        schedule.every().month.at(scheduled_task.schedule_time).do(job).tag(scheduled_task.id)
    
    def execute_scheduled_task(self, scheduled_task_id: int):
        """执行定时任务"""
        db = None
        execution_result = None
        
        try:
            # 为每个任务执行创建新的数据库会话
            db = db_manager.get_session()
            print(f"定时任务 {scheduled_task_id} 创建新数据库会话")
            
            # 重新查询定时任务，确保在当前会话中
            scheduled_task = db.query(ScheduledTask).filter_by(id=scheduled_task_id).first()
            if not scheduled_task:
                print(f"定时任务 {scheduled_task_id} 不存在")
                return
            
            # 重新查询搜索任务，确保在当前会话中
            search_task = db.query(Task).filter_by(id=scheduled_task.task_id).first()
            if not search_task:
                print(f"定时任务 {scheduled_task_id} 关联的搜索任务不存在")
                return
            
            print(f"执行定时任务: {scheduled_task_id}")
            print(f"定时任务 {scheduled_task_id} 关联的搜索任务:")
            print(f"  任务ID: {search_task.id}")
            print(f"  查询关键词: {search_task.query}")
            print(f"  最大结果: {search_task.max_results}")
            print(f"  发布时间范围: {search_task.published_after} 至 {search_task.published_before}")
            print(f"  地区: {search_task.region_code}")
            print(f"  语言: {search_task.relevance_language}")
            print(f"  视频时长: {search_task.video_duration}")
            print(f"  视频质量: {search_task.video_definition}")
            print(f"  视频类型: {search_task.video_type}")
            
            # 创建执行结果记录
            execution_result = ScheduledExecutionResult(
                scheduled_task_id=scheduled_task_id,
                status='running',
                started_at=get_east8_time(),
                completed_at=None,
                error_message=None,
                result_data=None,
                videos_count=0
            )
            db.add(execution_result)
            db.commit()
            db.flush()  # 确保ID被分配
            print(f"创建执行结果记录，ID: {execution_result.id}")
            
            # 检查认证状态
            from .utils.auth_utils import global_credential_store
            if not global_credential_store.is_authenticated():
                error_msg = "没有可用的YouTube API认证凭证，请先进行OAuth认证"
                execution_result.status = 'failed'
                execution_result.completed_at = get_east8_time()
                execution_result.error_message = error_msg
                execution_result.result_data = None
                execution_result.videos_count = 0
                db.commit()
                print(f"定时任务 {scheduled_task_id} 认证失败: {error_msg}")
                return
            
            # 获取认证凭证
            credentials = global_credential_store.get_credentials()
            if not credentials:
                error_msg = "无法获取认证凭证"
                execution_result.status = 'failed'
                execution_result.completed_at = get_east8_time()
                execution_result.error_message = error_msg
                execution_result.result_data = None
                execution_result.videos_count = 0
                db.commit()
                print(f"定时任务 {scheduled_task_id} 获取凭证失败: {error_msg}")
                return
            
            # 认证YouTube服务
            from .services.youtube_service import youtube_service
            if not youtube_service.authenticate(credentials):
                error_msg = "YouTube API认证失败"
                execution_result.status = 'failed'
                execution_result.completed_at = get_east8_time()
                execution_result.error_message = error_msg
                execution_result.result_data = None
                execution_result.videos_count = 0
                db.commit()
                print(f"定时任务 {scheduled_task_id} 认证失败: {error_msg}")
                return
            
            print(f"定时任务 {scheduled_task_id} 认证成功，开始执行搜索...")
            print(f"定时任务 {scheduled_task_id} 搜索参数:")
            print(f"  关键词: {search_task.query}")
            print(f"  最大结果: {search_task.max_results}")
            print(f"  发布时间范围: {search_task.published_after} 至 {search_task.published_before}")
            print(f"  地区: {search_task.region_code}")
            print(f"  语言: {search_task.relevance_language}")
            print(f"  视频时长: {search_task.video_duration}")
            print(f"  视频质量: {search_task.video_definition}")
            print(f"  视频类型: {search_task.video_type}")
            
            # 执行搜索
            result = youtube_service.search_videos(
                query=search_task.query,
                max_results=search_task.max_results,
                published_after=search_task.published_after,
                published_before=search_task.published_before,
                region_code=search_task.region_code,
                relevance_language=search_task.relevance_language,
                video_duration=search_task.video_duration,
                video_definition=search_task.video_definition,
                video_type=search_task.video_type,
                video_syndicated=search_task.video_syndicated,
                order_by=search_task.order_by,  # 新增：排序方式
            )
            
            if result.get('success'):
                # 搜索成功，更新执行结果
                execution_result.status = 'success'
                execution_result.completed_at = get_east8_time()
                execution_result.error_message = None
                execution_result.result_data = result['data']
                execution_result.videos_count = result['data'].get('pageInfo', {}).get('totalResults', 0)
                
                # 使用内容过滤服务过滤新视频
                from .services.content_filter_service import content_filter_service
                new_videos, all_videos = content_filter_service.filter_new_videos(scheduled_task_id, result['data'])
                
                # 更新执行结果，记录新视频数量
                execution_result.videos_count = len(new_videos)
                
                # 保存视频信息（只保存新视频）
                if new_videos:
                    for i, video_data in enumerate(new_videos):
                        try:
                            # 保存视频基本信息
                            video_id = video_data.get('id', {}).get('videoId')
                            if not video_id:
                                continue
                            
                            # 检查视频是否已存在
                            existing_video = db.query(VideoInfo).filter_by(video_id=video_id).first()
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
                                db.flush()  # 确保ID被分配
                            
                            # 尝试翻译视频标题和描述
                            try:
                                from .services.translate_service import get_translate_service
                                translate_service = get_translate_service()
                                if translate_service:
                                    # 翻译标题
                                    if video_info.title:
                                        translated_title = translate_service.translate_text(video_info.title)
                                        if translated_title:
                                            video_info.translated_title = translated_title
                                            print(f"标题翻译: '{video_info.title}' -> '{translated_title}'")
                                    
                                    # 翻译描述
                                    if video_info.description:
                                        translated_description = translate_service.translate_text(video_info.description)
                                        if translated_description:
                                            video_info.translated_description = translated_description
                                            print(f"描述翻译: '{video_info.description[:50]}...' -> '{translated_description[:50]}...'")
                                    
                                    # 更新翻译时间
                                    if translated_title or translated_description:
                                        video_info.translation_updated_at = get_east8_time()
                            except Exception as translate_error:
                                print(f"翻译视频信息时出错: {translate_error}")
                            
                            # 创建视频执行结果关联
                            video_execution = VideoExecutionResult(
                                video_id=video_info.id,
                                scheduled_execution_result_id=execution_result.id,
                                rank=i + 1
                            )
                            db.add(video_execution)
                            
                            # 提交当前视频的更改
                            try:
                                db.commit()
                            except Exception as commit_error:
                                print(f"提交视频信息失败: {commit_error}")
                                db.rollback()
                                continue
                        except Exception as video_error:
                            print(f"保存视频信息失败: {video_error}")
                            continue
                
                # 提交所有更改
                db.commit()
                print(f"定时任务 {scheduled_task_id} 执行完成，保存了 {len(new_videos)} 个新视频")
                
                # 发送飞书通知（只推送新内容）
                if new_videos:
                    try:
                        from .services.feishu_service import get_feishu_service
                        feishu_service = get_feishu_service()
                        if feishu_service:
                            # 将新视频数据转换为VideoInfo对象列表
                            new_video_objects = []
                            for video_data in new_videos:
                                video_id = video_data.get('id', {}).get('videoId')
                                if video_id:
                                    # 查询数据库中的视频信息
                                    video_info = db.query(VideoInfo).filter_by(video_id=video_id).first()
                                    if video_info:
                                        new_video_objects.append(video_info)
                            
                            if new_video_objects:
                                feishu_service.send_task_execution_result(
                                    task_name=search_task.query,
                                    videos=new_video_objects,
                                    execution_time=execution_result.completed_at.strftime('%Y-%m-%d %H:%M:%S'),
                                    total_count=len(all_videos),
                                    new_count=len(new_videos)
                                )
                                print(f"飞书通知发送成功，推送了 {len(new_videos)} 个新视频")
                    except Exception as feishu_error:
                        print(f"发送飞书通知失败: {feishu_error}")
                else:
                    print(f"定时任务 {scheduled_task_id} 没有发现新内容，跳过飞书推送")
                
            else:
                # 搜索失败
                error_msg = result.get('error', '未知错误')
                execution_result.status = 'failed'
                execution_result.completed_at = get_east8_time()
                execution_result.error_message = error_msg
                execution_result.result_data = None
                execution_result.videos_count = 0
                db.commit()
                print(f"定时任务 {scheduled_task_id} 搜索失败: {error_msg}")
            
        except Exception as e:
            # 执行过程中出现异常
            try:
                if execution_result and db:
                    execution_result.status = 'failed'
                    execution_result.completed_at = get_east8_time()
                    execution_result.error_message = f"定时任务执行失败: {str(e)}"
                    execution_result.result_data = None
                    execution_result.videos_count = 0
                    db.commit()
                print(f"定时任务 {scheduled_task_id} 执行异常: {str(e)}")
            except Exception as commit_error:
                print(f"更新执行结果失败: {commit_error}")
                if db:
                    db.rollback()
        finally:
            # 确保数据库会话被正确关闭
            if db:
                try:
                    db.close()
                    print(f"定时任务 {scheduled_task_id} 数据库会话已关闭")
                except Exception as close_error:
                    print(f"关闭数据库会话时出错: {close_error}")
        
        print(f"定时任务执行完成: {scheduled_task_id}")
    
    def load_existing_tasks(self):
        """加载数据库中已存在的定时任务"""
        db = None
        try:
            print("开始加载已存在的定时任务")
            db = db_manager.get_session()
            print("获取数据库会话成功")
            
            existing_tasks = db.query(ScheduledTask).filter(ScheduledTask.is_active == True).all()
            print(f"找到 {len(existing_tasks)} 个启用的定时任务")
            
            for task in existing_tasks:
                print(f"加载定时任务: {task.id}, 类型: {task.schedule_type}")
                self.add_scheduled_task(task)
            
            print(f"已加载 {len(existing_tasks)} 个定时任务")
        except Exception as e:
            print(f"加载定时任务失败: {e}")
        finally:
            # 确保数据库会话被正确关闭
            if db:
                try:
                    db.close()
                    print("加载定时任务会话已关闭")
                except Exception as close_error:
                    print(f"关闭数据库会话时出错: {close_error}")

    def check_scheduled_task_status(self):
        """检查定时任务状态"""
        db = None
        try:
            print("开始检查定时任务状态")
            db = db_manager.get_session()
            print("获取数据库会话成功")
            
            scheduled_tasks = db.query(ScheduledTask).all()
            print(f"找到 {len(scheduled_tasks)} 个定时任务")
            
            for scheduled_task in scheduled_tasks:
                try:
                    print(f"检查定时任务 {scheduled_task.id} 状态")
                    # 重新查询任务状态，避免会话绑定问题
                    task_refresh = db.query(ScheduledTask).filter_by(id=scheduled_task.id).first()
                    if task_refresh:
                        print(f"定时任务 {scheduled_task.id} 当前状态: is_active = {task_refresh.is_active}")
                        if not task_refresh.is_active:
                            # 任务已被禁用，从调度器中移除
                            self.remove_scheduled_task(scheduled_task.id)
                            print(f"定时任务 {scheduled_task.id} 已被禁用，从调度器中移除")
                        else:
                            print(f"定时任务 {scheduled_task.id} 状态正常")
                    else:
                        print(f"定时任务 {scheduled_task.id} 查询失败")
                except Exception as e:
                    print(f"检查定时任务 {scheduled_task.id} 状态时出错: {e}")
                    continue
                    
        except Exception as e:
            print(f"检查定时任务状态时出错: {e}")
        finally:
            # 确保数据库会话被正确关闭
            if db:
                try:
                    db.close()
                    print("数据库会话已关闭")
                except Exception as close_error:
                    print(f"关闭数据库会话时出错: {close_error}")


# 全局调度器实例
task_scheduler = TaskScheduler()


def start_scheduler():
    """启动定时任务调度器"""
    task_scheduler.start()
    task_scheduler.load_existing_tasks()


def stop_scheduler():
    """停止定时任务调度器"""
    task_scheduler.stop()
