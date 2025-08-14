# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, session
from datetime import datetime, timedelta, timezone
import uuid

from ..database import db_manager
from ..models import Task, ScheduledTask, ScheduledExecutionResult
from ..scheduler import task_scheduler

scheduled_tasks_bp = Blueprint('scheduled_tasks', __name__)

# 东八区时区
EAST_8_TZ = timezone(timedelta(hours=8))

def get_east8_time():
    """获取东八区当前时间"""
    return datetime.now(EAST_8_TZ)


@scheduled_tasks_bp.post('/scheduled-tasks')
def create_scheduled_task():
    """创建定时任务"""
    try:
        data = request.get_json() or {}
        
        # 验证必需参数
        required_fields = ['task_id', 'schedule_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400
        
        # 验证任务是否存在
        db = db_manager.get_session()
        task = db.query(Task).filter(Task.task_id == data['task_id']).first()
        if not task:
            return jsonify({"error": "任务不存在"}), 404
        
        # 验证调度类型和参数
        schedule_type = data['schedule_type']
        if schedule_type == 'interval':
            if 'interval_minutes' not in data or data['interval_minutes'] < 1:
                return jsonify({"error": "间隔任务需要指定有效的interval_minutes参数"}), 400
        elif schedule_type in ['daily', 'weekly', 'monthly']:
            if 'schedule_time' not in data:
                return jsonify({"error": f"{schedule_type}任务需要指定schedule_time参数"}), 400
            if schedule_type == 'weekly' and 'schedule_days' not in data:
                return jsonify({"error": "每周任务需要指定schedule_days参数"}), 400
            if schedule_type == 'monthly' and 'schedule_date' not in data:
                return jsonify({"error": "每月任务需要指定schedule_date参数"}), 400
        
        # 创建定时任务
        scheduled_task = ScheduledTask(
            task_id=task.id,
            schedule_type=schedule_type,
            interval_minutes=data.get('interval_minutes'),
            schedule_time=data.get('schedule_time'),
            schedule_days=data.get('schedule_days'),
            schedule_date=data.get('schedule_date'),
            is_active=True
        )
        
        # 计算下次执行时间
        scheduled_task.next_run = _calculate_next_run(scheduled_task)
        
        db.add(scheduled_task)
        db.commit()
        db.refresh(scheduled_task)
        
        # 添加到调度器
        task_scheduler.add_scheduled_task(scheduled_task)
        
        return jsonify({
            "success": True, 
            "scheduled_task_id": scheduled_task.id,
            "scheduled_task": _scheduled_task_to_dict(scheduled_task)
        }), 201
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": f"创建定时任务失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@scheduled_tasks_bp.get('/scheduled-tasks')
def list_scheduled_tasks():
    """获取所有定时任务列表"""
    try:
        db = db_manager.get_session()
        scheduled_tasks = db.query(ScheduledTask).join(Task).order_by(ScheduledTask.created_at.desc()).all()
        
        result = []
        for st in scheduled_tasks:
            task_dict = _scheduled_task_to_dict(st)
            task_dict['task'] = {
                'id': st.task.task_id,
                'query': st.task.query,
                'status': st.task.status,
                'max_results': st.task.max_results,
                'created_at': st.task.created_at.isoformat() if st.task.created_at else None,
                'region_code': st.task.region_code,
                'relevance_language': st.task.relevance_language,
                'video_duration': st.task.video_duration,
                'video_definition': st.task.video_definition,
                'video_type': st.task.video_type
            }
            result.append(task_dict)
        
        return jsonify({"success": True, "scheduled_tasks": result})
    except Exception as e:
        return jsonify({"error": f"获取定时任务列表失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@scheduled_tasks_bp.get('/scheduled-tasks/<int:scheduled_task_id>')
def get_scheduled_task(scheduled_task_id: int):
    """获取指定定时任务详情"""
    try:
        db = db_manager.get_session()
        scheduled_task = db.query(ScheduledTask).filter(ScheduledTask.id == scheduled_task_id).first()
        
        if not scheduled_task:
            return jsonify({"error": "定时任务不存在"}), 404
        
        result = _scheduled_task_to_dict(scheduled_task)
        result['task'] = {
            'id': scheduled_task.task.task_id,
            'query': scheduled_task.task.query,
            'status': scheduled_task.task.status,
            'max_results': scheduled_task.task.max_results,
            'created_at': scheduled_task.task.created_at.isoformat() if scheduled_task.task.created_at else None,
            'region_code': scheduled_task.task.region_code,
            'relevance_language': scheduled_task.task.relevance_language,
            'video_duration': scheduled_task.task.video_duration,
            'video_definition': scheduled_task.task.video_definition,
            'video_type': scheduled_task.task.video_type
        }
        
        return jsonify({"success": True, "scheduled_task": result})
    except Exception as e:
        return jsonify({"error": f"获取定时任务详情失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@scheduled_tasks_bp.put('/scheduled-tasks/<int:scheduled_task_id>/toggle')
def toggle_scheduled_task(scheduled_task_id: int):
    """启用/禁用定时任务"""
    try:
        data = request.get_json() or {}
        is_active = data.get('is_active', True)
        
        db = db_manager.get_session()
        scheduled_task = db.query(ScheduledTask).filter(ScheduledTask.id == scheduled_task_id).first()
        
        if not scheduled_task:
            return jsonify({"error": "定时任务不存在"}), 404
        
        scheduled_task.is_active = is_active
        
        if is_active:
            # 重新计算下次执行时间并添加到调度器
            scheduled_task.next_run = _calculate_next_run(scheduled_task)
            task_scheduler.add_scheduled_task(scheduled_task)
        else:
            # 从调度器移除
            task_scheduler.remove_scheduled_task(scheduled_task_id)
        
        db.commit()
        
        return jsonify({
            "success": True, 
            "message": f"定时任务已{'启用' if is_active else '禁用'}",
            "scheduled_task": _scheduled_task_to_dict(scheduled_task)
        })
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": f"切换定时任务状态失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@scheduled_tasks_bp.delete('/scheduled-tasks/<int:scheduled_task_id>')
def delete_scheduled_task(scheduled_task_id: int):
    """删除定时任务"""
    try:
        db = db_manager.get_session()
        scheduled_task = db.query(ScheduledTask).filter(ScheduledTask.id == scheduled_task_id).first()
        
        if not scheduled_task:
            return jsonify({"error": "定时任务不存在"}), 404
        
        # 从调度器移除
        task_scheduler.remove_scheduled_task(scheduled_task_id)
        
        # 从数据库删除
        db.delete(scheduled_task)
        db.commit()
        
        return jsonify({"success": True, "message": "定时任务已删除"})
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": f"删除定时任务失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@scheduled_tasks_bp.get('/scheduled-tasks/<int:scheduled_task_id>/executions')
def get_scheduled_task_executions(scheduled_task_id: int):
    """获取定时任务的执行历史"""
    try:
        db = db_manager.get_session()
        executions = db.query(ScheduledExecutionResult).filter(
            ScheduledExecutionResult.scheduled_task_id == scheduled_task_id
        ).order_by(ScheduledExecutionResult.started_at.desc()).all()
        
        result = []
        for execution in executions:
            result.append({
                'id': execution.id,
                'status': execution.status,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'error_message': execution.error_message,
                'videos_count': execution.videos_count,
                'result_data': execution.result_data
            })
        
        return jsonify({"success": True, "executions": result})
    except Exception as e:
        return jsonify({"error": f"获取执行历史失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@scheduled_tasks_bp.get('/scheduled-tasks/executions/<int:execution_id>/videos')
def get_execution_videos(execution_id: int):
    """获取执行结果的视频列表"""
    try:
        db = db_manager.get_session()
        execution = db.query(ScheduledExecutionResult).filter(
            ScheduledExecutionResult.id == execution_id
        ).first()
        
        if not execution:
            return jsonify({"error": "执行记录不存在"}), 400
        
        if execution.status != 'success' or not execution.result_data:
            return jsonify({"error": "执行未成功或无结果数据"}), 400
        
        # 从数据库中获取保存的视频信息
        from ..models import VideoExecutionResult, VideoInfo
        
        video_executions = db.query(VideoExecutionResult).filter(
            VideoExecutionResult.scheduled_execution_result_id == execution_id
        ).order_by(VideoExecutionResult.rank).all()
        
        videos = []
        for video_execution in video_executions:
            video_info = video_execution.video
            if video_info:
                # 构建视频数据结构，保持与YouTube API返回格式一致
                video_data = {
                    'id': {'videoId': video_info.video_id},
                    'snippet': {
                        'title': video_info.title,
                        'description': video_info.description,
                        'channelTitle': video_info.channel_title,
                        'channelId': video_info.channel_id,
                        'publishedAt': video_info.published_at.isoformat() if video_info.published_at else None,
                        'thumbnails': video_info.thumbnails,
                        'tags': video_info.tags,
                        'categoryId': video_info.category_id,
                        'defaultLanguage': video_info.default_language,
                        'defaultAudioLanguage': video_info.default_audio_language
                    },
                    'statistics': {
                        'viewCount': str(video_info.view_count) if video_info.view_count else '0',
                        'likeCount': str(video_info.like_count) if video_info.like_count else '0',
                        'commentCount': str(video_info.comment_count) if video_info.comment_count else '0'
                    },
                    # 添加翻译字段
                    'translated_title': video_info.translated_title,
                    'translated_description': video_info.translated_description
                }
                videos.append(video_data)
        
        # 如果没有从数据库获取到视频，则从result_data中提取（兼容性）
        if not videos and 'items' in execution.result_data:
            videos = execution.result_data['items']
            print(f"从result_data中提取视频数据，共{len(videos)}个")
        
        print(f"执行记录 {execution_id} 的视频数据: 数据库{len([v for v in videos if 'id' in v and 'videoId' in v['id']])}个, 总计{len(videos)}个")
        
        return jsonify({"success": True, "videos": videos})
    except Exception as e:
        return jsonify({"error": f"获取视频列表失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


def _scheduled_task_to_dict(scheduled_task: ScheduledTask) -> dict:
    """将ScheduledTask对象转换为字典"""
    if not scheduled_task:
        return None
    
    return {
        'id': scheduled_task.id,
        'schedule_type': scheduled_task.schedule_type,
        'interval_minutes': scheduled_task.interval_minutes,
        'schedule_time': scheduled_task.schedule_time,
        'schedule_days': scheduled_task.schedule_days,
        'schedule_date': scheduled_task.schedule_date,
        'is_active': scheduled_task.is_active,
        'next_run': scheduled_task.next_run.isoformat() if scheduled_task.next_run else None,
        'created_at': scheduled_task.created_at.isoformat() if scheduled_task.created_at else None,
        'updated_at': scheduled_task.updated_at.isoformat() if scheduled_task.updated_at else None
    }


def _calculate_next_run(scheduled_task: ScheduledTask) -> datetime:
    """计算下次执行时间"""
    now = get_east8_time()
    
    if scheduled_task.schedule_type == 'interval':
        return now + timedelta(minutes=scheduled_task.interval_minutes)
    
    elif scheduled_task.schedule_type == 'daily':
        time_parts = scheduled_task.schedule_time.split(':')
        hour, minute = int(time_parts[0]), int(time_parts[1])
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run
    
    elif scheduled_task.schedule_type == 'weekly':
        time_parts = scheduled_task.schedule_time.split(':')
        hour, minute = int(time_parts[0]), int(time_parts[1])
        days = [int(d) for d in scheduled_task.schedule_days.split(',')]
        
        # 找到下一个执行日期
        for day_offset in range(1, 8):
            next_date = now + timedelta(days=day_offset)
            if next_date.weekday() + 1 in days:  # weekday()返回0-6，我们使用1-7
                next_run = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return next_run
        
        # 如果本周没有找到，找下周
        for day_offset in range(8, 15):
            next_date = now + timedelta(days=day_offset)
            if next_date.weekday() + 1 in days:
                next_run = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return next_run
    
    elif scheduled_task.schedule_type == 'monthly':
        time_parts = scheduled_task.schedule_time.split(':')
        hour, minute = int(time_parts[0]), int(time_parts[1])
        day = int(scheduled_task.schedule_date)
        
        # 计算下个月的同一天
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=day, hour=hour, minute=minute, second=0, microsecond=0)
        else:
            next_month = now.replace(month=now.month + 1, day=day, hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_month <= now:
            # 如果下个月的同一天已经过去，找再下个月
            if next_month.month == 12:
                next_month = next_month.replace(year=next_month.year + 1, month=1)
            else:
                next_month = next_month.replace(month=next_month.month + 1)
        
        return next_month
    
    return now + timedelta(hours=1)  # 默认1小时后
