# -*- coding: utf-8 -*-

import uuid
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from ..database import db_manager
from ..models import Task, ExecutionResult, VideoInfo, VideoExecutionResult
from ..services.translate_service import get_translate_service

# 东八区时区
EAST_8_TZ = datetime.timezone(datetime.timedelta(hours=8))

def get_east8_time():
    """获取东八区当前时间"""
    return datetime.datetime.now(EAST_8_TZ)


def create_task(data: dict) -> dict:
    """创建新任务"""
    db = db_manager.get_session()
    try:
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            query=data['query'],
            max_results=data.get('max_results', 25),
            published_after=data.get('published_after'),
            published_before=data.get('published_before'),
            region_code=data.get('region_code'),
            relevance_language=data.get('relevance_language'),
            video_duration=data.get('video_duration'),
            video_definition=data.get('video_definition'),
            video_embeddable=data.get('video_embeddable'),
            video_license=data.get('video_license'),
            video_syndicated=data.get('video_syndicated'),
            video_type=data.get('video_type'),
            order_by=data.get('order_by', 'relevance'),  # 新增：排序方式
            status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return _task_to_dict(task)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def list_tasks() -> List[dict]:
    """获取所有任务列表"""
    db = db_manager.get_session()
    try:
        tasks = db.query(Task).order_by(Task.created_at.desc()).all()
        return [_task_to_dict(task) for task in tasks]
    finally:
        db.close()


def get_task(task_id: str) -> Optional[dict]:
    """根据任务ID获取任务"""
    db = db_manager.get_session()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        return _task_to_dict(task) if task else None
    finally:
        db.close()


def delete_task(task_id: str) -> Optional[dict]:
    """删除任务"""
    db = db_manager.get_session()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task_dict = _task_to_dict(task)
            db.delete(task)
            db.commit()
            return task_dict
        return None
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def mark_task_completed(task_id: str, results: dict):
    """标记任务完成"""
    db = db_manager.get_session()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = 'completed'
            task.updated_at = get_east8_time()
            
            # 创建执行结果记录
            execution_result = ExecutionResult(
                task_id=task.id,
                status='success',
                started_at=get_east8_time(),
                completed_at=get_east8_time(),
                result_data=results,
                videos_count=len(results.get('items', []))
            )
            
            db.add(execution_result)
            db.flush()  # 确保execution_result.id被设置
            
            # 保存视频信息（不包含翻译）
            video_id_list = []  # 改为保存视频ID列表
            if 'items' in results:
                for i, video_data in enumerate(results['items']):
                    video_info = _save_video_info_basic(video_data, db)
                    if video_info:
                        # 创建视频与执行结果的关联
                        video_execution = VideoExecutionResult(
                            video_id=video_info.id,
                            execution_result_id=execution_result.id,
                            scheduled_execution_result_id=None,  # 明确设置为None
                            rank=i + 1
                        )
                        db.add(video_execution)
                        video_id_list.append(video_info.id)  # 保存视频ID而不是对象
            
            # 提交数据库事务，确保所有数据都被保存
            db.commit()
            
            # 在单独的会话中进行翻译操作，传递视频ID列表
            _translate_videos_async(video_id_list)
            
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def mark_task_failed(task_id: str, error_msg: str):
    """标记任务失败"""
    db = db_manager.get_session()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = 'failed'
            task.updated_at = get_east8_time()
            
            # 创建执行结果记录
            execution_result = ExecutionResult(
                task_id=task.id,
                status='failed',
                started_at=get_east8_time(),
                completed_at=get_east8_time(),
                error_message=error_msg
            )
            
            db.add(execution_result)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def _task_to_dict(task: Task) -> dict:
    """将Task对象转换为字典"""
    if not task:
        return None
    
    # 获取最新的执行结果
    latest_result = None
    if task.execution_results:
        # 按完成时间排序，获取最新的结果
        latest_execution = sorted(task.execution_results, key=lambda x: x.completed_at or x.started_at, reverse=True)[0]
        if latest_execution.status == 'success':
            latest_result = latest_execution.result_data
        elif latest_execution.status == 'failed':
            latest_result = None
    
    return {
        "id": task.task_id,
        "query": task.query,
        "max_results": task.max_results,
        "published_after": task.published_after,
        "published_before": task.published_before,
        "region_code": task.region_code,
        "relevance_language": task.relevance_language,
        "video_duration": task.video_duration,
        "video_definition": task.video_definition,
        "video_embeddable": task.video_embeddable,
        "video_license": task.video_license,
        "video_syndicated": task.video_syndicated,
        "video_type": task.video_type,
        "order_by": task.order_by,  # 新增：排序方式
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "results": latest_result,
        "error": None
    }


