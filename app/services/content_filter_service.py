# -*- coding: utf-8 -*-
"""
内容过滤服务
用于过滤定时任务中的新内容，避免重复推送
"""

from typing import List, Dict, Any, Tuple
from ..database import db_manager
from ..models import VideoInfo, ScheduledTask, ScheduledExecutionResult
from datetime import datetime, timedelta


class ContentFilterService:
    """内容过滤服务"""
    
    def __init__(self):
        pass
    
    def filter_new_videos(self, scheduled_task_id: int, search_results: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """
        过滤新视频内容
        
        Args:
            scheduled_task_id: 定时任务ID
            search_results: YouTube API搜索结果
            
        Returns:
            Tuple[List[Dict], List[Dict]]: (新视频列表, 所有视频列表)
        """
        if not search_results or 'items' not in search_results:
            return [], []
        
        db = db_manager.get_session()
        try:
            # 获取定时任务信息
            scheduled_task = db.query(ScheduledTask).filter_by(id=scheduled_task_id).first()
            if not scheduled_task:
                return [], search_results['items']
            
            # 获取该定时任务之前的所有执行结果
            previous_executions = db.query(ScheduledExecutionResult).filter(
                ScheduledExecutionResult.scheduled_task_id == scheduled_task_id,
                ScheduledExecutionResult.status == 'success'
            ).order_by(ScheduledExecutionResult.completed_at.desc()).all()
            
            # 收集之前所有执行过的视频ID
            previous_video_ids = set()
            for execution in previous_executions:
                if execution.result_data and 'items' in execution.result_data:
                    for item in execution.result_data['items']:
                        video_id = item.get('id', {}).get('videoId')
                        if video_id:
                            previous_video_ids.add(video_id)
            
            # 过滤新视频
            new_videos = []
            all_videos = search_results['items']
            
            for video in all_videos:
                video_id = video.get('id', {}).get('videoId')
                if video_id and video_id not in previous_video_ids:
                    new_videos.append(video)
            
            print(f"定时任务 {scheduled_task_id} 过滤结果:")
            print(f"  总视频数: {len(all_videos)}")
            print(f"  新视频数: {len(new_videos)}")
            print(f"  重复视频数: {len(all_videos) - len(new_videos)}")
            
            return new_videos, all_videos
            
        finally:
            db.close()
    
    def get_task_execution_summary(self, scheduled_task_id: int) -> Dict[str, Any]:
        """
        获取定时任务执行摘要
        
        Args:
            scheduled_task_id: 定时任务ID
            
        Returns:
            Dict: 执行摘要信息
        """
        db = db_manager.get_session()
        try:
            # 获取定时任务信息
            scheduled_task = db.query(ScheduledTask).filter_by(id=scheduled_task_id).first()
            if not scheduled_task:
                return {}
            
            # 获取执行历史
            executions = db.query(ScheduledExecutionResult).filter(
                ScheduledExecutionResult.scheduled_task_id == scheduled_task_id
            ).order_by(ScheduledExecutionResult.completed_at.desc()).all()
            
            # 统计信息
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.status == 'success'])
            failed_executions = len([e for e in executions if e.status == 'failed'])
            
            # 获取最新执行结果
            latest_execution = executions[0] if executions else None
            latest_new_videos = 0
            latest_total_videos = 0
            
            if latest_execution and latest_execution.status == 'success':
                latest_total_videos = latest_execution.videos_count or 0
                # 计算新视频数量（这里简化处理，实际应该调用filter_new_videos）
                latest_new_videos = latest_total_videos
            
            return {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'latest_execution': {
                    'status': latest_execution.status if latest_execution else None,
                    'started_at': latest_execution.started_at.isoformat() if latest_execution else None,
                    'completed_at': latest_execution.completed_at.isoformat() if latest_execution else None,
                    'total_videos': latest_total_videos,
                    'new_videos': latest_new_videos
                } if latest_execution else None
            }
            
        finally:
            db.close()


# 单例服务
content_filter_service = ContentFilterService()
