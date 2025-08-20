# 视频爬虫模块使用说明

## 概述

视频爬虫模块是一个强大的网站视频信息爬取工具，支持多种爬取策略和配置选项。该模块集成了 `crawl4ai` 库，提供高效的异步爬取能力，同时支持传统的 BeautifulSoup 解析作为备用方案。

## 主要功能

### 1. 网站管理
- **添加网站**: 支持自定义爬取模式和解析策略
- **编辑网站**: 修改网站信息和爬取配置
- **删除网站**: 安全删除网站（检查关联任务）
- **网站模板**: 内置 YouTube、Bilibili 等网站模板

### 2. 爬取任务管理
- **手动任务**: 立即执行的爬取任务
- **定时任务**: 按计划执行的爬取任务
- **任务状态**: 实时监控任务执行状态
- **结果查看**: 查看爬取到的视频信息

### 3. 爬取配置
- **解析策略**: 自动解析或自定义CSS选择器
- **翻译支持**: 自动翻译为中文（双语显示）
- **元数据获取**: 可选的缩略图、时长、观看数等信息
- **爬取控制**: 页数限制、请求间隔等参数

## 使用方法

### 1. 添加网站

#### 自动解析模式
```json
{
    "name": "示例网站",
    "url": "https://example.com",
    "description": "网站描述",
    "crawl_pattern": "general",
    "parse_strategy": "auto"
}
```

#### 自定义选择器模式
```json
{
    "name": "自定义网站",
    "url": "https://example.com",
    "description": "网站描述",
    "crawl_pattern": "custom",
    "parse_strategy": "custom",
    "container_selector": ".video-item",
    "title_selector": ".title",
    "url_selector": "a[href]",
    "description_selector": ".description",
    "thumbnail_selector": "img"
}
```

### 2. 创建爬取任务

```json
{
    "name": "爬取任务名称",
    "website_id": 1,
    "task_type": "manual",
    "crawl_config": {
        "enable_translation": true,
        "enable_thumbnail": true,
        "enable_metadata": false,
        "max_pages": 1,
        "delay_between_requests": 1.0
    }
}
```

### 3. 爬取配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_translation` | boolean | true | 是否启用翻译（中英文双语） |
| `enable_thumbnail` | boolean | false | 是否获取缩略图 |
| `enable_metadata` | boolean | false | 是否获取元数据（时长、观看数等） |
| `max_pages` | integer | 1 | 最大爬取页数（1-10） |
| `delay_between_requests` | float | 1.0 | 请求间隔时间（秒） |

## 技术架构

### 1. 爬取引擎
- **主要引擎**: `crawl4ai` - 高性能异步爬取
- **备用引擎**: `aiohttp` + `BeautifulSoup` - 传统解析方案
- **自动回退**: 当 crawl4ai 失败时自动切换到备用方案

### 2. 数据流程
```
网站配置 → 爬取任务 → 爬取执行 → 数据解析 → 翻译处理 → 结果存储
```

### 3. 异步处理
- 使用 `asyncio` 进行异步爬取
- 多线程任务执行
- 非阻塞式操作

## API 接口

### 网站管理
- `GET /api/crawler/websites` - 获取网站列表
- `POST /api/crawler/websites` - 创建新网站
- `PUT /api/crawler/websites/<id>` - 更新网站
- `DELETE /api/crawler/websites/<id>` - 删除网站

### 任务管理
- `GET /api/crawler/tasks` - 获取任务列表
- `POST /api/crawler/tasks` - 创建新任务
- `GET /api/crawler/tasks/<id>/videos` - 获取任务结果
- `POST /api/crawler/tasks/<id>/execute` - 执行任务

### 系统信息
- `GET /api/crawler/supported-websites` - 获取支持的网站模板

## 使用示例

### 1. 爬取 YouTube 视频

```python
# 1. 添加 YouTube 网站
website_data = {
    "name": "YouTube",
    "url": "https://www.youtube.com",
    "crawl_pattern": "youtube",
    "parse_strategy": "custom"
}

# 2. 创建爬取任务
task_data = {
    "name": "YouTube 热门视频",
    "website_id": website_id,
    "task_type": "manual",
    "crawl_config": {
        "enable_translation": True,
        "max_pages": 2
    }
}
```

### 2. 自定义网站爬取

```python
# 1. 添加自定义网站
website_data = {
    "name": "自定义视频网站",
    "url": "https://custom-video-site.com",
    "parse_strategy": "custom",
    "container_selector": ".video-container",
    "title_selector": ".video-title",
    "url_selector": "a.video-link",
    "description_selector": ".video-description"
}

# 2. 创建爬取任务
task_data = {
    "name": "自定义网站爬取",
    "website_id": website_id,
    "crawl_config": {
        "enable_translation": True,
        "delay_between_requests": 2.0
    }
}
```

## 注意事项

### 1. 爬取限制
- 请遵守网站的 robots.txt 规则
- 设置合理的请求间隔，避免被网站封禁
- 限制爬取页数，避免过度请求

### 2. 数据质量
- 自定义选择器需要根据具体网站结构调整
- 建议先在小范围测试，确认选择器正确性
- 翻译功能依赖外部服务，可能影响爬取速度

### 3. 错误处理
- 爬取失败时会自动记录错误信息
- 网络问题可能导致部分数据丢失
- 建议定期检查任务状态和错误日志

## 故障排除

### 1. 爬取失败
- 检查网站是否可访问
- 验证CSS选择器是否正确
- 查看错误日志获取详细信息

### 2. 数据不完整
- 确认网站结构是否发生变化
- 调整CSS选择器以匹配新结构
- 检查网络连接和请求限制

### 3. 性能问题
- 减少并发请求数量
- 增加请求间隔时间
- 使用更精确的CSS选择器

## 更新日志

- **v1.0.0**: 初始版本，支持基本爬取功能
- **v1.1.0**: 集成 crawl4ai，提升爬取性能
- **v1.2.0**: 添加自定义选择器支持
- **v1.3.0**: 完善配置管理和错误处理

## 技术支持

如有问题或建议，请通过以下方式联系：
- 提交 Issue 到项目仓库
- 查看项目文档和示例
- 参考错误日志和调试信息
