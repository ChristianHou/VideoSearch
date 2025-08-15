# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request
from datetime import datetime
from sqlalchemy import and_

from ..database import db_manager
from ..models import Event, EventScheduledTask, ScheduledTask, Task
from ..utils.datetime_utils import get_east8_time

events_bp = Blueprint('events', __name__)

# 预定义的事件类型
EVENT_TYPES = [
    '国际会议或峰会',
    '高级领导人访问', 
    '国际热点事件'
]

# 预定义的领域
DOMAINS = [
    '政治', '经济', '科技', '军事', '文化', '外交', '贸易', '能源', '环境', '教育'
]

# 预定义的关注点
FOCUS_POINTS = [
    '纪录片', '领导人讲话', '官方媒体视频资料'
]


@events_bp.get('/events/types')
def get_event_types():
    """获取事件类型列表"""
    return jsonify({"success": True, "types": EVENT_TYPES})


@events_bp.get('/events/domains')
def get_domains():
    """获取领域列表"""
    return jsonify({"success": True, "domains": DOMAINS})


@events_bp.get('/events/focus-points')
def get_focus_points():
    """获取关注点列表"""
    return jsonify({"success": True, "focus_points": FOCUS_POINTS})


@events_bp.get('/events')
def list_events():
    """获取所有事件列表"""
    try:
        db = db_manager.get_session()
        events = db.query(Event).order_by(Event.created_at.desc()).all()
        
        result = []
        for event in events:
            # 获取关联的定时任务
            event_tasks = db.query(EventScheduledTask).filter(
                EventScheduledTask.event_id == event.id
            ).all()
            
            scheduled_tasks = []
            for event_task in event_tasks:
                scheduled_task = db.query(ScheduledTask).filter(
                    ScheduledTask.id == event_task.scheduled_task_id
                ).first()
                if scheduled_task:
                    task = db.query(Task).filter(Task.id == scheduled_task.task_id).first()
                    if task:
                        scheduled_tasks.append({
                            'id': scheduled_task.id,
                            'task_id': task.task_id,
                            'query': task.query,
                            'status': scheduled_task.is_active,
                            'schedule_type': scheduled_task.schedule_type
                        })
            
            event_dict = {
                'id': event.id,
                'name': event.name,
                'event_type': event.event_type,
                'countries': event.countries or [],
                'domains': event.domains or [],
                'keywords': event.keywords or [],
                'focus_points': event.focus_points or [],
                'involves_china': event.involves_china,
                'start_date': event.start_date.isoformat() if event.start_date else None,
                'end_date': event.end_date.isoformat() if event.end_date else None,
                'description': event.description,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'updated_at': event.updated_at.isoformat() if event.updated_at else None,
                'scheduled_tasks': scheduled_tasks
            }
            result.append(event_dict)
        
        return jsonify({"success": True, "events": result})
        
    except Exception as e:
        return jsonify({"error": f"获取事件列表失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@events_bp.get('/events/<int:event_id>')
def get_event(event_id: int):
    """获取指定事件详情"""
    try:
        db = db_manager.get_session()
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            return jsonify({"error": "事件不存在"}), 404
        
        # 获取关联的定时任务
        event_tasks = db.query(EventScheduledTask).filter(
            EventScheduledTask.event_id == event.id
        ).all()
        
        scheduled_tasks = []
        for event_task in event_tasks:
            scheduled_task = db.query(ScheduledTask).filter(
                ScheduledTask.id == event_task.scheduled_task_id
            ).first()
            if scheduled_task:
                task = db.query(Task).filter(Task.id == scheduled_task.task_id).first()
                if task:
                    scheduled_tasks.append({
                        'id': scheduled_task.id,
                        'task_id': task.task_id,
                        'query': task.query,
                        'status': scheduled_task.is_active,
                        'schedule_type': scheduled_task.schedule_type
                    })
        
        event_dict = {
            'id': event.id,
            'name': event.name,
            'event_type': event.event_type,
            'countries': event.countries or [],
            'domains': event.domains or [],
            'keywords': event.keywords or [],
            'focus_points': event.focus_points or [],
            'involves_china': event.involves_china,
            'start_date': event.start_date.isoformat() if event.start_date else None,
            'end_date': event.end_date.isoformat() if event.end_date else None,
            'description': event.description,
            'created_at': event.created_at.isoformat() if event.created_at else None,
            'updated_at': event.updated_at.isoformat() if event.updated_at else None,
            'scheduled_tasks': scheduled_tasks
        }
        
        return jsonify({"success": True, "event": event_dict})
        
    except Exception as e:
        return jsonify({"error": f"获取事件详情失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@events_bp.post('/events')
def create_event():
    """创建新事件"""
    try:
        data = request.get_json() or {}
        
        # 验证必需参数
        required_fields = ['name', 'event_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400
        
        # 验证事件类型
        if data['event_type'] not in EVENT_TYPES:
            return jsonify({"error": f"无效的事件类型: {data['event_type']}"}), 400
        
        db = db_manager.get_session()
        
        # 创建事件
        event = Event(
            name=data['name'],
            event_type=data['event_type'],
            countries=data.get('countries', []),
            domains=data.get('domains', []),
            keywords=data.get('keywords', []),
            focus_points=data.get('focus_points', []),
            involves_china=data.get('involves_china', False),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            description=data.get('description', '')
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        # 处理关联的定时任务
        if data.get('scheduled_task_ids'):
            for task_id in data['scheduled_task_ids']:
                # 验证定时任务是否存在
                scheduled_task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                if scheduled_task:
                    event_task = EventScheduledTask(
                        event_id=event.id,
                        scheduled_task_id=task_id
                    )
                    db.add(event_task)
            
            db.commit()
        
        return jsonify({
            "success": True, 
            "message": "事件创建成功",
            "event_id": event.id
        }), 201
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": f"创建事件失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@events_bp.put('/events/<int:event_id>')
def update_event(event_id: int):
    """更新事件"""
    try:
        data = request.get_json() or {}
        
        db = db_manager.get_session()
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            return jsonify({"error": "事件不存在"}), 404
        
        # 更新事件字段
        if 'name' in data:
            event.name = data['name']
        if 'event_type' in data:
            if data['event_type'] not in EVENT_TYPES:
                return jsonify({"error": f"无效的事件类型: {data['event_type']}"}), 400
            event.event_type = data['event_type']
        if 'countries' in data:
            event.countries = data['countries']
        if 'domains' in data:
            event.domains = data['domains']
        if 'keywords' in data:
            event.keywords = data['keywords']
        if 'focus_points' in data:
            event.focus_points = data['focus_points']
        if 'involves_china' in data:
            event.involves_china = data['involves_china']
        if 'start_date' in data:
            event.start_date = datetime.fromisoformat(data['start_date']) if data['start_date'] else None
        if 'end_date' in data:
            event.end_date = datetime.fromisoformat(data['end_date']) if data['end_date'] else None
        if 'description' in data:
            event.description = data['description']
        
        event.updated_at = get_east8_time()
        
        # 处理关联的定时任务
        if 'scheduled_task_ids' in data:
            # 删除现有的关联
            db.query(EventScheduledTask).filter(EventScheduledTask.event_id == event.id).delete()
            
            # 添加新的关联
            for task_id in data['scheduled_task_ids']:
                scheduled_task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                if scheduled_task:
                    event_task = EventScheduledTask(
                        event_id=event.id,
                        scheduled_task_id=task_id
                    )
                    db.add(event_task)
        
        db.commit()
        
        return jsonify({
            "success": True, 
            "message": "事件更新成功"
        })
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": f"更新事件失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@events_bp.delete('/events/<int:event_id>')
def delete_event(event_id: int):
    """删除事件"""
    try:
        db = db_manager.get_session()
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            return jsonify({"error": "事件不存在"}), 404
        
        # 删除关联的定时任务关系
        db.query(EventScheduledTask).filter(EventScheduledTask.event_id == event.id).delete()
        
        # 删除事件
        db.delete(event)
        db.commit()
        
        return jsonify({
            "success": True, 
            "message": "事件删除成功"
        })
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": f"删除事件失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()


@events_bp.get('/events/<int:event_id>/scheduled-tasks')
def get_event_scheduled_tasks(event_id: int):
    """获取事件关联的定时任务列表"""
    try:
        db = db_manager.get_session()
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            return jsonify({"error": "事件不存在"}), 404
        
        event_tasks = db.query(EventScheduledTask).filter(
            EventScheduledTask.event_id == event.id
        ).all()
        
        scheduled_tasks = []
        for event_task in event_tasks:
            scheduled_task = db.query(ScheduledTask).filter(
                ScheduledTask.id == event_task.scheduled_task_id
            ).first()
            if scheduled_task:
                task = db.query(Task).filter(Task.id == scheduled_task.task_id).first()
                if task:
                    scheduled_tasks.append({
                        'id': scheduled_task.id,
                        'task_id': task.task_id,
                        'query': task.query,
                        'status': scheduled_task.is_active,
                        'schedule_type': scheduled_task.schedule_type,
                        'next_run': scheduled_task.next_run.isoformat() if scheduled_task.next_run else None,
                        'created_at': scheduled_task.created_at.isoformat() if scheduled_task.created_at else None
                    })
        
        return jsonify({"success": True, "scheduled_tasks": scheduled_tasks})
        
    except Exception as e:
        return jsonify({"error": f"获取事件定时任务失败: {str(e)}"}), 500
    finally:
        if 'db' in locals():
            db.close()
