#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
事件管理数据库初始化脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import init_db
from app.models import Event, EventScheduledTask

def main():
    """主函数"""
    print("🚀 开始初始化事件管理数据库...")
    
    try:
        # 初始化数据库
        init_db()
        print("✅ 数据库初始化完成")
        
        print("📋 数据库表结构:")
        print("  - events: 事件管理表")
        print("  - event_scheduled_tasks: 事件与定时任务关联表")
        print("  - 其他现有表保持不变")
        
        print("\n🎉 事件管理数据库初始化成功！")
        print("现在可以启动应用并访问 /events 页面了")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
