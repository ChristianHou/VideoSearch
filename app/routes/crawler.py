#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import asyncio
import threading
from typing import Dict, List

from ..database import db_manager
from ..models import CrawlWebsite, CrawlTask, CrawlVideo, CrawlScheduledTask
from ..services.crawler_service import CrawlerService
from ..services.translate_service import get_translate_service

crawler_bp = Blueprint('crawler', __name__, url_prefix='/api/crawler')

# 全局变量存储爬虫任务状态
crawler_tasks = {}

@crawler_bp.route('/websites', methods=['GET'])
def get_websites():
    """获取所有爬取网站"""
    try:
        db = db_manager.get_session()
        websites = db.query(CrawlWebsite).filter(CrawlWebsite.is_active == True).all()
        
        result = []
        for website in websites:
            website_data = {
                'id': website.id,
                'name': website.name,
                'url': website.url,
                'description': website.description,
                'crawl_pattern': website.crawl_pattern,
                'is_active': website.is_active,
                'created_at': website.created_at.isoformat() if website.created_at else None,
                'updated_at': website.updated_at.isoformat() if website.updated_at else None
            }
            
            # 添加爬取配置信息
            if website.crawl_config:
                try:
                    crawl_config = json.loads(website.crawl_config)
                    website_data.update(crawl_config)
                except:
                    pass
            
            result.append(website_data)
        
        return jsonify({
            'success': True,
            'websites': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取网站列表失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/websites', methods=['POST'])
def create_website():
    """创建新的爬取网站"""
    try:
        data = request.get_json()
        name = data.get('name')
        url = data.get('url')
        description = data.get('description', '')
        crawl_pattern = data.get('crawl_pattern', 'general')
        
        if not name or not url:
            return jsonify({
                'success': False,
                'error': '网站名称和URL不能为空'
            }), 400
        
        db = db_manager.get_session()
        
        # 检查URL是否已存在
        existing_website = db.query(CrawlWebsite).filter(CrawlWebsite.url == url).first()
        if existing_website:
            return jsonify({
                'success': False,
                'error': '该网站URL已存在'
            }), 400
        
        # 创建新网站
        new_website = CrawlWebsite(
            name=name,
            url=url,
            description=description,
            crawl_pattern=crawl_pattern
        )
        
        # 如果是自定义模式，保存选择器信息到crawl_config
        if data.get('parse_strategy') == 'custom':
            crawl_config = {
                'parse_strategy': 'custom',
                'container_selector': data.get('container_selector', ''),
                'title_selector': data.get('title_selector', ''),
                'url_selector': data.get('url_selector', ''),
                'description_selector': data.get('description_selector', ''),
                'thumbnail_selector': data.get('thumbnail_selector', '')
            }
            new_website.crawl_config = json.dumps(crawl_config)
        
        db.add(new_website)
        db.commit()
        db.refresh(new_website)
        
        return jsonify({
            'success': True,
            'website': {
                'id': new_website.id,
                'name': new_website.name,
                'url': new_website.url,
                'description': new_website.description,
                'crawl_pattern': new_website.crawl_pattern,
                'is_active': new_website.is_active,
                'created_at': new_website.created_at.isoformat() if new_website.created_at else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'创建网站失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/websites/<int:website_id>', methods=['PUT'])
def update_website(website_id):
    """更新爬取网站"""
    try:
        data = request.get_json()
        db = db_manager.get_session()
        
        website = db.query(CrawlWebsite).filter(CrawlWebsite.id == website_id).first()
        if not website:
            return jsonify({
                'success': False,
                'error': '网站不存在'
            }), 404
        
        # 更新字段
        if 'name' in data:
            website.name = data['name']
        if 'url' in data:
            website.url = data['url']
        if 'description' in data:
            website.description = data['description']
        if 'crawl_pattern' in data:
            website.crawl_pattern = data['crawl_pattern']
        if 'is_active' in data:
            website.is_active = data['is_active']
        
        # 更新爬取配置
        if 'parse_strategy' in data and data['parse_strategy'] == 'custom':
            crawl_config = {
                'parse_strategy': 'custom',
                'container_selector': data.get('container_selector', ''),
                'title_selector': data.get('title_selector', ''),
                'url_selector': data.get('url_selector', ''),
                'description_selector': data.get('description_selector', ''),
                'thumbnail_selector': data.get('thumbnail_selector', '')
            }
            website.crawl_config = json.dumps(crawl_config)
        elif 'parse_strategy' in data and data['parse_strategy'] == 'auto':
            website.crawl_config = None
        
        website.updated_at = datetime.now()
        db.commit()
        
        return jsonify({
            'success': True,
            'website': {
                'id': website.id,
                'name': website.name,
                'url': website.url,
                'description': website.description,
                'crawl_pattern': website.crawl_pattern,
                'is_active': website.is_active,
                'updated_at': website.updated_at.isoformat() if website.updated_at else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'更新网站失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/websites/<int:website_id>', methods=['DELETE'])
def delete_website(website_id):
    """删除爬取网站"""
    try:
        db = db_manager.get_session()
        
        website = db.query(CrawlWebsite).filter(CrawlWebsite.id == website_id).first()
        if not website:
            return jsonify({
                'success': False,
                'error': '网站不存在'
            }), 404
        
        # 检查是否有关联的任务
        task_count = db.query(CrawlTask).filter(CrawlTask.website_id == website_id).count()
        if task_count > 0:
            return jsonify({
                'success': False,
                'error': f'该网站还有 {task_count} 个关联任务，无法删除'
            }), 400
        
        db.delete(website)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '网站删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'删除网站失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """获取所有爬取任务"""
    try:
        db = db_manager.get_session()
        tasks = db.query(CrawlTask).order_by(CrawlTask.created_at.desc()).all()
        
        result = []
        for task in tasks:
            result.append({
                'id': task.id,
                'name': task.name,
                'website_id': task.website_id,
                'task_type': task.task_type,
                'status': task.status,
                'crawl_config': json.loads(task.crawl_config) if task.crawl_config else {},
                'scheduled_time': task.scheduled_time.isoformat() if task.scheduled_time else None,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'total_videos': task.total_videos,
                'error_message': task.error_message
            })
        
        return jsonify({
            'success': True,
            'tasks': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取任务列表失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/tasks', methods=['POST'])
def create_task():
    """创建新的爬取任务"""
    try:
        data = request.get_json()
        name = data.get('name')
        website_id = data.get('website_id')
        task_type = data.get('task_type', 'manual')
        crawl_config = data.get('crawl_config', {})
        scheduled_time = data.get('scheduled_time')
        
        if not name or not website_id:
            return jsonify({
                'success': False,
                'error': '任务名称和网站ID不能为空'
            }), 400
        
        db = db_manager.get_session()
        
        # 检查网站是否存在
        website = db.query(CrawlWebsite).filter(CrawlWebsite.id == website_id).first()
        if not website:
            return jsonify({
                'success': False,
                'error': '网站不存在'
            }), 404
        
        # 创建新任务
        new_task = CrawlTask(
            name=name,
            website_id=website_id,
            task_type=task_type,
            status='pending',
            crawl_config=json.dumps(crawl_config),
            scheduled_time=datetime.fromisoformat(scheduled_time) if scheduled_time else None
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        # 如果是手动任务，立即执行
        if task_type == 'manual':
            # 在新线程中执行爬取任务
            thread = threading.Thread(target=execute_crawl_task_async, args=(new_task.id,))
            thread.daemon = True
            thread.start()
        
        return jsonify({
            'success': True,
            'task': {
                'id': new_task.id,
                'name': new_task.name,
                'website_id': new_task.website_id,
                'task_type': new_task.task_type,
                'status': new_task.status,
                'created_at': new_task.created_at.isoformat() if new_task.created_at else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'创建任务失败: {str(e)}'
        }), 500

@crawler_bp.route('/tasks/<int:task_id>/videos', methods=['GET'])
def get_task_videos(task_id):
    """获取任务关联的视频"""
    try:
        db = db_manager.get_session()
        videos = db.query(CrawlVideo).filter(CrawlVideo.task_id == task_id).order_by(CrawlVideo.crawl_time.desc()).all()
        
        result = []
        for video in videos:
            result.append({
                'id': video.id,
                'task_id': video.task_id,
                'website_id': video.website_id,
                'video_title': video.video_title,
                'video_url': video.video_url,
                'video_description': video.video_description,
                'thumbnail_url': video.thumbnail_url,
                'duration': video.duration,
                'upload_date': video.upload_date,
                'view_count': video.view_count,
                'like_count': video.like_count,
                'translated_title': video.translated_title,
                'translated_description': video.translated_description,
                'language': video.language,
                'crawl_time': video.crawl_time.isoformat() if video.crawl_time else None
            })
        
        return jsonify({
            'success': True,
            'videos': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取视频列表失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/tasks/<int:task_id>/execute', methods=['POST'])
def execute_crawl_task(task_id):
    """执行爬取任务"""
    try:
        db = db_manager.get_session()
        
        # 查找任务
        task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        # 查找网站
        website = db.query(CrawlWebsite).filter(CrawlWebsite.id == task.website_id).first()
        if not website:
            return jsonify({
                'success': False,
                'error': '网站不存在'
            }), 404
        
        # 更新任务状态
        task.status = 'running'
        task.started_at = datetime.utcnow()
        db.commit()
        
        # 在后台执行爬取任务
        def run_crawl_task():
            try:
                asyncio.run(execute_crawl_task_async(task_id))
            except Exception as e:
                print(f"爬取任务执行失败: {str(e)}")
                # 更新任务状态为失败
                try:
                    db = db_manager.get_session()
                    task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
                    if task:
                        task.status = 'failed'
                        task.error_message = str(e)
                        task.completed_at = datetime.utcnow()
                        db.commit()
                except Exception as db_error:
                    print(f"更新任务状态失败: {str(db_error)}")
                finally:
                    db.close()
        
        # 启动后台线程
        thread = threading.Thread(target=run_crawl_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '任务执行已启动'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'启动任务失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_crawl_task(task_id):
    """删除爬取任务"""
    try:
        db = db_manager.get_session()
        
        # 查找任务
        task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        # 删除相关的视频数据
        db.query(CrawlVideo).filter(CrawlVideo.task_id == task_id).delete()
        
        # 删除任务
        db.delete(task)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '任务删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'删除任务失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/scheduled-tasks', methods=['GET'])
def get_scheduled_tasks():
    """获取所有定时爬取任务"""
    try:
        db = db_manager.get_session()
        tasks = db.query(CrawlScheduledTask).filter(CrawlScheduledTask.is_active == True).all()
        
        result = []
        for task in tasks:
            result.append({
                'id': task.id,
                'name': task.name,
                'website_id': task.website_id,
                'schedule_type': task.schedule_type,
                'schedule_value': task.schedule_value,
                'is_active': task.is_active,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'total_runs': task.total_runs,
                'created_at': task.created_at.isoformat() if task.created_at else None
            })
        
        return jsonify({
            'success': True,
            'scheduled_tasks': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取定时任务列表失败: {str(e)}'
        }), 500
    finally:
        db.close()

@crawler_bp.route('/scheduled-tasks', methods=['POST'])
def create_scheduled_task():
    """创建新的定时爬取任务"""
    try:
        data = request.get_json()
        name = data.get('name')
        website_id = data.get('website_id')
        schedule_type = data.get('schedule_type', 'daily')
        schedule_value = data.get('schedule_value', '00:00')
        crawl_config = data.get('crawl_config', {})
        
        if not name or not website_id:
            return jsonify({
                'success': False,
                'error': '任务名称和网站ID不能为空'
            }), 400
        
        db = db_manager.get_session()
        
        # 检查网站是否存在
        website = db.query(CrawlWebsite).filter(CrawlWebsite.id == website_id).first()
        if not website:
            return jsonify({
                'success': False,
                'error': '网站不存在'
            }), 404
        
        # 创建新定时任务
        new_task = CrawlScheduledTask(
            name=name,
            website_id=website_id,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            is_active=True
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return jsonify({
            'success': True,
            'scheduled_task': {
                'id': new_task.id,
                'name': new_task.name,
                'website_id': new_task.website_id,
                'schedule_type': new_task.schedule_type,
                'schedule_value': new_task.schedule_value,
                'is_active': new_task.is_active,
                'created_at': new_task.created_at.isoformat() if new_task.created_at else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'创建定时任务失败: {str(e)}'
        }), 500

@crawler_bp.route('/supported-websites', methods=['GET'])
def get_supported_websites():
    """获取支持的网站模板"""
    try:
        crawler_service = CrawlerService()
        supported_websites = crawler_service.get_supported_websites()
        
        return jsonify({
            'success': True,
            'supported_websites': supported_websites
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取支持的网站失败: {str(e)}'
        }), 500

def execute_crawl_task_async(task_id: int):
    """执行爬取任务（异步）"""
    try:
        db = db_manager.get_session()
        task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
        
        if not task:
            print(f"任务 {task_id} 不存在")
            return
        
        # 获取网站信息
        website = db.query(CrawlWebsite).filter(CrawlWebsite.id == task.website_id).first()
        if not website:
            task.status = 'failed'
            task.error_message = '网站不存在'
            task.updated_at = datetime.now()
            db.commit()
            return
        
        # 获取爬取配置
        task_crawl_config = json.loads(task.crawl_config) if task.crawl_config else {}
        
        # 获取网站的爬取配置
        website_crawl_config = {}
        if website.crawl_config:
            try:
                website_crawl_config = json.loads(website.crawl_config)
            except:
                pass
        
        # 合并配置
        final_crawl_config = {
            **task_crawl_config,
            'website_crawl_config': website_crawl_config
        }
        
        # 执行爬取
        try:
            # 创建新的爬虫服务实例
            crawler_service = CrawlerService()
            # 直接调用爬取方法
            videos = asyncio.run(crawler_service.crawl_website(website.url, final_crawl_config))
        except Exception as crawl_error:
            print(f"爬取失败: {str(crawl_error)}")
            videos = []
        
        # 保存视频信息
        for video_data in videos:
            video = CrawlVideo(
                task_id=task_id,
                website_id=website.id,
                video_title=video_data.get('video_title', ''),
                video_url=video_data.get('video_url', ''),
                video_description=video_data.get('video_description', ''),
                thumbnail_url=video_data.get('thumbnail_url', ''),
                duration=video_data.get('duration', ''),
                upload_date=video_data.get('upload_date', ''),
                view_count=video_data.get('view_count', ''),
                like_count=video_data.get('like_count', ''),
                translated_title=video_data.get('translated_title', ''),
                translated_description=video_data.get('translated_description', ''),
                language=video_data.get('language', ''),
                crawl_time=datetime.utcnow()
            )
            db.add(video)
        
        # 更新任务状态
        task.status = 'completed'
        task.total_videos = len(videos)
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        db.commit()
        print(f"任务 {task_id} 执行完成，共获取 {len(videos)} 个视频")
        
    except Exception as e:
        print(f"任务 {task_id} 执行失败: {str(e)}")
        try:
            task.status = 'failed'
            task.error_message = str(e)
            task.updated_at = datetime.utcnow()
            db.commit()
        except:
            pass
    finally:
        db.close()