def get_task_with_results(task_id: str) -> Optional[dict]:
    """获取任务及其执行结果和视频信息"""
    db = db_manager.get_session()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return None
        
        # 获取最新的执行结果
        latest_result = None
        error_message = None
        
        if task.execution_results:
            # 按完成时间排序，获取最新的结果
            latest_execution = sorted(task.execution_results, key=lambda x: x.completed_at or x.started_at, reverse=True)[0]
            if latest_execution.status == 'success':
                latest_result = latest_execution.result_data
                
                # 获取视频信息，包括翻译后的标题和描述
                if 'items' in latest_result:
                    for item in latest_result['items']:
                        video_id = item.get('id', {}).get('videoId')
                        if video_id:
                            # 查询数据库中的视频信息
                            video_info = db.query(VideoInfo).filter(VideoInfo.video_id == video_id).first()
                            if video_info and video_info.translated_title:
                                # 添加翻译后的标题和描述到结果中
                                if 'snippet' in item:
                                    item['snippet']['translated_title'] = video_info.translated_title
                                    if video_info.translated_description:
                                        item['snippet']['translated_description'] = video_info.translated_description
                
            elif latest_execution.status == 'failed':
                error_message = latest_execution.error_message
        
        task_dict = _task_to_dict(task)
        if task_dict:
            task_dict['results'] = latest_result
            task_dict['error'] = error_message
        
        return task_dict
    finally:
        db.close()


def _save_video_info_basic(video_data: dict, db: Session) -> Optional[VideoInfo]:
    """保存视频基本信息到数据库（不包含翻译）"""
    try:
        video_id = video_data.get('id', {}).get('videoId')
        if not video_id:
            return None
        
        # 检查视频是否已存在
        existing_video = db.query(VideoInfo).filter(VideoInfo.video_id == video_id).first()
        if existing_video:
            return existing_video
        
        # 创建新的视频信息
        snippet = video_data.get('snippet', {})
        statistics = video_data.get('statistics', {})
        
        video_info = VideoInfo(
            video_id=video_id,
            title=snippet.get('title'),
            description=snippet.get('description'),
            channel_title=snippet.get('channelTitle'),
            channel_id=snippet.get('channelId'),
            published_at=datetime.datetime.fromisoformat(snippet.get('publishedAt').replace('Z', '+00:00')).replace(tzinfo=EAST_8_TZ) if snippet.get('publishedAt') else None,
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
        db.flush()  # 获取ID但不提交
        return video_info
        
    except Exception as e:
        print(f"保存视频基本信息失败: {e}")
        return None


def _translate_videos_async(video_id_list: List[int]):
    """异步翻译视频信息"""
    if not video_id_list:
        return
    
    # 在新线程中执行翻译，避免阻塞主流程
    import threading
    
    def translate_worker():
        try:
            translate_service = get_translate_service()
            if not translate_service:
                return
            
            # 创建新的数据库会话进行翻译更新
            db = db_manager.get_session()
            try:
                for video_db_id in video_id_list:
                    current_video = None
                    try:
                        # 重新查询视频信息，确保在正确的会话中
                        # 这里应该用数据库主键ID查询，不是video_id字段
                        current_video = db.query(VideoInfo).filter(VideoInfo.id == video_db_id).first()
                        if not current_video:
                            print(f"视频ID {video_db_id} 在数据库中不存在，跳过翻译")
                            continue
                        
                        # 翻译标题
                        if current_video.title and not current_video.translated_title:
                            translated_title = translate_service.translate_text(current_video.title, 'zh')
                            if translated_title:
                                current_video.translated_title = translated_title
                                print(f"标题翻译: '{current_video.title}' -> '{translated_title}'")
                        
                        # 翻译描述
                        if current_video.description and not current_video.translated_description:
                            # 限制描述长度，避免翻译过长的文本
                            description_text = current_video.description[:500] if len(current_video.description) > 500 else current_video.description
                            translated_description = translate_service.translate_text(description_text, 'zh')
                            if translated_description:
                                current_video.translated_description = translated_description
                                print(f"描述翻译: '{description_text[:50]}...' -> '{translated_description[:50]}...'")
                        
                    except Exception as video_error:
                        print(f"翻译视频ID {video_db_id} 时出错: {video_error}")
                        continue
                
                # 提交翻译结果
                db.commit()
                print(f"成功翻译 {len(video_id_list)} 个视频")
                
            except Exception as e:
                print(f"翻译过程中出错: {e}")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            print(f"翻译服务初始化失败: {e}")
    
    # 启动翻译线程
    translate_thread = threading.Thread(target=translate_worker)
    translate_thread.daemon = True
    translate_thread.start()
