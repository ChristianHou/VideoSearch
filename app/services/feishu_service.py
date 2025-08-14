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
                                 execution_time: str, total_count: int) -> bool:
        """
        发送定时任务执行结果到飞书群聊
        
        Args:
            task_name: 任务名称
            videos: 视频信息列表
            execution_time: 执行时间
            total_count: 总视频数量
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 构建消息内容
            message_content = self._build_message_content(task_name, videos, execution_time, total_count)
            
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
                             execution_time: str, total_count: int) -> Dict[str, Any]:
        """
        构建飞书消息内容
        
        Args:
            task_name: 任务名称
            videos: 视频信息列表
            execution_time: 执行时间
            total_count: 总视频数量
            
        Returns:
            Dict: 飞书消息内容
        """
        # 构建视频列表
        video_list = []

        for video in videos:
            # 构建list_content：视频简介 + 作者 + 时长 + 发布时间
            list_content_parts = []
            
            # 添加视频简介（限制长度）
            if video.description:
                desc = video.description
                list_content_parts.append(f"**简介**: {desc}")
            
            # 添加作者
            if video.channel_title:
                list_content_parts.append(f"**作者**: {video.channel_title}")
            
            # 添加时长
            if video.duration:
                list_content_parts.append(f"**时长**: {video.duration}")
            
            # 添加发布时间
            if video.published_at:
                published_str = video.published_at.strftime("%Y-%m-%d %H:%M")
                list_content_parts.append(f"**发布时间**: {published_str}")
            
            # 添加视频URL
            video_url = f"https://www.youtube.com/watch?v={video.video_id}"
            list_content_parts.append(f"**视频URL**: [点击查看视频]({video_url})")

            list_content = "\n".join(list_content_parts)
            
            # 构建缩略图URL
            # img_key = ""
            # if video.thumbnails:
            #     # 优先使用中等质量的缩略图
            #     if 'medium' in video.thumbnails:
            #         img_key = video.thumbnails['medium']['url']
            #     elif 'default' in video.thumbnails:
            #         img_key = video.thumbnails['default']['url']
            #     elif 'high' in video.thumbnails:
            #         img_key = video.thumbnails['high']['url']
            
            # 获取双语标题
            title = video.title or "无标题"
            bilingual_title = title
            
            # 尝试获取翻译服务来创建双语标题
            try:
                from .translate_service import get_translate_service
                translate_service = get_translate_service()
                if translate_service:
                    # 翻译标题
                    translated_title = translate_service.translate_text(title)
                    if translated_title:
                        bilingual_title = translate_service.create_bilingual_text(title, translated_title)
            except Exception as e:
                print(f"获取双语标题时出错: {e}")
            
            video_item = {
                "list_content": list_content,
                # "img": {
                #     "img_key": img_key
                # },
                "title": f"### {bilingual_title}",
            }
            video_list.append(video_item)
        
        # 构建完整的消息内容
        message_content = {
            "type": "template",
            "data": {
                "template_id": "AAqzzWk1aK7zl",
                "template_variable": {
                    "object_img": video_list
                }
            }
        }
        
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
