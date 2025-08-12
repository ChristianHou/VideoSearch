# -*- coding: utf-8 -*-

import datetime
from typing import Dict, Optional


_tasks: Dict[str, dict] = {}
_task_counter: int = 1


def create_task(data: dict) -> dict:
    global _task_counter
    task_id = f"task_{_task_counter}"
    _task_counter += 1

    task = {
        "id": task_id,
        "query": data['query'],
        "max_results": data.get('max_results', 25),
        "published_after": data.get('published_after'),
        "published_before": data.get('published_before'),
        "region_code": data.get('region_code'),
        "relevance_language": data.get('relevance_language'),
        "video_duration": data.get('video_duration'),
        "video_definition": data.get('video_definition'),
        "video_embeddable": data.get('video_embeddable'),
        "video_license": data.get('video_license'),
        "video_syndicated": data.get('video_syndicated'),
        "video_type": data.get('video_type'),
        "status": "pending",
        "created_at": datetime.datetime.now().isoformat(),
        "results": None,
        "error": None,
    }

    _tasks[task_id] = task
    return task


def list_tasks():
    return list(_tasks.values())


def get_task(task_id: str) -> Optional[dict]:
    return _tasks.get(task_id)


def delete_task(task_id: str) -> Optional[dict]:
    return _tasks.pop(task_id, None)


def mark_task_completed(task_id: str, results: dict):
    task = _tasks[task_id]
    task['status'] = 'completed'
    task['results'] = results
    task['completed_at'] = datetime.datetime.now().isoformat()
    task['error'] = None


def mark_task_failed(task_id: str, error_msg: str):
    task = _tasks[task_id]
    task['status'] = 'failed'
    task['error'] = error_msg
    task['failed_at'] = datetime.datetime.now().isoformat()
