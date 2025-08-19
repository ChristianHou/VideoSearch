#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import yt_dlp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """YouTube视频下载器"""
    
    def __init__(self, download_path: str = "./downloads"):
        """
        初始化下载器
        
        Args:
            download_path: 下载文件保存路径
        """
        self.download_path = download_path
        self._ensure_download_path()
        
        # 默认下载选项
        self.default_options = {
            'format': 'best',  # 最佳质量
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': False,
            'verbose': True
        }
    
    def _ensure_download_path(self):
        """确保下载路径存在"""
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
            logger.info(f"创建下载目录: {self.download_path}")
    
    def extract_video_info(self, url: str) -> Dict:
        """
        提取视频信息
        
        Args:
            url: YouTube视频URL
            
        Returns:
            包含视频信息的字典
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 提取基本信息
                video_info = {
                    'title': info.get('title', '未知标题'),
                    'description': info.get('description', '')[:500] + '...' if info.get('description', '') else '',
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'uploader': info.get('uploader', '未知上传者'),
                    'upload_date': info.get('upload_date', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'formats': []
                }
                
                # 提取可用格式
                if 'formats' in info:
                    for fmt in info['formats']:
                        # 只包含有视频和音频的格式
                        if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                            format_info = {
                                'format_id': fmt.get('format_id', ''),
                                'ext': fmt.get('ext', ''),
                                'resolution': fmt.get('resolution', ''),
                                'filesize': fmt.get('filesize', 0),
                                'vcodec': fmt.get('vcodec', ''),
                                'acodec': fmt.get('acodec', ''),
                                'fps': fmt.get('fps', 0),
                                'height': fmt.get('height', 0),
                                'width': fmt.get('width', 0),
                                'quality': self._calculate_quality_score(fmt)
                            }
                            video_info['formats'].append(format_info)
                
                # 按质量排序
                video_info['formats'].sort(key=lambda x: x['quality'], reverse=True)
                
                # 添加预定义格式选项
                video_info['predefined_formats'] = self._get_predefined_formats()
                
                return {
                    'success': True,
                    'video_info': video_info
                }
                
        except Exception as e:
            logger.error(f"提取视频信息失败: {str(e)}")
            return {
                'success': False,
                'error': f"提取视频信息失败: {str(e)}"
            }
    
    def _calculate_quality_score(self, fmt: Dict) -> int:
        """计算格式质量分数"""
        score = 0
        
        # 分辨率分数
        if fmt.get('height'):
            if fmt['height'] >= 2160:  # 4K
                score += 1000
            elif fmt['height'] >= 1440:  # 2K
                score += 800
            elif fmt['height'] >= 1080:  # 1080p
                score += 600
            elif fmt['height'] >= 720:   # 720p
                score += 400
            elif fmt['height'] >= 480:   # 480p
                score += 200
        
        # 帧率分数
        if fmt.get('fps'):
            if fmt['fps'] >= 60:
                score += 100
            elif fmt['fps'] >= 30:
                score += 50
        
        # 文件大小分数（越小越好）
        if fmt.get('filesize'):
            score += max(0, 100 - (fmt['filesize'] // (1024 * 1024)))
        
        return score
    
    def download_video(self, url: str, options: Dict = None) -> Dict:
        """
        下载视频
        
        Args:
            url: YouTube视频URL
            options: 下载选项
            
        Returns:
            下载结果字典
        """
        try:
            # 合并选项
            download_options = self.default_options.copy()
            if options:
                download_options.update(options)
            
            # 设置输出模板
            if 'outtmpl' not in download_options or not download_options['outtmpl']:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                download_options['outtmpl'] = os.path.join(
                    self.download_path, 
                    f'%(title)s_{timestamp}.%(ext)s'
                )
            
            logger.info(f"开始下载视频: {url}")
            logger.info(f"下载选项: {download_options}")
            
            # 创建下载器
            with yt_dlp.YoutubeDL(download_options) as ydl:
                # 下载视频
                result = ydl.download([url])
                
                if result == 0:
                    # 获取下载后的文件信息
                    downloaded_files = self._get_downloaded_files(download_options['outtmpl'])
                    
                    return {
                        'success': True,
                        'message': '视频下载成功',
                        'files': downloaded_files
                    }
                else:
                    return {
                        'success': False,
                        'error': '下载过程中出现错误'
                    }
                    
        except Exception as e:
            logger.error(f"下载视频失败: {str(e)}")
            return {
                'success': False,
                'error': f"下载失败: {str(e)}"
            }
    
    def _get_downloaded_files(self, outtmpl: str) -> List[Dict]:
        """获取下载的文件信息"""
        files = []
        try:
            # 从输出模板推断文件名模式
            if '%(title)s' in outtmpl and '%(ext)s' in outtmpl:
                # 查找匹配的文件
                import glob
                pattern = outtmpl.replace('%(title)s', '*').replace('%(ext)s', '*')
                matching_files = glob.glob(pattern)
                
                for file_path in matching_files:
                    if os.path.exists(file_path):
                        file_info = {
                            'path': file_path,
                            'name': os.path.basename(file_path),
                            'size': os.path.getsize(file_path),
                            'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                            'created_time': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                        }
                        files.append(file_info)
        except Exception as e:
            logger.error(f"获取下载文件信息失败: {str(e)}")
        
        return files
    
    def get_download_progress(self, url: str) -> Dict:
        """获取下载进度（需要实现进度回调）"""
        # 这里可以实现进度跟踪功能
        return {
            'success': True,
            'progress': 0,
            'status': '准备中'
        }
    
    def get_supported_formats(self) -> List[Dict]:
        """获取支持的格式列表"""
        return [
            {'id': 'best', 'name': '最佳质量', 'description': '自动选择最佳质量'},
            {'id': 'worst', 'name': '最低质量', 'description': '自动选择最低质量'},
            {'id': 'bestvideo+bestaudio', 'name': '最佳视频+音频', 'description': '分别下载最佳视频和音频后合并'},
            {'id': 'mp4', 'name': 'MP4格式', 'description': '仅下载MP4格式'},
            {'id': 'webm', 'name': 'WebM格式', 'description': '仅下载WebM格式'},
            {'id': '720p', 'name': '720p', 'description': '720p分辨率'},
            {'id': '1080p', 'name': '1080p', 'description': '1080p分辨率'},
            {'id': '1440p', 'name': '1440p', 'description': '1440p分辨率'},
            {'id': '2160p', 'name': '4K', 'description': '4K分辨率'}
        ]
    
    def _get_predefined_formats(self) -> List[Dict]:
        """获取预定义的格式选项"""
        return [
            {'id': 'best', 'name': '最佳质量', 'description': '自动选择最佳质量'},
            {'id': 'worst', 'name': '最低质量', 'description': '自动选择最低质量'},
            {'id': 'bestvideo+bestaudio', 'name': '最佳视频+音频', 'description': '分别下载最佳视频和音频后合并'},
            {'id': 'mp4', 'name': 'MP4格式', 'description': '仅下载MP4格式'},
            {'id': 'webm', 'name': 'WebM格式', 'description': '仅下载WebM格式'},
            {'id': '720p', 'name': '720p', 'description': '720p分辨率'},
            {'id': '1080p', 'name': '1080p', 'description': '1080p分辨率'},
            {'id': '1440p', 'name': '1440p', 'description': '1440p分辨率'},
            {'id': '2160p', 'name': '4K', 'description': '4K分辨率'}
        ]
    
    def validate_url(self, url: str) -> bool:
        """验证URL是否为有效的YouTube链接"""
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+'
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        return False

# 全局下载器实例
_downloader_instance = None

def get_youtube_downloader() -> YouTubeDownloader:
    """获取YouTube下载器实例"""
    global _downloader_instance
    if _downloader_instance is None:
        _downloader_instance = YouTubeDownloader()
    return _downloader_instance
