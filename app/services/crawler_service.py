#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    print("警告: crawl4ai 未安装，将使用备用爬虫方案")

from ..services.translate_service import get_translate_service

logger = logging.getLogger(__name__)

class CrawlerService:
    """视频爬虫服务"""
    
    def __init__(self):
        self.translate_service = get_translate_service()
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def crawl_website(self, website_url: str, crawl_config: Dict) -> List[Dict]:
        """
        爬取网站视频信息
        
        Args:
            website_url: 网站URL
            crawl_config: 爬取配置
            
        Returns:
            视频信息列表
        """
        try:
            logger.info(f"开始爬取网站: {website_url}")
            
            # 使用 crawl4ai 进行爬取
            if CRAWL4AI_AVAILABLE:
                videos = await self._crawl_with_crawl4ai(website_url, crawl_config)
            else:
                # 备用方案：使用传统方法
                videos = await self._crawl_traditional(website_url, crawl_config)
            
            # 翻译视频信息
            if crawl_config.get('enable_translation', True):
                videos = self._translate_videos(videos)
            
            logger.info(f"爬取完成，共获取 {len(videos)} 个视频")
            return videos
            
        except Exception as e:
            logger.error(f"爬取网站失败: {website_url}, 错误: {str(e)}")
            return []
    
    async def _crawl_with_crawl4ai(self, website_url: str, crawl_config: Dict) -> List[Dict]:
        """使用 crawl4ai 爬取网站"""
        try:
            logger.info(f"使用 crawl4ai 爬取网站: {website_url}")
            
            # 创建 AsyncWebCrawler 实例
            crawler = AsyncWebCrawler()
            logger.info("AsyncWebCrawler 实例创建成功")
            
            # 方法1: 最简单的爬取配置 - 获取HTML内容
            logger.info("尝试方法1: 获取HTML内容")
            try:
                result = await crawler.arun(
                    url=website_url,
                    extraction_rules={
                        "selector": "html",
                        "type": "html"
                    }
                )
                
                if result and hasattr(result, '_results') and result._results:
                    logger.info(f"crawl4ai 方法1执行成功，结果类型: {type(result)}")
                    logger.info(f"结果属性: {[attr for attr in dir(result) if not attr.startswith('_')]}")
                    
                    # 检查结果内容
                    if hasattr(result, 'html') and result.html:
                        logger.info("找到HTML内容，使用传统方法解析")
                        # 使用BeautifulSoup解析HTML内容
                        soup = BeautifulSoup(result.html, 'html.parser')
                        videos = await self._auto_parse_videos(soup, website_url)
                        if videos:
                            logger.info(f"传统方法解析成功，找到 {len(videos)} 个视频")
                            return videos
                    
                    # 如果没有html属性，尝试其他属性
                    for attr in ['body', 'content', 'text']:
                        if hasattr(result, attr) and getattr(result, attr):
                            logger.info(f"找到 {attr} 内容，使用传统方法解析")
                            content = getattr(result, attr)
                            if isinstance(content, str):
                                soup = BeautifulSoup(content, 'html.parser')
                                videos = await self._auto_parse_videos(soup, website_url)
                                if videos:
                                    logger.info(f"传统方法解析成功，找到 {len(videos)} 个视频")
                                    return videos
                
                logger.info("方法1未找到有效内容，尝试方法2")
                
            except Exception as e:
                logger.warning(f"crawl4ai 方法1失败: {str(e)}")
            
            # 方法2: 使用更复杂的爬取配置
            logger.info("尝试方法2: 使用更复杂的爬取配置")
            try:
                # 构建提取规则
                extraction_rules = {
                    "videos": {
                        "selector": crawl_config.get('video_selector', 'video, iframe[src*="youtube"], iframe[src*="vimeo"], div[class*="video"], div[class*="player"]'),
                        "type": "elements"
                    },
                    "titles": {
                        "selector": crawl_config.get('title_selector', 'h1, h2, h3, h4, h5, h6, .title, .video-title, [class*="title"]'),
                        "type": "text"
                    },
                    "links": {
                        "selector": crawl_config.get('link_selector', 'a[href], iframe[src]'),
                        "type": "attributes",
                        "attribute": "href"
                    },
                    "descriptions": {
                        "selector": crawl_config.get('description_selector', 'p, .description, .video-description, [class*="desc"]'),
                        "type": "text"
                    }
                }
                
                result = await crawler.arun(
                    url=website_url,
                    extraction_rules=extraction_rules
                )
                
                if result and hasattr(result, '_results') and result._results:
                    logger.info(f"crawl4ai 方法2爬取完成，结果类型: {type(result)}")
                    
                    # 尝试从结果中提取视频信息
                    videos = []
                    if hasattr(result, 'videos') and result.videos:
                        logger.info(f"找到 {len(result.videos)} 个视频元素")
                        for video_elem in result.videos:
                            video_info = await self._extract_video_info(video_elem, website_url)
                            if video_info:
                                videos.append(video_info)
                    
                    if videos:
                        logger.info(f"方法2成功提取 {len(videos)} 个视频")
                        return videos
                    
                    logger.info("方法2未找到视频，尝试方法3")
                
            except Exception as e:
                logger.warning(f"crawl4ai 方法2失败: {str(e)}")
            
            # 方法3: 获取原始HTML并使用传统方法解析
            logger.info("尝试方法3: 获取原始HTML并使用传统方法解析")
            try:
                result = await crawler.arun(
                    url=website_url,
                    extraction_rules={
                        "selector": "body",
                        "type": "html"
                    }
                )
                
                if result and hasattr(result, 'body') and result.body:
                    logger.info("找到body内容，使用传统方法解析")
                    soup = BeautifulSoup(result.body, 'html.parser')
                    videos = await self._auto_parse_videos(soup, website_url)
                    if videos:
                        logger.info(f"传统方法解析成功，找到 {len(videos)} 个视频")
                        return videos
                
            except Exception as e:
                logger.warning(f"crawl4ai 方法3失败: {str(e)}")
            
            logger.warning("所有 crawl4ai 方法都失败，回退到传统方法")
            return []
            
        except Exception as e:
            logger.error(f"crawl4ai 爬取失败: {str(e)}")
            return []

    async def _crawl_traditional(self, website_url: str, crawl_config: Dict) -> List[Dict]:
        """使用传统方法进行爬取（备用方案）"""
        try:
            logger.info(f"使用传统方法爬取网站: {website_url}")
            
            # 获取网站内容
            html_content = await self._fetch_website_content(website_url)
            if not html_content:
                logger.error(f"无法获取网站内容: {website_url}")
                return []
            
            # 解析视频信息
            videos = await self._parse_videos(html_content, website_url, crawl_config)
            
            return videos
            
        except Exception as e:
            logger.error(f"传统爬取方法失败: {str(e)}")
            return []

    async def _fetch_website_content(self, url: str) -> Optional[str]:
        """获取网站HTML内容"""
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"HTTP请求失败: {url}, 状态码: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"获取网站内容失败: {url}, 错误: {str(e)}")
            return None
    
    async def _parse_videos(self, html_content: str, base_url: str, crawl_config: Dict) -> List[Dict]:
        """解析HTML中的视频信息"""
        videos = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 根据配置选择解析策略
        parse_strategy = crawl_config.get('parse_strategy', 'auto')
        
        if parse_strategy == 'auto':
            videos = await self._auto_parse_videos(soup, base_url)
        elif parse_strategy == 'custom':
            videos = await self._custom_parse_videos(soup, base_url, crawl_config)
        
        return videos
    
    async def _auto_parse_videos(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """自动解析视频信息"""
        videos = []
        
        # 1. 首先查找所有视频相关标签（任何网站都应该优先查找）
        logger.info("优先查找视频相关标签")
        video_selectors = [
            'video', 'iframe[src*="youtube"]', 'iframe[src*="vimeo"]', 'iframe[src*="bilibili"]',
            'iframe[src*="player"]', 'iframe[src*="embed"]', 'iframe[src*="watch"]',
            'div[class*="video"]', 'div[class*="player"]', 'div[class*="media"]',
            'a[href*="video"]', 'a[href*="watch"]', 'a[href*="play"]',
            'object[type*="video"]', 'embed[type*="video"]',
            '[data-type="video"]', '[data-video]', '[class*="video-player"]'
        ]
        
        for selector in video_selectors:
            elements = soup.select(selector)
            for element in elements:
                video_info = await self._extract_video_info(element, base_url)
                if video_info:
                    videos.append(video_info)
                    logger.info(f"找到视频元素: {video_info.get('video_title', 'Unknown')}")
        
        # 2. 如果找到视频，直接返回
        if videos:
            logger.info(f"找到 {len(videos)} 个视频元素，返回结果")
            # 去重
            unique_videos = []
            seen_urls = set()
            for video in videos:
                if video['video_url'] not in seen_urls:
                    unique_videos.append(video)
                    seen_urls.add(video['video_url'])
            return unique_videos
        
        # 3. 如果没有找到视频，针对特定网站使用专门逻辑
        if 'mnb.mn' in base_url:
            logger.info("未找到视频元素，使用蒙古国家广播电视网站特定解析逻辑")
            videos = self._parse_mnb_mn_content(soup, base_url)
            if videos:
                logger.info(f"蒙古网站特定解析找到 {len(videos)} 个内容项")
                return videos
        
        # 4. 对于其他网站，尝试查找媒体内容
        logger.info("未找到视频元素，尝试查找其他媒体内容")
        media_selectors = [
            'img[src*="video"]', 'img[src*="thumb"]', 'img[src*="preview"]',
            'div[class*="media"]', 'div[class*="content"]', 'div[class*="item"]',
            'article', 'section', '.post', '.entry'
        ]
        
        for selector in media_selectors:
            elements = soup.select(selector)
            for element in elements:
                # 尝试从媒体元素中提取信息
                media_info = self._extract_media_info(element, base_url)
                if media_info:
                    videos.append(media_info)
        
        # 5. 如果仍然没有找到内容，尝试提取页面基本信息
        if not videos:
            logger.info("尝试提取页面基本信息")
            videos = self._extract_basic_page_info(soup, base_url)
        
        # 去重
        unique_videos = []
        seen_titles = set()
        for video in videos:
            title = video.get('video_title', '')
            if title and title not in seen_titles:
                unique_videos.append(video)
                seen_titles.add(title)
        
        logger.info(f"最终找到 {len(unique_videos)} 个内容项")
        return unique_videos
    
    def _extract_basic_page_info(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """提取页面基本信息"""
        videos = []
        
        try:
            # 提取页面标题
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text(strip=True)
                if title_text and len(title_text) > 5:
                    videos.append({
                        'video_title': title_text,
                        'video_url': base_url,
                        'video_description': f"页面标题: {title_text}",
                        'thumbnail_url': '',
                        'duration': '',
                        'upload_date': '',
                        'view_count': '',
                        'like_count': '',
                        'language': 'auto',
                        'content_type': 'page_title'
                    })
            
            # 提取主要标题
            for i in range(1, 7):
                headings = soup.find_all(f'h{i}')
                for heading in headings[:3]:  # 只取前3个
                    heading_text = heading.get_text(strip=True)
                    if heading_text and len(heading_text) > 5:
                        videos.append({
                            'video_title': heading_text,
                            'video_url': base_url,
                            'video_description': f"标题 {i}: {heading_text}",
                            'thumbnail_url': '',
                            'duration': '',
                            'upload_date': '',
                            'view_count': '',
                            'like_count': '',
                            'language': 'auto',
                            'content_type': f'heading_h{i}'
                        })
            
            # 提取主要链接
            main_links = soup.find_all('a', href=True)
            link_count = 0
            for link in main_links:
                if link_count >= 5:  # 限制数量
                    break
                    
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                
                if (href and link_text and len(link_text) > 5 and 
                    not href.startswith('#') and 
                    not href.startswith('javascript:') and
                    href != base_url):
                    
                    full_url = urljoin(base_url, href)
                    videos.append({
                        'video_title': link_text,
                        'video_url': full_url,
                        'video_description': f"链接: {link_text}",
                        'thumbnail_url': '',
                        'duration': '',
                        'upload_date': '',
                        'view_count': '',
                        'like_count': '',
                        'language': 'auto',
                        'content_type': 'main_link'
                    })
                    link_count += 1
            
            logger.info(f"提取页面基本信息完成，找到 {len(videos)} 个内容项")
            
        except Exception as e:
            logger.error(f"提取页面基本信息失败: {str(e)}")
        
        return videos
    
    def _parse_mnb_mn_content(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """解析蒙古国家广播电视网站内容"""
        videos = []
        
        try:
            # 1. 优先查找直播和视频相关内容
            logger.info("查找直播和视频相关内容")
            
            # 查找直播相关元素
            live_selectors = [
                'div[class*="live"]', 'div[class*="stream"]', 'div[class*="broadcast"]',
                'div[class*="tv"]', 'div[class*="radio"]', 'div[class*="channel"]',
                'iframe[src*="live"]', 'iframe[src*="stream"]', 'iframe[src*="tv"]',
                'video', 'audio', 'embed[type*="video"]', 'embed[type*="audio"]',
                'object[type*="video"]', 'object[type*="audio"]'
            ]
            
            for selector in live_selectors:
                elements = soup.select(selector)
                for element in elements:
                    video_info = self._extract_media_info(element, base_url)
                    if video_info:
                        videos.append(video_info)
            
            # 2. 查找节目时间表和新闻内容
            logger.info("查找节目时间表和新闻内容")
            
            # 查找所有可能的新闻和节目链接
            news_selectors = [
                'a[href*="/news"]', 'a[href*="/program"]', 'a[href*="/live"]',
                'a[href*="/tv"]', 'a[href*="/radio"]', 'a[href*="/broadcast"]',
                '.news-item', '.program-item', '.live-item', '.tv-item',
                'div[class*="news"]', 'div[class*="program"]', 'div[class*="live"]'
            ]
            
            for selector in news_selectors:
                elements = soup.select(selector)
                for element in elements:
                    video_info = self._extract_media_info(element, base_url)
                    if video_info:
                        videos.append(video_info)
            
            # 3. 查找新闻文章和链接
            logger.info("查找新闻文章和链接")
            
            # 查找所有链接，包括新闻标题
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 过滤掉空链接和导航链接
                if not text or len(text) < 3:
                    continue
                    
                # 检查是否是有效的新闻或节目链接
                if any(keyword in href.lower() for keyword in ['/news', '/program', '/live', '/tv', '/radio', '/broadcast']):
                    video_info = {
                        'video_title': text,
                        'video_url': self._normalize_url(href, base_url),
                        'video_description': text,
                        'thumbnail_url': '',
                        'language': 'mn'
                    }
                    videos.append(video_info)
            
            # 4. 查找主要内容区域
            logger.info("查找主要内容区域")
            
            # 查找主要内容容器
            content_selectors = [
                '.content', '.main-content', '.article', '.post',
                '.news-content', '.program-content', '.live-content'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    # 查找元素内的所有文本内容
                    text_content = element.get_text(strip=True)
                    if len(text_content) > 20:  # 过滤太短的内容
                        video_info = {
                            'video_title': text_content[:100] + '...' if len(text_content) > 100 else text_content,
                            'video_url': base_url,
                            'video_description': text_content,
                            'thumbnail_url': '',
                            'language': 'mn'
                        }
                        videos.append(video_info)
            
            # 5. 查找频道和媒体信息
            logger.info("查找频道和媒体信息")
            
            # 查找频道信息
            channel_selectors = [
                '.channel', '.station', '.frequency', '.program-schedule',
                '[class*="channel"]', '[class*="station"]', '[class*="frequency"]'
            ]
            
            for selector in channel_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text_content = element.get_text(strip=True)
                    if text_content and len(text_content) > 5:
                        video_info = {
                            'video_title': text_content,
                            'video_url': base_url,
                            'video_description': f"频道信息: {text_content}",
                            'thumbnail_url': '',
                            'language': 'mn'
                        }
                        videos.append(video_info)
            
            # 6. 查找时间表信息
            logger.info("查找时间表信息")
            
            # 查找时间表
            schedule_selectors = [
                '.schedule', '.timetable', '.program-list', '.time-slot',
                '[class*="schedule"]', '[class*="timetable"]', '[class*="time"]'
            ]
            
            for selector in schedule_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text_content = element.get_text(strip=True)
                    if text_content and len(text_content) > 10:
                        video_info = {
                            'video_title': f"时间表: {text_content[:50]}...",
                            'video_url': base_url,
                            'video_description': text_content,
                            'thumbnail_url': '',
                            'language': 'mn'
                        }
                        videos.append(video_info)
            
            # 7. 查找所有文本内容，提取有意义的信息
            logger.info("查找所有文本内容")
            
            # 查找所有段落和文本块
            text_selectors = [
                'p', 'div', 'span', 'li', 'td', 'th',
                '[class*="text"]', '[class*="content"]', '[class*="info"]'
            ]
            
            for selector in text_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text_content = element.get_text(strip=True)
                    if text_content and len(text_content) > 15 and len(text_content) < 500:
                        # 过滤掉导航和重复内容
                        if not any(keyword in text_content.lower() for keyword in ['copyright', 'all rights reserved', 'privacy policy', 'terms of service']):
                            video_info = {
                                'video_title': text_content[:80] + '...' if len(text_content) > 80 else text_content,
                                'video_url': base_url,
                                'video_description': text_content,
                                'thumbnail_url': '',
                                'language': 'mn'
                            }
                            videos.append(video_info)
            
            # 8. 查找所有链接，提取新闻和节目信息
            logger.info("查找所有链接信息")
            
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 过滤掉空链接和导航链接
                if not text or len(text) < 3:
                    continue
                    
                # 检查是否是有效的链接
                if (href and not href.startswith('#') and 
                    not href.startswith('javascript:') and
                    len(text) > 5 and len(text) < 200):
                    
                    video_info = {
                        'video_title': text,
                        'video_url': self._normalize_url(href, base_url),
                        'video_description': f"链接: {text}",
                        'thumbnail_url': '',
                        'language': 'mn'
                    }
                    videos.append(video_info)
            
            # 移除重复项，但保留更多内容
            unique_videos = []
            seen_titles = set()
            
            for video in videos:
                title = video.get('video_title', '').strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_videos.append(video)
            
            logger.info(f"蒙古国家广播电视网站解析完成，找到 {len(unique_videos)} 个内容项")
            return unique_videos
            
        except Exception as e:
            logger.error(f"解析蒙古国家广播电视网站内容失败: {str(e)}")
            return []
    
    async def _custom_parse_videos(self, soup: BeautifulSoup, base_url: str, crawl_config: Dict) -> List[Dict]:
        """自定义解析视频信息"""
        videos = []
        
        # 从配置中获取选择器
        container_selector = crawl_config.get('container_selector')
        title_selector = crawl_config.get('title_selector')
        url_selector = crawl_config.get('url_selector')
        description_selector = crawl_config.get('description_selector')
        thumbnail_selector = crawl_config.get('thumbnail_selector')
        
        if not container_selector:
            logger.warning("自定义解析配置不完整，使用自动解析")
            return await self._auto_parse_videos(soup, base_url)
        
        containers = soup.select(container_selector)
        for container in containers:
            video_info = {}
            
            # 提取标题
            if title_selector:
                title_elem = container.select_one(title_selector)
                if title_elem:
                    video_info['video_title'] = title_elem.get_text(strip=True)
            
            # 提取链接
            if url_selector:
                url_elem = container.select_one(url_selector)
                if url_elem:
                    href = url_elem.get('href') or url_elem.get('src')
                    if href:
                        video_info['video_url'] = urljoin(base_url, href)
            
            # 提取描述
            if description_selector:
                desc_elem = container.select_one(description_selector)
                if desc_elem:
                    video_info['video_description'] = desc_elem.get_text(strip=True)
            
            # 提取缩略图
            if thumbnail_selector:
                thumb_elem = container.select_one(thumbnail_selector)
                if thumb_elem:
                    src = thumb_elem.get('src') or thumb_elem.get('data-src')
                    if src:
                        video_info['thumbnail_url'] = urljoin(base_url, src)
            
            # 验证必要字段
            if video_info.get('video_title') and video_info.get('video_url'):
                # 设置默认值
                video_info.setdefault('video_description', '')
                video_info.setdefault('thumbnail_url', '')
                video_info.setdefault('duration', '')
                video_info.setdefault('upload_date', '')
                video_info.setdefault('view_count', '')
                video_info.setdefault('like_count', '')
                
                videos.append(video_info)
        
        return videos
    
    async def _extract_video_info(self, element, base_url: str) -> Optional[Dict]:
        """从单个元素中提取视频信息"""
        try:
            video_info = {}
            
            # 提取标题
            title = self._extract_title(element)
            if title:
                video_info['video_title'] = title
            
            # 提取链接
            url = self._extract_url(element, base_url)
            if url:
                video_info['video_url'] = url
            
            # 提取描述
            description = self._extract_description(element)
            if description:
                video_info['video_description'] = description
            
            # 提取缩略图
            thumbnail = self._extract_thumbnail(element, base_url)
            if thumbnail:
                video_info['thumbnail_url'] = thumbnail
            
            # 设置其他字段默认值
            video_info.setdefault('duration', '')
            video_info.setdefault('upload_date', '')
            video_info.setdefault('view_count', '')
            video_info.setdefault('like_count', '')
            
            # 验证必要字段
            if video_info.get('video_title') and video_info.get('video_url'):
                return video_info
            
            return None
            
        except Exception as e:
            logger.error(f"提取视频信息失败: {str(e)}")
            return None
    
    def _extract_media_info(self, element, base_url: str) -> Optional[Dict]:
        """提取媒体信息（同步版本）"""
        try:
            # 提取标题
            title = self._extract_title(element)
            if not title:
                return None
            
            # 提取URL
            url = self._extract_url(element, base_url)
            if not url:
                url = base_url
            
            # 提取描述
            description = self._extract_description_from_element(element)
            if not description:
                description = title
            
            # 提取缩略图
            thumbnail = self._extract_thumbnail(element, base_url)
            
            return {
                'video_title': title,
                'video_url': url,
                'video_description': description,
                'thumbnail_url': thumbnail,
                'language': 'mn'
            }
        except Exception as e:
            logger.warning(f"提取媒体信息失败: {str(e)}")
            return None
    
    def _extract_title(self, element) -> Optional[str]:
        """提取标题"""
        # 尝试多种方式提取标题
        title_selectors = [
            'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '[class*="title"]', '[class*="name"]', '[class*="heading"]'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 3:  # 过滤太短的标题
                    return title
        
        # 尝试从alt属性或title属性获取
        alt_title = element.get('alt') or element.get('title')
        if alt_title and len(alt_title) > 3:
            return alt_title
        
        return None
    
    def _extract_url(self, element, base_url: str) -> Optional[str]:
        """提取链接"""
        # 尝试从href属性获取
        href = element.get('href')
        if href:
            return urljoin(base_url, href)
        
        # 尝试从src属性获取
        src = element.get('src')
        if src:
            return urljoin(base_url, src)
        
        # 尝试从data-src属性获取
        data_src = element.get('data-src')
        if data_src:
            return urljoin(base_url, data_src)
        
        return None
    
    def _extract_description(self, element) -> Optional[str]:
        """提取描述"""
        # 尝试多种方式提取描述
        desc_selectors = [
            'p', 'span', 'div',
            '[class*="description"]', '[class*="desc"]', '[class*="summary"]'
        ]
        
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                desc = desc_elem.get_text(strip=True)
                if desc and len(desc) > 10:  # 过滤太短的描述
                    return desc[:500]  # 限制长度
        
        return None
    
    def _extract_thumbnail(self, element, base_url: str) -> Optional[str]:
        """提取缩略图"""
        # 尝试多种方式提取缩略图
        img_selectors = ['img', '[class*="thumbnail"]', '[class*="thumb"]']
        
        for selector in img_selectors:
            img_elem = element.select_one(selector)
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src:
                    return urljoin(base_url, src)
        
        return None
    
    def _translate_videos(self, videos: List[Dict]) -> List[Dict]:
        """翻译视频信息"""
        if not self.translate_service:
            logger.warning("翻译服务不可用，跳过翻译")
            return videos
        
        translated_videos = []
        for video in videos:
            try:
                # 翻译标题
                if video.get('video_title'):
                    translated_title = self.translate_service.translate_text(
                        video['video_title'], 
                        target_language='zh-CN'
                    )
                    video['translated_title'] = translated_title
                
                # 翻译描述
                if video.get('video_description'):
                    translated_description = self.translate_service.translate_text(
                        video['video_description'], 
                        target_language='zh-CN'
                    )
                    video['translated_description'] = translated_description
                
                # 设置语言标识
                video['language'] = 'zh-CN' # 默认中文，根据实际语言调整
                
                translated_videos.append(video)
                
            except Exception as e:
                logger.error(f"翻译视频信息失败: {str(e)}")
                # 即使翻译失败，也保留原视频信息
                video['translated_title'] = video.get('video_title', '')
                video['translated_description'] = video.get('video_description', '')
                video['language'] = 'zh-CN'
                translated_videos.append(video)
        
        return translated_videos
    
    def get_supported_websites(self) -> List[Dict]:
        """获取支持的网站列表"""
        return [
            {
                'name': 'YouTube',
                'url': 'https://www.youtube.com',
                'description': 'YouTube视频平台',
                'crawl_pattern': 'youtube',
                'parse_strategy': 'custom',
                'container_selector': 'div[id="dismissible"]',
                'title_selector': 'h3 a#video-title',
                'url_selector': 'h3 a#video-title',
                'description_selector': 'div#description-text',
                'thumbnail_selector': 'img#img'
            },
            {
                'name': 'Bilibili',
                'url': 'https://www.bilibili.com',
                'description': 'B站视频平台',
                'crawl_pattern': 'bilibili',
                'parse_strategy': 'custom',
                'container_selector': 'li.video-item',
                'title_selector': 'a.title',
                'url_selector': 'a.title',
                'description_selector': 'div.desc',
                'thumbnail_selector': 'img.pic'
            },
            {
                'name': '通用视频网站',
                'url': '',
                'description': '通用的视频网站爬取模板',
                'crawl_pattern': 'general',
                'parse_strategy': 'auto',
                'container_selector': '',
                'title_selector': '',
                'url_selector': '',
                'description_selector': '',
                'thumbnail_selector': ''
            }
        ]

    def _normalize_url(self, url: str, base_url: str) -> str:
        """标准化URL，将相对URL转换为绝对URL"""
        if not url:
            return ''
        
        try:
            # 如果已经是绝对URL，直接返回
            if url.startswith(('http://', 'https://')):
                return url
            
            # 将相对URL转换为绝对URL
            return urljoin(base_url, url)
        except Exception as e:
            logger.warning(f"URL标准化失败: {url}, 错误: {str(e)}")
            return url

    def _extract_description_from_element(self, element) -> str:
        """从元素中提取描述信息"""
        try:
            # 查找相邻的描述元素
            next_sibling = element.find_next_sibling()
            if next_sibling and next_sibling.name in ['p', 'div', 'span']:
                return next_sibling.get_text(strip=True)[:200]
            
            # 查找子元素中的描述
            desc_elem = element.find(['p', 'div', 'span'])
            if desc_elem:
                return desc_elem.get_text(strip=True)[:200]
            
            # 查找父元素中的描述
            parent = element.find_parent(['div', 'section'])
            if parent:
                desc_elem = parent.find(['p', 'div'])
                if desc_elem:
                    return desc_elem.get_text(strip=True)[:200]
            
            return ""
        except Exception as e:
            logger.warning(f"提取描述失败: {str(e)}")
            return ""
