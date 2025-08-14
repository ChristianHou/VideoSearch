# -*- coding: utf-8 -*-
"""
翻译服务
使用火山引擎翻译API将视频标题和简介翻译成中文
"""

import json
import re
from typing import List, Dict, Any, Optional
from volcengine.ApiInfo import ApiInfo
from volcengine.Credentials import Credentials
from volcengine.ServiceInfo import ServiceInfo
from volcengine.base.Service import Service
from ..config import AppConfig


class TranslateService:
    """翻译服务"""
    
    def __init__(self):
        """初始化翻译服务"""
        self.service = None
        self._init_service()
    
    def _init_service(self):
        """初始化火山引擎翻译服务"""
        try:
            k_service_info = ServiceInfo(
                'translate.volcengineapi.com',
                {'Content-Type': 'application/json'},
                Credentials(
                    AppConfig.VOLC_ACCESS_KEY, 
                    AppConfig.VOLC_SECRET_KEY, 
                    'translate', 
                    'cn-north-1'
                ),
                5, 5
            )
            
            k_query = {
                'Action': 'TranslateText',
                'Version': '2020-06-01'
            }
            
            k_api_info = {
                'translate': ApiInfo('POST', '/', k_query, {}, {})
            }
            
            self.service = Service(k_service_info, k_api_info)
            print("火山引擎翻译服务初始化成功")
            
        except Exception as e:
            print(f"火山引擎翻译服务初始化失败: {e}")
            self.service = None
    
    def translate_text(self, text: str, target_language: str = 'zh') -> Optional[str]:
        """
        翻译单个文本
        
        Args:
            text: 要翻译的文本
            target_language: 目标语言，默认为中文
            
        Returns:
            str: 翻译后的文本，失败返回None
        """
        if not text or not self.service:
            return None
        
        try:
            # 检测文本语言，如果是中文则跳过翻译
            if self._is_chinese_text(text):
                return text
            
            body = {
                'TargetLanguage': target_language,
                'TextList': [text],
            }
            
            response = self.service.json('translate', {}, json.dumps(body))
            result = json.loads(response)
            
            if 'TranslationList' in result and len(result['TranslationList']) > 0:
                translated_text = result['TranslationList'][0].get('Translation', '')
                print(f"翻译成功: '{text}' -> '{translated_text}'")
                return translated_text
            else:
                print(f"翻译失败: {result}")
                return None
                
        except Exception as e:
            print(f"翻译文本时出错: {e}")
            return None
    
    def translate_texts(self, texts: List[str], target_language: str = 'zh') -> List[Optional[str]]:
        """
        批量翻译文本列表
        
        Args:
            texts: 要翻译的文本列表
            target_language: 目标语言，默认为中文
            
        Returns:
            List[Optional[str]]: 翻译后的文本列表，失败的项目为None
        """
        if not texts or not self.service:
            return [None] * len(texts)
        
        try:
            # 过滤掉空文本和中文文本
            valid_texts = []
            text_indices = []
            
            for i, text in enumerate(texts):
                if text and not self._is_chinese_text(text):
                    valid_texts.append(text)
                    text_indices.append(i)
            
            if not valid_texts:
                return [None] * len(texts)
            
            body = {
                'TargetLanguage': target_language,
                'TextList': valid_texts,
            }
            
            response = self.service.json('translate', {}, json.dumps(body))
            result = json.loads(response)
            
            # 构建结果列表
            results = [None] * len(texts)
            
            if 'TranslationList' in result:
                for i, translation_item in enumerate(result['TranslationList']):
                    original_index = text_indices[i]
                    translated_text = translation_item.get('Translation', '')
                    results[original_index] = translated_text
                    
                    if i < len(valid_texts):
                        print(f"批量翻译成功: '{valid_texts[i]}' -> '{translated_text}'")
            
            return results
                
        except Exception as e:
            print(f"批量翻译文本时出错: {e}")
            return [None] * len(texts)
    
    def _is_chinese_text(self, text: str) -> bool:
        """
        检测文本是否为中文
        
        Args:
            text: 要检测的文本
            
        Returns:
            bool: 是否为中文文本
        """
        if not text:
            return False
        
        # 中文字符的Unicode范围
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        return bool(chinese_pattern.search(text))
    
    def create_bilingual_text(self, original_text: str, translated_text: str = None) -> str:
        """
        创建双语文本格式
        
        Args:
            original_text: 原始文本
            translated_text: 翻译后的文本
            
        Returns:
            str: 双语格式的文本
        """
        if not original_text:
            return ""
        
        if not translated_text:
            return original_text
        
        # 如果原文已经是中文，直接返回
        if self._is_chinese_text(original_text):
            return original_text
        
        # 创建"中文（英文）"格式
        return f"{translated_text}（{original_text}）"
    
    def translate_video_info(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        翻译视频信息
        
        Args:
            video_data: 包含视频信息的字典
            
        Returns:
            Dict[str, Any]: 包含双语信息的视频数据
        """
        if not video_data:
            return video_data
        
        try:
            # 提取需要翻译的字段
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            
            # 翻译标题和描述
            translated_title = self.translate_text(title) if title else None
            translated_description = self.translate_text(description) if description else None
            
            # 创建双语版本
            bilingual_title = self.create_bilingual_text(title, translated_title)
            bilingual_description = self.create_bilingual_text(description, translated_description)
            
            # 更新视频数据
            result = video_data.copy()
            result['bilingual_title'] = bilingual_title
            result['bilingual_description'] = bilingual_description
            result['translated_title'] = translated_title
            result['translated_description'] = translated_description
            
            return result
            
        except Exception as e:
            print(f"翻译视频信息时出错: {e}")
            return video_data
    
    def translate_video_list(self, video_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量翻译视频列表
        
        Args:
            video_list: 视频信息列表
            
        Returns:
            List[Dict[str, Any]]: 包含双语信息的视频列表
        """
        if not video_list:
            return video_list
        
        try:
            # 提取所有需要翻译的文本
            titles = [video.get('title', '') for video in video_list]
            descriptions = [video.get('description', '') for video in video_list]
            
            # 批量翻译
            translated_titles = self.translate_texts(titles)
            translated_descriptions = self.translate_texts(descriptions)
            
            # 更新每个视频的信息
            result = []
            for i, video in enumerate(video_list):
                bilingual_video = video.copy()
                
                # 创建双语版本
                bilingual_video['bilingual_title'] = self.create_bilingual_text(
                    titles[i], translated_titles[i]
                )
                bilingual_video['bilingual_description'] = self.create_bilingual_text(
                    descriptions[i], translated_descriptions[i]
                )
                bilingual_video['translated_title'] = translated_titles[i]
                bilingual_video['translated_description'] = translated_descriptions[i]
                
                result.append(bilingual_video)
            
            return result
            
        except Exception as e:
            print(f"批量翻译视频列表时出错: {e}")
            return video_list


# 全局翻译服务实例
translate_service = None


def init_translate_service():
    """初始化全局翻译服务"""
    global translate_service
    try:
        translate_service = TranslateService()
        print("翻译服务已初始化")
    except Exception as e:
        print(f"翻译服务初始化失败: {e}")


def get_translate_service() -> TranslateService:
    """获取全局翻译服务实例"""
    return translate_service
