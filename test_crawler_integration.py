#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def test_crawler_integration():
    """测试爬虫模块的集成功能"""
    base_url = "http://localhost:5000"
    
    print("🧪 开始测试爬虫模块集成功能...")
    
    # 1. 测试添加网站
    print("\n1. 测试添加网站...")
    website_data = {
        "name": "测试网站",
        "url": "https://example.com",
        "description": "这是一个测试网站",
        "crawl_pattern": "general",
        "parse_strategy": "auto"
    }
    
    try:
        response = requests.post(f"{base_url}/api/crawler/websites", json=website_data)
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                website_id = result['website']['id']
                print(f"✅ 网站添加成功，ID: {website_id}")
            else:
                print(f"❌ 网站添加失败: {result['error']}")
                return
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return
    
    # 2. 测试创建爬取任务
    print("\n2. 测试创建爬取任务...")
    task_data = {
        "name": "测试爬取任务",
        "website_id": website_id,
        "task_type": "manual",
        "crawl_config": {
            "enable_translation": True,
            "enable_thumbnail": True,
            "enable_metadata": False,
            "max_pages": 1,
            "delay_between_requests": 1.0
        }
    }
    
    try:
        response = requests.post(f"{base_url}/api/crawler/tasks", json=task_data)
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                task_id = result['task']['id']
                print(f"✅ 任务创建成功，ID: {task_id}")
            else:
                print(f"❌ 任务创建失败: {result['error']}")
                return
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return
    
    # 3. 等待任务执行
    print("\n3. 等待任务执行...")
    time.sleep(5)
    
    # 4. 检查任务状态
    print("\n4. 检查任务状态...")
    try:
        response = requests.get(f"{base_url}/api/crawler/tasks")
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                tasks = result['tasks']
                task = next((t for t in tasks if t['id'] == task_id), None)
                if task:
                    print(f"✅ 任务状态: {task['status']}")
                    if task['total_videos'] is not None:
                        print(f"✅ 爬取视频数量: {task['total_videos']}")
                else:
                    print("❌ 未找到任务")
            else:
                print(f"❌ 获取任务列表失败: {result['error']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 网络错误: {e}")
    
    # 5. 检查爬取结果
    print("\n5. 检查爬取结果...")
    try:
        response = requests.get(f"{base_url}/api/crawler/tasks/{task_id}/videos")
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                videos = result['videos']
                print(f"✅ 获取到 {len(videos)} 个视频")
                if videos:
                    video = videos[0]
                    print(f"   第一个视频:")
                    print(f"   - 标题: {video['video_title']}")
                    if video.get('translated_title'):
                        print(f"   - 中文标题: {video['translated_title']}")
                    print(f"   - 链接: {video['video_url']}")
                    print(f"   - 描述: {video['video_description'][:100]}...")
                    if video.get('translated_description'):
                        print(f"   - 中文描述: {video['translated_description'][:100]}...")
            else:
                print(f"❌ 获取视频列表失败: {result['error']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 网络错误: {e}")
    
    print("\n🎉 爬虫模块集成测试完成！")

if __name__ == "__main__":
    test_crawler_integration()
