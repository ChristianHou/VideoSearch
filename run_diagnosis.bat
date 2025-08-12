@echo off
echo 网络诊断工具启动中...
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
pip install requests

echo.
echo 启动网络诊断...
echo 这将帮助诊断WinError 10060等网络问题
echo.
python network_diagnosis.py

echo.
pause
