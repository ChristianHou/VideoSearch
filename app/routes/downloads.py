#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, send_file
import os
from datetime import datetime
import threading
import time

from ..services.youtube_downloader import get_youtube_downloader

downloads_bp = Blueprint('downloads', __name__)

# 存储下载任务状态
download_tasks = {}

@downloads_bp.route('/downloads/extract-info', methods=['POST'])
def extract_video_info():
    """提取视频信息"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': '请提供视频URL'})
        
        # 验证URL
        downloader = get_youtube_downloader()
        if not downloader.validate_url(url):
            return jsonify({'success': False, 'error': '无效的YouTube URL'})
        
        # 提取视频信息
        result = downloader.extract_video_info(url)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'提取视频信息失败: {str(e)}'}), 500

@downloads_bp.route('/downloads/start', methods=['POST'])
def start_download():
    """开始下载视频"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        format_id = data.get('format', 'best')
        download_path = data.get('download_path', '')
        
        if not url:
            return jsonify({'success': False, 'error': '请提供视频URL'})
        
        # 验证URL
        downloader = get_youtube_downloader()
        if not downloader.validate_url(url):
            return jsonify({'success': False, 'error': '无效的YouTube URL'})
        
        # 创建下载任务
        task_id = f"download_{int(time.time())}"
        download_tasks[task_id] = {
            'id': task_id,
            'url': url,
            'status': 'starting',
            'progress': 0,
            'start_time': datetime.now().isoformat(),
            'error': None
        }
        
        # 在后台线程中执行下载
        def download_worker():
            try:
                download_tasks[task_id]['status'] = 'downloading'
                download_tasks[task_id]['progress'] = 10
                
                # 设置下载选项
                options = {
                    'format': format_id
                }
                
                # 添加进度回调（如果支持）
                try:
                    options['progress_hooks'] = [lambda d: progress_callback(task_id, d)]
                except:
                    pass
                
                if download_path:
                    options['outtmpl'] = os.path.join(download_path, '%(title)s.%(ext)s')
                
                # 执行下载
                result = downloader.download_video(url, options)
                
                if result['success']:
                    download_tasks[task_id]['status'] = 'completed'
                    download_tasks[task_id]['progress'] = 100
                    download_tasks[task_id]['result'] = result
                else:
                    download_tasks[task_id]['status'] = 'failed'
                    download_tasks[task_id]['error'] = result['error']
                    
            except Exception as e:
                download_tasks[task_id]['status'] = 'failed'
                download_tasks[task_id]['error'] = str(e)
        
        # 启动下载线程
        thread = threading.Thread(target=download_worker)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '下载任务已启动'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'启动下载失败: {str(e)}'}), 500

def progress_callback(task_id: str, d: dict):
    """下载进度回调"""
    if task_id in download_tasks:
        if d['status'] == 'downloading':
            # 计算进度百分比
            if 'total_bytes' in d and d['total_bytes']:
                progress = int((d['downloaded_bytes'] / d['total_bytes']) * 90) + 10
                download_tasks[task_id]['progress'] = progress
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                progress = int((d['downloaded_bytes'] / d['total_bytes_estimate']) * 90) + 10
                download_tasks[task_id]['progress'] = progress

@downloads_bp.route('/downloads/status/<task_id>', methods=['GET'])
def get_download_status(task_id: str):
    """获取下载任务状态"""
    if task_id not in download_tasks:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    task = download_tasks[task_id]
    return jsonify({
        'success': True,
        'task': task
    })

@downloads_bp.route('/downloads/tasks', methods=['GET'])
def list_download_tasks():
    """获取所有下载任务"""
    return jsonify({
        'success': True,
        'tasks': list(download_tasks.values())
    })

@downloads_bp.route('/downloads/cancel/<task_id>', methods=['POST'])
def cancel_download(task_id: str):
    """取消下载任务"""
    if task_id not in download_tasks:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    # 标记任务为已取消
    download_tasks[task_id]['status'] = 'cancelled'
    download_tasks[task_id]['progress'] = 0
    
    return jsonify({
        'success': True,
        'message': '下载任务已取消'
    })

@downloads_bp.route('/downloads/formats', methods=['GET'])
def get_supported_formats():
    """获取支持的下载格式"""
    try:
        downloader = get_youtube_downloader()
        formats = downloader.get_supported_formats()
        
        return jsonify({
            'success': True,
            'formats': formats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取格式列表失败: {str(e)}'}), 500

@downloads_bp.route('/downloads/files', methods=['GET'])
def list_downloaded_files():
    """获取已下载的文件列表"""
    try:
        downloader = get_youtube_downloader()
        download_path = downloader.download_path
        
        files = []
        if os.path.exists(download_path):
            for filename in os.listdir(download_path):
                file_path = os.path.join(download_path, filename)
                if os.path.isfile(file_path):
                    file_info = {
                        'name': filename,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                        'created_time': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                        'modified_time': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    files.append(file_info)
        
        # 按创建时间排序
        files.sort(key=lambda x: x['created_time'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files,
            'download_path': download_path
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取文件列表失败: {str(e)}'}), 500

@downloads_bp.route('/downloads/download/<filename>', methods=['GET'])
def download_file(filename: str):
    """下载文件"""
    try:
        downloader = get_youtube_downloader()
        file_path = os.path.join(downloader.download_path, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': f'下载文件失败: {str(e)}'}), 500

@downloads_bp.route('/downloads/delete/<filename>', methods=['DELETE'])
def delete_file(filename: str):
    """删除下载的文件"""
    try:
        downloader = get_youtube_downloader()
        file_path = os.path.join(downloader.download_path, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': '文件删除成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'删除文件失败: {str(e)}'}), 500
