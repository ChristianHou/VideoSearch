# -*- coding: utf-8 -*-
"""
为兼容旧入口保留的文件。请使用 run.py 启动服务：
    python run.py
"""

from app import create_app
import os

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
