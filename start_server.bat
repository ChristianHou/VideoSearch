@echo off
echo YouTube搜索API管理平台启动中...
echo.
echo 正在检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo.
echo 正在安装依赖包...
pip install -r requirements.txt

echo.
echo 启动服务器...
echo 服务器将在 http://localhost:5000 启动
echo 按 Ctrl+C 停止服务器
echo.
python app.py

pause
