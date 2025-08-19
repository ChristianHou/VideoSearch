#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_youtube_download():
    """测试YouTube下载功能"""
    
    base_url = "http://localhost:5000"
    
    # 测试视频URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll
    
    try:
        print("正在测试YouTube下载功能...")
        
        # 1. 测试提取视频信息
        print("\n1. 测试提取视频信息...")
        extract_url = f"{base_url}/api/downloads/extract-info"
        extract_response = requests.post(extract_url, json={"url": test_url})
        
        print(f"提取信息响应状态码: {extract_response.status_code}")
        if extract_response.status_code == 200:
            extract_result = extract_response.json()
            print(f"提取结果: {json.dumps(extract_result, ensure_ascii=False, indent=2)}")
        else:
            print(f"提取失败: {extract_response.text}")
            return
        
        # 2. 测试获取支持的格式
        print("\n2. 测试获取支持的格式...")
        formats_url = f"{base_url}/api/downloads/formats"
        formats_response = requests.get(formats_url)
        
        print(f"格式列表响应状态码: {formats_response.status_code}")
        if formats_response.status_code == 200:
            formats_result = formats_response.json()
            print(f"格式列表: {json.dumps(formats_result, ensure_ascii=False, indent=2)}")
        else:
            print(f"获取格式列表失败: {formats_response.text}")
        
        # 3. 测试启动下载（可选）
        print("\n3. 测试启动下载...")
        start_url = f"{base_url}/api/downloads/start"
        start_response = requests.post(start_url, json={
            "url": test_url,
            "format": "best"
        })
        
        print(f"启动下载响应状态码: {start_response.status_code}")
        if start_response.status_code == 200:
            start_result = start_response.json()
            print(f"启动结果: {json.dumps(start_result, ensure_ascii=False, indent=2)}")
            
            if start_result['success']:
                task_id = start_result['task_id']
                
                # 4. 测试获取下载状态
                print(f"\n4. 测试获取下载状态 (任务ID: {task_id})...")
                status_url = f"{base_url}/api/downloads/status/{task_id}"
                status_response = requests.get(status_url)
                
                print(f"状态查询响应状态码: {status_response.status_code}")
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"状态结果: {json.dumps(status_result, ensure_ascii=False, indent=2)}")
                else:
                    print(f"状态查询失败: {status_response.text}")
        else:
            print(f"启动下载失败: {start_response.text}")
        
        # 5. 测试获取已下载文件列表
        print("\n5. 测试获取已下载文件列表...")
        files_url = f"{base_url}/api/downloads/files"
        files_response = requests.get(files_url)
        
        print(f"文件列表响应状态码: {files_response.status_code}")
        if files_response.status_code == 200:
            files_result = files_response.json()
            print(f"文件列表: {json.dumps(files_result, ensure_ascii=False, indent=2)}")
        else:
            print(f"获取文件列表失败: {files_response.text}")
        
        print("\n✅ YouTube下载功能测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_youtube_download()
