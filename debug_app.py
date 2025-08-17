#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_app():
    """调试Flask应用"""
    try:
        print("=== 调试Flask应用 ===")
        
        # 1. 测试蓝图导入
        print("1. 测试蓝图导入...")
        from app.routes.scheduled_tasks import scheduled_tasks_bp
        print(f"✅ scheduled_tasks_bp 导入成功: {scheduled_tasks_bp}")
        
        # 2. 检查蓝图中的路由
        print("2. 检查蓝图中的路由...")
        print(f"蓝图名称: {scheduled_tasks_bp.name}")
        print(f"蓝图URL前缀: {scheduled_tasks_bp.url_prefix}")
        
        # 3. 创建Flask应用
        print("3. 创建Flask应用...")
        from app import create_app
        app = create_app()
        print("✅ Flask应用创建成功")
        
        # 4. 检查应用中的路由
        print("4. 检查应用中的路由...")
        print(f"应用URL规则数量: {len(app.url_map._rules)}")
        
        # 查找scheduled_tasks相关的路由
        scheduled_routes = []
        for rule in app.url_map._rules:
            if 'scheduled_tasks' in rule.rule:
                scheduled_routes.append(rule.rule)
        
        print(f"找到 {len(scheduled_routes)} 个scheduled_tasks相关路由:")
        for route in scheduled_routes:
            print(f"  - {route}")
        
        # 5. 检查特定路由
        print("5. 检查特定路由...")
        test_routes = [
            '/api/scheduled-tasks/test-route',
            '/api/scheduled-tasks/ai-generate-keywords'
        ]
        
        for route in test_routes:
            try:
                with app.test_client() as client:
                    if 'ai-generate-keywords' in route:
                        response = client.post(route, json={'event_id': 1})
                    else:
                        response = client.get(route)
                    print(f"  {route}: {response.status_code}")
            except Exception as e:
                print(f"  {route}: 错误 - {e}")
        
        print("=== 调试完成 ===")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_app()
