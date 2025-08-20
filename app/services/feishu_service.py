# -*- coding: utf-8 -*-
"""
飞书消息服务
用于发送定时任务执行结果到指定的飞书群聊
"""

import json
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from typing import List, Dict, Any
from ..models import VideoInfo


class FeishuService:
    """飞书消息服务"""
    
    def __init__(self, app_id: str, app_secret: str, chat_id: str):
        """
        初始化飞书服务
        
        Args:
            app_id: 飞书应用的APP_ID
            app_secret: 飞书应用的APP_SECRET
            chat_id: 目标群聊的chat_id
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.chat_id = chat_id
        self.client = None
        
    def _get_client(self):
        """获取飞书客户端"""
        if not self.client:
            self.client = lark.Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .log_level(lark.LogLevel.INFO) \
                .build()
        return self.client
    
    def send_task_execution_result(self, task_name: str, videos: List[VideoInfo], 
                                 execution_time: str, total_count: int, new_count: int = None) -> bool:
        """
        发送定时任务执行结果到飞书群聊
        
        Args:
            task_name: 任务名称
            videos: 视频信息列表
            execution_time: 执行时间
            total_count: 总视频数量
            new_count: 新视频数量（可选）
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 构建消息内容
            message_content = self._build_message_content(task_name, videos, execution_time, total_count, new_count)
            
            # 发送消息
            client = self._get_client()
            request = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(CreateMessageRequestBody.builder()
                    .receive_id(self.chat_id)
                    .msg_type("interactive")
                    .content(json.dumps(message_content, ensure_ascii=False))
                    .build()) \
                .build()
            
            response = client.im.v1.message.create(request)
            
            if not response.success():
                print(f"发送飞书消息失败: {response.code}, {response.msg}")
                return False
            
            print(f"飞书消息发送成功，消息ID: {response.data.message_id}")
            return True
            
        except Exception as e:
            print(f"发送飞书消息时出错: {e}")
            return False
    
    def _build_message_content(self, task_name: str, videos: List[VideoInfo], 
                             execution_time: str, total_count: int, new_count: int = None) -> Dict[str, Any]:
        """
        构建飞书消息内容
        
        Args:
            task_name: 任务名称
            videos: 视频信息列表
            execution_time: 执行时间
            total_count: 总视频数量
            new_count: 新视频数量（可选）
            
        Returns:
            Dict: 飞书消息内容
        """
        # 构建消息标题
        title = f"📺 {task_name} - 定时任务执行完成"
        if new_count is not None and new_count > 0:
            title += f" (发现 {new_count} 个新视频)"
        elif new_count == 0:
            title += " (无新内容)"
        
        # 构建视频列表
        video_elements = []
        
        for i, video in enumerate(videos[:10]):  # 限制显示前10个视频，避免消息过长
            # 构建视频标题（支持双语）
            video_title = video.title or "无标题"
            if video.translated_title:
                video_title = f"{video_title}\n{video.translated_title}"
            
            # 构建视频描述（支持双语）
            video_description = video.description or "无描述"
            if len(video_description) > 200:  # 限制描述长度
                video_description = video_description[:200] + "..."
            
            if video.translated_description:
                video_description = f"{video_description}\n{video.translated_description}"
            
            # 构建发布时间
            published_time = "未知时间"
            if video.published_at:
                published_time = video.published_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # 构建视频链接
            video_url = f"https://www.youtube.com/watch?v={video.video_id}"
            
            # 构建视频信息卡片
            video_card = {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{i+1}. {video_title}**\n\n"
                              f"👤 **作者**: {video.channel_title or '未知'}\n"
                              f"📅 **发布时间**: {published_time}\n"
                              f"👁️ **观看次数**: {video.view_count:,}\n"
                              f"👍 **点赞数**: {video.like_count:,}\n"
                              f"💬 **评论数**: {video.comment_count:,}\n\n"
                              f"📝 **简介**: {video_description}\n\n"
                              f"🔗 **链接**: {video_url}"
                }
            }
            
            video_elements.append(video_card)
            
            # 添加分隔线（除了最后一个视频）
            if i < len(videos[:10]) - 1:
                video_elements.append({
                    "tag": "hr"
                })
        
        # 构建消息内容
        message_content = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**执行时间**: {execution_time}\n**总视频数**: {total_count}\n**新视频数**: {new_count or total_count}"
                    }
                },
                {
                    "tag": "hr"
                }
            ]
        }
        
        # 添加视频列表
        if video_elements:
            message_content["elements"].extend(video_elements)
        else:
            message_content["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "暂无视频信息"
                }
            })
        
        # 如果视频数量超过10个，添加提示
        if len(videos) > 10:
            message_content["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"*注：仅显示前10个视频，共{len(videos)}个视频*"
                }
            })
        
        return message_content


# 全局飞书服务实例
feishu_service = None


def init_feishu_service(app_id: str, app_secret: str, chat_id: str):
    """初始化全局飞书服务"""
    global feishu_service
    feishu_service = FeishuService(app_id, app_secret, chat_id)
    print(f"飞书服务已初始化，目标群聊: {chat_id}")


def get_feishu_service() -> FeishuService:
    """获取全局飞书服务实例"""
    return feishu_service
