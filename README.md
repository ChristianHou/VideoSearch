# YouTube搜索API管理平台

该项目已重构为模块化分层结构：

## 目录结构
```
VideoSearch/
├── app/                      # 应用包
│   ├── __init__.py           # 应用工厂，注册蓝图
│   ├── config.py             # 配置
│   ├── templates/            # 模板
│   │   └── index.html
│   ├── routes/               # 路由（蓝图）
│   │   ├── auth.py           # 认证相关
│   │   ├── tasks.py          # 任务管理API
│   │   └── utils.py          # 工具接口
│   ├── services/             # 业务服务
│   │   └── youtube_service.py
│   ├── store/                # 存储（内存版）
│   │   └── task_store.py
│   └── utils/                # 工具函数
│       ├── datetime_utils.py
│       └── auth_utils.py
├── run.py                    # 新的启动入口
├── app.py                    # 兼容旧入口（建议使用 run.py）
├── requirements.txt
├── README.md
└── templates/                # 旧模板目录（仍保留）
    └── index.html
```

## 启动
```bash
python run.py
```

或兼容旧方式：
```bash
python app.py
```

## API 入口
- 网页: `GET /`
- 任务: `GET/POST /api/tasks`, `GET/DELETE /api/tasks/<id>`, `POST /api/tasks/<id>/execute`
- 地区语言: `GET /api/regions`, `GET /api/languages`
- 网络测试: `GET /api/network-test`
- 认证: `GET /authorize`, `GET /oauth2callback`, `GET /logout`

## 变更亮点
- 拆分路由、服务、工具与存储，`app.py` 不再承载所有逻辑
- 使用应用工厂与蓝图，结构清晰、易维护
- 后端自动规范日期为 RFC3339 格式，避免 400 错误
