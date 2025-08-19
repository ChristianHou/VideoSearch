#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def test_download_fix():
    """测试下载功能的修复"""
    
    base_url = "http://localhost:5000"
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll
    
    print("🔧 正在测试下载功能修复...")
    print("=" * 50)
    
    try:
        # 1. 测试提取视频信息
        print("\n1. 测试提取视频信息...")
        extract_response = requests.post(f"{base_url}/api/downloads/extract-info", 
                                      json={"url": test_url})
        
        if extract_response.status_code == 200:
            extract_result = extract_response.json()
            print(f"✅ 提取成功: {extract_result['success']}")
            
            if extract_result['success']:
                video_info = extract_result['video_info']
                print(f"📹 视频标题: {video_info['title']}")
                print(f"👤 上传者: {video_info['uploader']}")
                print(f"⏱️  时长: {video_info['duration']}秒")
                print(f"👁️  观看次数: {video_info['view_count']}")
                print(f"👍 点赞数: {video_info['like_count']}")
                print(f"📅 上传日期: {video_info['upload_date']}")
                print(f"🎬 可用格式数量: {len(video_info['formats'])}")
                
                # 显示前几个格式
                if video_info['formats']:
                    print("\n📋 前3个可用格式:")
                    for i, fmt in enumerate(video_info['formats'][:3]):
                        print(f"  {i+1}. {fmt['resolution']} - {fmt['ext']} - 质量:{fmt['quality']}")
                
                # 2. 测试启动下载
                print("\n2. 测试启动下载...")
                start_response = requests.post(f"{base_url}/api/downloads/start", 
                                            json={
                                                "url": test_url,
                                                "format": "best"
                                            })
                
                if start_response.status_code == 200:
                    start_result = start_response.json()
                    print(f"✅ 启动下载成功: {start_result['success']}")
                    
                    if start_result['success']:
                        task_id = start_result['task_id']
                        print(f"🆔 任务ID: {task_id}")
                        
                        # 3. 测试获取下载状态
                        print(f"\n3. 测试获取下载状态 (任务ID: {task_id})...")
                        time.sleep(2)  # 等待一下
                        
                        status_response = requests.get(f"{base_url}/api/downloads/status/{task_id}")
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            print(f"✅ 状态查询成功: {status_result['success']}")
                            
                            if status_result['success']:
                                task = status_result['task']
                                print(f"📊 任务状态: {task['status']}")
                                print(f"📈 进度: {task['progress']}%")
                                if task.get('error'):
                                    print(f"❌ 错误: {task['error']}")
                        else:
                            print(f"❌ 状态查询失败: {status_response.status_code}")
                    else:
                        print(f"❌ 启动下载失败: {start_result.get('error', '未知错误')}")
                else:
                    print(f"❌ 启动下载请求失败: {start_response.status_code}")
                    print(f"错误信息: {start_response.text}")
            else:
                print(f"❌ 提取失败: {extract_result.get('error', '未知错误')}")
        else:
            print(f"❌ 提取请求失败: {extract_response.status_code}")
            print(f"错误信息: {extract_response.text}")
        
        # 4. 测试获取支持的格式
        print("\n4. 测试获取支持的格式...")
        formats_response = requests.get(f"{base_url}/api/downloads/formats")
        if formats_response.status_code == 200:
            formats_result = formats_response.json()
            print(f"✅ 格式列表获取成功: {formats_result['success']}")
            if formats_result['success']:
                print(f"📋 支持 {len(formats_result['formats'])} 种格式")
                for fmt in formats_result['formats'][:3]:
                    print(f"  - {fmt['name']}: {fmt['description']}")
        else:
            print(f"❌ 格式列表获取失败: {formats_response.status_code}")
        
        # 5. 测试获取已下载文件列表
        print("\n5. 测试获取已下载文件列表...")
        files_response = requests.get(f"{base_url}/api/downloads/files")
        if files_response.status_code == 200:
            files_result = files_response.json()
            print(f"✅ 文件列表获取成功: {files_result['success']}")
            if files_result['success']:
                print(f"📁 下载目录: {files_result['download_path']}")
                print(f"📄 文件数量: {len(files_result['files'])}")
        else:
            print(f"❌ 文件列表获取失败: {files_response.status_code}")
        
        print("\n" + "=" * 50)
        print("🎯 下载功能修复测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_download_fix()
