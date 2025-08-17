#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import signal
import sys

# 加载环境变量
try:
    from load_env import load_env_file
    load_env_file()
except ImportError:
    print("⚠️  无法导入 load_env，请确保 .env 文件存在")
except Exception as e:
    print(f"⚠️  环境变量加载失败: {e}")

from app import create_app
from app.scheduler import start_scheduler, stop_scheduler

def signal_handler(sig, frame):
    """处理退出信号"""
    print('\n正在关闭服务器...')
    stop_scheduler()
    sys.exit(0)

if __name__ == '__main__':
    # 生产环境设置
    os.environ['FLASK_ENV'] = 'production'
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = create_app()
    
    # 启动定时任务调度器
    start_scheduler()
    
    print('\n🚀 生产环境服务器启动成功!')
    print('📍 访问地址: http://localhost:5000')
    print('📅 事件管理: http://localhost:5000/events')
    print('⏰ 定时任务调度器已启动')
    print('💡 按 Ctrl+C 退出\n')
    
    # 生产环境：禁用调试模式
    app.run(host='0.0.0.0', port=5000, debug=False)
