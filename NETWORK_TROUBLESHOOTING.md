# 网络故障排除指南

## 🔍 问题描述
遇到 `WinError 10060` 错误，表示网络连接超时或连接失败。

## 🛠️ 解决方案

### 1. 基本网络检查

#### 检查网络连接
```bash
# 测试基本网络连接
ping www.google.com
ping www.youtube.com

# 测试DNS解析
nslookup www.google.com
```

#### 检查防火墙设置
- Windows防火墙可能阻止了Python或Flask的网络访问
- 临时禁用防火墙测试，或添加Python到防火墙白名单

### 2. 代理设置检查

#### 检查系统代理
```bash
# 查看当前代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

#### 检查Python代理设置
```python
import os
print("HTTP_PROXY:", os.environ.get('HTTP_PROXY'))
print("HTTPS_PROXY:", os.environ.get('HTTPS_PROXY'))
```

### 3. 网络配置优化

#### 修改hosts文件
如果DNS解析有问题，可以尝试修改hosts文件：
```
# C:\Windows\System32\drivers\etc\hosts
8.8.8.8 www.google.com
8.8.8.8 www.googleapis.com
```

#### 使用公共DNS
- Google DNS: 8.8.8.8, 8.8.4.4
- Cloudflare DNS: 1.1.1.1, 1.0.0.1

### 4. 应用程序优化

#### 增加超时时间
应用程序已配置了重试机制和超时设置：
- 连接超时: 10秒
- 读取超时: 30秒
- 重试次数: 3次
- 指数退避策略

#### 网络测试功能
使用界面中的"网络测试"按钮检查连接状态。

### 5. 环境变量设置

#### 设置网络相关环境变量
```bash
# Windows PowerShell
$env:REQUESTS_CA_BUNDLE = "path\to\cacert.pem"
$env:HTTP_PROXY = "http://proxy:port"
$env:HTTPS_PROXY = "http://proxy:port"

# Windows CMD
set REQUESTS_CA_BUNDLE=path\to\cacert.pem
set HTTP_PROXY=http://proxy:port
set HTTPS_PROXY=http://proxy:port
```

### 6. 高级故障排除

#### 使用curl测试
```bash
# 测试Google连接
curl -v https://www.google.com

# 测试YouTube API
curl -v https://www.googleapis.com/discovery/v1/apis
```

#### 检查SSL证书
```bash
# 检查SSL连接
openssl s_client -connect www.googleapis.com:443
```

#### 网络诊断工具
```bash
# 路由跟踪
tracert www.google.com

# 网络配置
ipconfig /all
```

### 7. 常见解决方案

#### 方案1: 重启网络服务
```bash
# 重启网络适配器
netsh winsock reset
netsh int ip reset
ipconfig /flushdns
```

#### 方案2: 检查杀毒软件
某些杀毒软件可能阻止网络连接，尝试：
- 临时禁用杀毒软件
- 将Python添加到杀毒软件白名单
- 检查杀毒软件的网络保护设置

#### 方案3: 使用VPN
如果网络有地理限制，尝试：
- 使用VPN服务
- 更换网络环境
- 使用移动热点测试

### 8. 开发环境特定问题

#### Flask开发服务器
```python
# 修改Flask运行配置
app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
```

#### 环境变量设置
```python
# 在代码中设置环境变量
os.environ['REQUESTS_CA_BUNDLE'] = 'path/to/cacert.pem'
os.environ['HTTP_PROXY'] = 'http://proxy:port'
os.environ['HTTPS_PROXY'] = 'http://proxy:port'
```

### 9. 监控和日志

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 网络请求监控
应用程序已添加网络测试API端点：
- `GET /api/network-test` - 测试网络连接状态

### 10. 联系支持

如果以上方法都无法解决问题，请提供：
- 错误日志
- 网络测试结果
- 系统环境信息
- 网络配置详情

## 📞 获取帮助

- 检查网络测试结果
- 查看应用程序日志
- 尝试不同的网络环境
- 联系网络管理员

## 🔄 预防措施

1. 定期检查网络连接
2. 配置合适的超时时间
3. 实现重试机制
4. 监控网络状态
5. 保持系统更新
