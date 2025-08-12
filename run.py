# -*- coding: utf-8 -*-

import os
import signal
import sys
from app import create_app
from app.scheduler import start_scheduler, stop_scheduler

def signal_handler(sig, frame):
    """处理退出信号"""
    print('\n正在关闭服务器...')
    stop_scheduler()
    sys.exit(0)

if __name__ == '__main__':
    # 开发环境设置（生产禁用）
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = create_app()
    
    # 启动定时任务调度器
    start_scheduler()
    
    print('YouTube搜索API服务器启动中...')
    print('定时任务调度器已启动')
    print('访问 http://localhost:5000 开始使用')
    print('按 Ctrl+C 退出')
    
    app.run(host='0.0.0.0', port=5000, debug=True)
