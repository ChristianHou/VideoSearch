# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, session
import google.oauth2.credentials

from ..services.youtube_service import youtube_service
from ..store import task_store


tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.get('/tasks')
def get_tasks():
    return jsonify({"success": True, "tasks": task_store.list_tasks()})


@tasks_bp.post('/tasks')
def create_task():
    try:
        data = request.get_json() or {}
        if 'query' not in data:
            return jsonify({"error": "缺少必需参数: query"}), 400
        task = task_store.create_task(data)
        return jsonify({"success": True, "task_id": task['id'], "task": task}), 201
    except Exception as e:
        return jsonify({"error": f"创建任务失败: {str(e)}"}), 500


@tasks_bp.post('/tasks/<task_id>/execute')
def execute_task(task_id: str):
    task = task_store.get_task(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    if 'credentials' not in session:
        return jsonify({"error": "需要先进行OAuth认证"}), 401

    try:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
        if not youtube_service.authenticate(credentials):
            return jsonify({"error": "API认证失败"}), 500

        result = youtube_service.search_videos(
            query=task['query'],
            max_results=task['max_results'],
            published_after=task.get('published_after'),
            published_before=task.get('published_before'),
            region_code=task.get('region_code'),
            relevance_language=task.get('relevance_language'),
            video_duration=task.get('video_duration'),
            video_definition=task.get('video_definition'),
            video_embeddable=task.get('video_embeddable'),
            video_license=task.get('video_license'),
            video_syndicated=task.get('video_syndicated'),
            video_type=task.get('video_type'),
        )

        if result.get('success'):
            task_store.mark_task_completed(task_id, result['data'])
        else:
            task_store.mark_task_failed(task_id, result.get('error', '未知错误'))

        return jsonify({"success": True, "task": task_store.get_task(task_id), "result": result})
    except Exception as e:
        task_store.mark_task_failed(task_id, str(e))
        return jsonify({"error": f"执行任务失败: {str(e)}"}), 500


@tasks_bp.get('/tasks/<task_id>')
def get_task(task_id: str):
    task = task_store.get_task(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify({"success": True, "task": task})


@tasks_bp.delete('/tasks/<task_id>')
def delete_task(task_id: str):
    deleted = task_store.delete_task(task_id)
    if not deleted:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify({"success": True, "message": "任务已删除", "deleted_task": deleted})
