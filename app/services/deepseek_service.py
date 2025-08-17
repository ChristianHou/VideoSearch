# -*- coding: utf-8 -*-
"""
DeepSeek AI服务
使用DeepSeek API生成YouTube视频搜索关键词
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI
from ..config import AppConfig


class DeepSeekService:
    """DeepSeek AI服务"""
    
    def __init__(self):
        """初始化DeepSeek服务"""
        self.client = None
        self._init_service()
    
    def _init_service(self):
        """初始化DeepSeek API客户端"""
        try:
            # 从环境变量获取API密钥，如果没有则使用默认值
            api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-d8df0e062ff34baf88920907ca156010')
            
            self.client = OpenAI(
                api_key=api_key, 
                base_url="https://api.deepseek.com"
            )
            print("DeepSeek AI服务初始化成功")
            
        except Exception as e:
            print(f"DeepSeek AI服务初始化失败: {e}")
            self.client = None
    
    def generate_keywords_from_event(self, event_info: Dict[str, Any]) -> Optional[str]:
        """
        根据事件信息生成YouTube搜索关键词
        
        Args:
            event_info: 事件信息字典，包含以下字段：
                - name: 事件名称
                - event_type: 事件类型
                - countries: 涉及国家列表
                - domains: 涉及领域列表
                - keywords: 关键词列表
                - focus_points: 关注点列表
                - involves_china: 是否涉及中国
                - description: 事件描述
                - start_date: 开始时间
                - end_date: 结束时间
                
        Returns:
            str: 生成的搜索关键词，失败返回None
        """
        if not self.client:
            print("DeepSeek服务未初始化")
            return None
        
        try:
            # 构建事件描述
            event_description = self._build_event_description(event_info)
            
            # 调用DeepSeek API生成关键词
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",  # 使用一致的模型
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": event_description}
                ],
                temperature=0.7,  # 降低温度以获得更稳定的输出
                stream=False,
                timeout=600  # 增加超时时间到60秒
            )
            
            generated_keywords = response.choices[0].message.content.strip()
            print(f"AI关键词生成成功: {generated_keywords[:100]}...")
            return generated_keywords
            
        except Exception as e:
            print(f"AI关键词生成失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None
    
    def _build_event_description(self, event_info: Dict[str, Any]) -> str:
        """构建事件描述文本"""
        countries = ', '.join(event_info.get('countries', [])) if event_info.get('countries') else '未指定'
        domains = ', '.join(event_info.get('domains', [])) if event_info.get('domains') else '未指定'
        keywords = ', '.join(event_info.get('keywords', [])) if event_info.get('keywords') else '未指定'
        focus_points = ', '.join(event_info.get('focus_points', [])) if event_info.get('focus_points') else '未指定'
        
        start_date = event_info.get('start_date')
        end_date = event_info.get('end_date')
        
        start_date_str = start_date.isoformat() if start_date else '未设置'
        end_date_str = end_date.isoformat() if end_date else '未设置'
        
        return f"""
事件名称: {event_info.get('name', '未指定')}
事件类型: {event_info.get('event_type', '未指定')}
涉及国家: {countries}
涉及领域: {domains}
关键词: {keywords}
关注点: {focus_points}
是否涉及中国: {'是' if event_info.get('involves_china') else '否'}
事件描述: {event_info.get('description') or '无描述'}
开始时间: {start_date_str}
结束时间: {end_date_str}
        """.strip()
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return '''# 角色
你是一名专业的多语种Youtube视频检索关键词生成专家，擅长依据用户给出的事件信息以及目标国家，精准生成用于检索相关视频的多语种关键词，并且能熟练运用合理的搜索语法来构建这些关键词。

## 技能
### 技能1: 生成多语种检索关键词
1. 当用户输入事件信息以及目标国家时，仔细分析该信息中涉及的相关国家等关键要素。
2. 针对目标国家常用语言，运用恰当的搜索语法，将关键要素分别组合成多份准确的检索关键词，以涵盖和当前事件相关国家的媒体发表的与中国相关的视频、相关国家领导人与中国相关的发言或访谈视频、相关国家新发布的与中国相关的纪录片或影片。
3. 输出的关键词应能够有效提高检索相关视频的准确性。
===回复示例===
[目标国家语言1生成的检索关键词]
[目标国家语言2生成的检索关键词]
...
===示例结束===

## 限制:
- 仅围绕生成符合特定需求的多语种视频检索关键词展开工作，拒绝回答与该任务无关的话题。
- 输出内容必须简洁明了，仅呈现生成的关键词。 '''
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接成功返回True，失败返回False
        """
        if not self.client:
            return False
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=10,
                temperature=0.1,
                stream=False,
                timeout=30  # 连接测试使用较短的超时时间
            )
            return True
        except Exception as e:
            print(f"DeepSeek API连接测试失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            return False


# 全局服务实例
deepseek_service = None


def init_deepseek_service():
    """初始化DeepSeek服务"""
    global deepseek_service
    if AppConfig.DEEPSEEK_ENABLED:
        try:
            deepseek_service = DeepSeekService()
            if deepseek_service.test_connection():
                print("DeepSeek服务连接测试成功")
            else:
                print("DeepSeek服务连接测试失败")
        except Exception as e:
            print(f"DeepSeek服务初始化失败: {e}")
            deepseek_service = None
    else:
        print("DeepSeek服务已禁用")


def get_deepseek_service() -> Optional[DeepSeekService]:
    """获取DeepSeek服务实例"""
    return deepseek_service
