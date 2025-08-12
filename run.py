# -*- coding: utf-8 -*-

import os
from app import create_app

if __name__ == '__main__':
    # 开发环境设置（生产禁用）
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

    app = create_app()
    print('YouTube搜索API服务器启动中...')
    print('访问 http://localhost:5000 开始使用')
    app.run(host='0.0.0.0', port=5000, debug=True)
