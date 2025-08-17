# DeepSeek AI服务集成说明

## 概述

本项目已将 `deepseek_demo.py` 重写为 `deepseek_service.py`，并集成到现有的服务架构中。新的服务架构提供了更好的代码组织、错误处理和配置管理。

## 文件结构

```
app/
├── services/
│   ├── deepseek_service.py      # 新的DeepSeek服务
│   ├── feishu_service.py        # 飞书服务
│   ├── translate_service.py     # 翻译服务
│   └── youtube_service.py       # YouTube服务
├── config.py                    # 配置文件（已更新）
└── __init__.py                  # 应用初始化（已更新）
```

## 主要改进

### 1. 服务架构集成
- 遵循现有的服务模式（如 `feishu_service.py`、`translate_service.py`）
- 统一的初始化和配置管理
- 全局服务实例管理

### 2. 配置管理
- 支持环境变量配置
- 可配置的启用/禁用开关
- 默认API密钥配置

### 3. 错误处理
- 完善的异常处理机制
- 连接测试功能
- 详细的日志记录

### 4. 代码质量
- 类型注解支持
- 文档字符串
- 模块化设计

## 配置选项

### 环境变量
```bash
# DeepSeek API密钥
export DEEPSEEK_API_KEY="your-api-key-here"

# 启用/禁用服务
export DEEPSEEK_ENABLED="true"
```

### 默认配置
```python
# app/config.py
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-d8df0e062ff34baf88920907ca156010')
DEEPSEEK_ENABLED = os.environ.get('DEEPSEEK_ENABLED', 'true').lower() == 'true'
```

## 使用方法

### 1. 服务初始化
```python
from app.services.deepseek_service import init_deepseek_service, get_deepseek_service

# 初始化服务
init_deepseek_service()

# 获取服务实例
service = get_deepseek_service()
```

### 2. 生成关键词
```python
if service:
    event_info = {
        'name': '事件名称',
        'event_type': '事件类型',
        'countries': ['国家1', '国家2'],
        'domains': ['领域1', '领域2'],
        # ... 其他字段
    }
    
    keywords = service.generate_keywords_from_event(event_info)
    if keywords:
        print(f"生成的关键词: {keywords}")
```

### 3. 连接测试
```python
if service.test_connection():
    print("API连接正常")
else:
    print("API连接失败")
```

## API端点

### POST /api/scheduled-tasks/ai-generate-keywords
- **功能**: 根据事件信息生成YouTube搜索关键词
- **请求体**: `{"event_id": 123}`
- **响应**: 
  ```json
  {
    "success": true,
    "keywords": "生成的关键词",
    "event_info": {
      "name": "事件名称",
      "type": "事件类型",
      "countries": ["国家列表"],
      "domains": ["领域列表"]
    }
  }
  ```

## 依赖要求

```txt
openai>=1.0.0
```

## 迁移说明

### 从 deepseek_demo.py 迁移
1. **删除旧文件**: `deepseek_demo.py` 不再需要
2. **更新导入**: 使用新的服务模块
3. **配置更新**: 通过环境变量或配置文件管理API密钥

### 代码变更示例
```python
# 旧代码
from openai import OpenAI
client = OpenAI(api_key="...", base_url="https://api.deepseek.com")

# 新代码
from app.services.deepseek_service import get_deepseek_service
service = get_deepseek_service()
keywords = service.generate_keywords_from_event(event_info)
```

## 故障排除

### 常见问题

1. **服务未初始化**
   - 检查 `DEEPSEEK_ENABLED` 配置
   - 确认服务在应用启动时已初始化

2. **API连接失败**
   - 验证API密钥是否正确
   - 检查网络连接
   - 确认DeepSeek服务状态

3. **关键词生成失败**
   - 检查事件信息是否完整
   - 查看服务日志
   - 验证API配额

### 调试方法
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 测试服务连接
service = get_deepseek_service()
if service:
    print(f"服务状态: {'正常' if service.test_connection() else '异常'}")
```

## 性能优化

1. **连接池**: 复用OpenAI客户端实例
2. **缓存**: 可考虑添加关键词缓存机制
3. **异步**: 支持异步调用以提高性能

## 安全考虑

1. **API密钥管理**: 使用环境变量存储敏感信息
2. **访问控制**: 限制API端点访问权限
3. **日志安全**: 避免在日志中记录敏感信息

## 未来扩展

1. **多模型支持**: 支持不同的AI模型
2. **批量处理**: 支持批量关键词生成
3. **结果缓存**: 实现关键词结果缓存
4. **质量评估**: 添加关键词质量评估功能
