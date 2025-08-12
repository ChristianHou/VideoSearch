# YouTube搜索API管理平台启动脚本
Write-Host "YouTube搜索API管理平台启动中..." -ForegroundColor Green
Write-Host ""

# 检查Python环境
Write-Host "正在检查Python环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: 未找到Python，请先安装Python 3.7+" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "正在安装依赖包..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "启动服务器..." -ForegroundColor Green
Write-Host "服务器将在 http://localhost:5000 启动" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

# 启动Flask应用
python app.py

Read-Host "按回车键退出"
