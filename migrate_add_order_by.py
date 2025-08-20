#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为tasks表添加order_by字段
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """执行数据库迁移"""
    # 获取数据库文件路径
    db_path = Path(__file__).parent / "video_search.db"
    
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        print("请先启动应用，让数据库自动创建")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查order_by字段是否已存在
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'order_by' in columns:
            print("order_by字段已存在，无需迁移")
            return True
        
        # 添加order_by字段
        print("正在添加order_by字段...")
        cursor.execute("ALTER TABLE tasks ADD COLUMN order_by TEXT DEFAULT 'relevance'")
        
        # 更新现有记录的order_by字段为默认值
        cursor.execute("UPDATE tasks SET order_by = 'relevance' WHERE order_by IS NULL")
        
        # 提交更改
        conn.commit()
        print("✅ 数据库迁移完成！")
        print("  - 为tasks表添加了order_by字段")
        print("  - 设置默认值为'relevance'")
        print("  - 更新了所有现有记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("开始数据库迁移...")
    success = migrate_database()
    if success:
        print("迁移脚本执行完成！")
    else:
        print("迁移脚本执行失败！")
        exit(1)
