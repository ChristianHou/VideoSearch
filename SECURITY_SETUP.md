# 🔐 安全配置说明

## 🚨 重要安全提醒

**⚠️ 请立即更改所有已暴露的API密钥！**

由于之前的代码中包含了硬编码的API密钥，这些密钥已经被提交到Git仓库中，存在严重的安全风险。请按照以下步骤进行安全配置：

## 📋 需要更改的密钥

1. **DeepSeek API密钥** - 已在代码中暴露
2. **飞书应用密钥** - 已在代码中暴露  
3. **火山引擎访问密钥** - 已在代码中暴露
4. **Google OAuth客户端密钥** - 已在代码中暴露

## 🛡️ 安全配置步骤

### 1. 创建环境变量文件

复制 `env.example` 为 `.env`：

```bash
cp env.example .env
```

### 2. 编辑 .env 文件

填入正确的配置值（**不要使用示例中的值**）：

```bash
# 应用配置
APP_SECRET_KEY=your-actual-secret-key-here

# Google OAuth/YouTube配置
GOOGLE_CLIENT_SECRETS_FILE=./config/client_secret.json

# 飞书配置
FEISHU_APP_ID=your-actual-feishu-app-id
FEISHU_APP_SECRET=your-actual-feishu-app-secret
FEISHU_CHAT_ID=your-actual-feishu-chat-id

# 火山引擎翻译配置
VOLC_ACCESS_KEY=your-actual-volcengine-access-key
VOLC_SECRET_KEY=your-actual-volcengine-secret-key

# DeepSeek AI配置
DEEPSEEK_API_KEY=your-actual-deepseek-api-key
```

### 3. 配置Google OAuth

复制 `config/client_secret.example.json` 为 `config/client_secret.json`：

```bash
cp config/client_secret.example.json config/client_secret.json
```

然后编辑 `config/client_secret.json`，填入正确的Google OAuth配置。

### 4. 验证配置

运行应用时，系统会自动验证配置：

```bash
python run.py
```

如果配置正确，会显示 "✅ 配置验证通过"。

## 🔒 安全最佳实践

### 1. 环境变量管理

- ✅ 使用 `.env` 文件存储敏感配置
- ✅ `.env` 文件已添加到 `.gitignore`
- ❌ 不要在代码中硬编码任何密钥
- ❌ 不要将 `.env` 文件提交到Git仓库

### 2. 生产环境配置

- 使用环境变量或配置管理系统
- 定期轮换API密钥
- 使用最小权限原则
- 监控API使用情况

### 3. 密钥轮换

如果密钥已经暴露，请：

1. 立即在相应平台禁用旧密钥
2. 生成新的API密钥
3. 更新 `.env` 文件
4. 测试新配置是否工作正常

## 🚀 快速开始

1. **复制配置模板**：
   ```bash
   cp env.example .env
   cp config/client_secret.example.json config/client_secret.json
   ```

2. **编辑配置文件**，填入正确的值

3. **启动应用**：
   ```bash
   python run.py
   ```

## 📞 技术支持

如果遇到配置问题，请检查：

1. `.env` 文件是否存在
2. 所有必需的配置项是否已填写
3. 配置文件格式是否正确
4. 环境变量是否正确加载

## 🔍 配置验证

系统启动时会自动验证配置，如果发现问题会显示详细的错误信息，帮助您快速定位问题。
