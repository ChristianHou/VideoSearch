#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_event_binding():
    """测试事件绑定功能"""
    
    base_url = "http://localhost:5000"
    
    # 测试数据
    test_data = {
        "event_id": 1,  # 假设存在ID为1的事件
        "scheduled_task_id": 1  # 假设存在ID为1的定时任务
    }
    
    try:
        print("正在测试事件绑定功能...")
        
        # 1. 测试绑定事件
        print("\n1. 测试绑定事件到定时任务...")
        bind_url = f"{base_url}/api/scheduled-tasks/{test_data['scheduled_task_id']}/bind-event"
        bind_response = requests.post(bind_url, json={"event_id": test_data["event_id"]})
        
        print(f"绑定响应状态码: {bind_response.status_code}")
        if bind_response.status_code == 200:
            bind_result = bind_response.json()
            print(f"绑定结果: {json.dumps(bind_result, ensure_ascii=False, indent=2)}")
        else:
            print(f"绑定失败: {bind_response.text}")
        
        # 2. 测试查询绑定关系
        print("\n2. 测试查询定时任务的事件绑定...")
        query_url = f"{base_url}/api/scheduled-tasks/{test_data['scheduled_task_id']}/event-binding"
        query_response = requests.get(query_url)
        
        print(f"查询响应状态码: {query_response.status_code}")
        if query_response.status_code == 200:
            query_result = query_response.json()
            print(f"查询结果: {json.dumps(query_result, ensure_ascii=False, indent=2)}")
        else:
            print(f"查询失败: {query_response.text}")
        
        # 3. 测试绑定到另一个事件（应该自动解绑前一个）
        print("\n3. 测试绑定到另一个事件（应该自动解绑前一个）...")
        bind_url2 = f"{base_url}/api/scheduled-tasks/{test_data['scheduled_task_id']}/bind-event"
        bind_response2 = requests.post(bind_url2, json={"event_id": 2})  # 绑定到事件2
        
        print(f"重新绑定响应状态码: {bind_response2.status_code}")
        if bind_response2.status_code == 200:
            bind_result2 = bind_response2.json()
            print(f"重新绑定结果: {json.dumps(bind_result2, ensure_ascii=False, indent=2)}")
        else:
            print(f"重新绑定失败: {bind_response2.text}")
        
        # 4. 再次查询绑定关系
        print("\n4. 再次查询绑定关系...")
        query_response2 = requests.get(query_url)
        
        print(f"查询响应状态码: {query_response2.status_code}")
        if query_response2.status_code == 200:
            query_result2 = query_response2.json()
            print(f"查询结果: {json.dumps(query_result2, ensure_ascii=False, indent=2)}")
        else:
            print(f"查询失败: {query_response2.text}")
        
        print("\n✅ 事件绑定测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_event_binding()
