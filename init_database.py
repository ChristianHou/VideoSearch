# -*- coding: utf-8 -*-
"""
数据库初始化脚本
运行此脚本可以手动初始化数据库
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db

if __name__ == '__main__':
    print("正在初始化数据库...")
    try:
        init_db()
        print("数据库初始化成功！")
        print("数据库文件位置: video_search.db")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)
