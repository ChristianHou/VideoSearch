# -*- coding: utf-8 -*-
"""
测试定时任务功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_create_task():
    """测试创建搜索任务"""
    print("1. 创建搜索任务...")
    
    task_data = {
        "query": "Python编程教程",
        "max_results": 10,
        "region_code": "US",
        "video_duration": "medium"
    }
    
    response = requests.post(f"{BASE_URL}/tasks", json=task_data)
    if response.status_code == 201:
        result = response.json()
        print(f"✅ 任务创建成功，ID: {result['task_id']}")
        return result['task_id']
    else:
        print(f"❌ 任务创建失败: {response.text}")
        return None

def test_create_scheduled_task(task_id):
    """测试创建定时任务"""
    print(f"\n2. 为任务 {task_id} 创建定时任务...")
    
    scheduled_task_data = {
        "task_id": task_id,
        "schedule_type": "interval",
        "interval_minutes": 5
    }
    
    response = requests.post(f"{BASE_URL}/scheduled-tasks", json=scheduled_task_data)
    if response.status_code == 201:
        result = response.json()
        print(f"✅ 定时任务创建成功，ID: {result['scheduled_task_id']}")
        return result['scheduled_task_id']
    else:
        print(f"❌ 定时任务创建失败: {response.text}")
        return None

def test_list_scheduled_tasks():
    """测试获取定时任务列表"""
    print("\n3. 获取定时任务列表...")
    
    response = requests.get(f"{BASE_URL}/scheduled-tasks")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功，共 {len(result['scheduled_tasks'])} 个定时任务")
        for task in result['scheduled_tasks']:
            print(f"   - ID: {task['id']}, 类型: {task['schedule_type']}, 状态: {'启用' if task['is_active'] else '禁用'}")
        return result['scheduled_tasks']
    else:
        print(f"❌ 获取失败: {response.text}")
        return []

def test_toggle_scheduled_task(scheduled_task_id, is_active):
    """测试切换定时任务状态"""
    print(f"\n4. 切换定时任务 {scheduled_task_id} 状态为 {'启用' if is_active else '禁用'}...")
    
    response = requests.put(f"{BASE_URL}/scheduled-tasks/{scheduled_task_id}/toggle", 
                           json={"is_active": is_active})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 状态切换成功: {result['message']}")
        return True
    else:
        print(f"❌ 状态切换失败: {response.text}")
        return False

def test_get_scheduled_task_detail(scheduled_task_id):
    """测试获取定时任务详情"""
    print(f"\n5. 获取定时任务 {scheduled_task_id} 详情...")
    
    response = requests.get(f"{BASE_URL}/scheduled-tasks/{scheduled_task_id}")
    if response.status_code == 200:
        result = response.json()
        task = result['scheduled_task']
        print(f"✅ 获取成功:")
        print(f"   - 调度类型: {task['schedule_type']}")
        print(f"   - 状态: {'启用' if task['is_active'] else '禁用'}")
        print(f"   - 下次执行: {task['next_run']}")
        print(f"   - 关联任务: {task['task']['query']}")
        return True
    else:
        print(f"❌ 获取失败: {response.text}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试定时任务功能...\n")
    
    try:
        # 1. 创建搜索任务
        task_id = test_create_task()
        if not task_id:
            return
        
        # 2. 创建定时任务
        scheduled_task_id = test_create_scheduled_task(task_id)
        if not scheduled_task_id:
            return
        
        # 3. 获取定时任务列表
        scheduled_tasks = test_list_scheduled_tasks()
        if not scheduled_tasks:
            return
        
        # 4. 切换定时任务状态
        test_toggle_scheduled_task(scheduled_task_id, False)
        test_toggle_scheduled_task(scheduled_task_id, True)
        
        # 5. 获取定时任务详情
        test_get_scheduled_task_detail(scheduled_task_id)
        
        print("\n🎉 所有测试完成！")
        print("\n💡 提示:")
        print("   - 定时任务已创建并启用")
        print("   - 系统会每5分钟自动执行一次搜索")
        print("   - 可以在Web界面查看执行结果")
        print("   - 按Ctrl+C停止服务器")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保服务器正在运行 (python run.py)")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
