#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_ai_api_fixed():
    """测试修复后的AI关键词生成API"""
    url = "http://localhost:5000/api/scheduled-tasks/ai-generate-keywords"
    
    # 测试数据
    test_data = {
        "event_id": 1  # 假设存在ID为1的事件
    }
    
    try:
        print(f"正在测试修复后的API: {url}")
        print(f"请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
        
        # 设置较长的超时时间
        response = requests.post(url, json=test_data, timeout=90)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ 成功！响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"响应内容: {response.text[:500]}")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时（90秒）")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_ai_api_fixed()
