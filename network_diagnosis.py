#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络诊断脚本 - 帮助诊断WinError 10060等网络问题
"""

import os
import sys
import socket
import requests
import subprocess
import platform
from datetime import datetime

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_section(title):
    """打印章节标题"""
    print(f"\n--- {title} ---")

def check_python_environment():
    """检查Python环境"""
    print_section("Python环境检查")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")
    
    # 检查网络相关环境变量
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'REQUESTS_CA_BUNDLE']
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"{var}: {value}")
        else:
            print(f"{var}: 未设置")

def check_system_info():
    """检查系统信息"""
    print_section("系统信息")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"系统版本: {platform.version()}")
    print(f"机器类型: {platform.machine()}")
    print(f"处理器: {platform.processor()}")

def check_network_interfaces():
    """检查网络接口"""
    print_section("网络接口信息")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, encoding='gbk')
            if result.returncode == 0:
                print("网络配置信息:")
                print(result.stdout)
            else:
                print("无法获取网络配置信息")
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            if result.returncode == 0:
                print("网络接口信息:")
                print(result.stdout)
            else:
                print("无法获取网络接口信息")
    except Exception as e:
        print(f"获取网络接口信息失败: {e}")

def test_dns_resolution():
    """测试DNS解析"""
    print_section("DNS解析测试")
    test_hosts = [
        'www.google.com',
        'www.youtube.com',
        'www.googleapis.com',
        'accounts.google.com'
    ]
    
    for host in test_hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"✓ {host} -> {ip}")
        except socket.gaierror as e:
            print(f"✗ {host} -> DNS解析失败: {e}")

def test_network_connectivity():
    """测试网络连接"""
    print_section("网络连接测试")
    test_urls = [
        'https://www.google.com',
        'https://www.youtube.com',
        'https://youtube.googleapis.com',
        'https://accounts.google.com'
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✓ {url} -> 状态码: {response.status_code}")
            else:
                print(f"⚠ {url} -> 状态码: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"✗ {url} -> 连接超时")
        except requests.exceptions.ConnectionError as e:
            print(f"✗ {url} -> 连接失败: {e}")
        except Exception as e:
            print(f"✗ {url} -> 错误: {e}")

def test_ping():
    """测试ping连接"""
    print_section("Ping测试")
    test_hosts = ['www.google.com', '8.8.8.8']
    
    for host in test_hosts:
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['ping', '-n', '3', host], capture_output=True, text=True, encoding='gbk')
            else:
                result = subprocess.run(['ping', '-c', '3', host], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ {host} -> Ping成功")
                # 显示ping结果摘要
                lines = result.stdout.split('\n')
                for line in lines:
                    if '时间=' in line or 'time=' in line:
                        print(f"  {line.strip()}")
            else:
                print(f"✗ {host} -> Ping失败")
        except Exception as e:
            print(f"✗ {host} -> Ping测试异常: {e}")

def test_traceroute():
    """测试路由跟踪"""
    print_section("路由跟踪测试")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['tracert', '-h', '10', 'www.google.com'], capture_output=True, text=True, encoding='gbk')
        else:
            result = subprocess.run(['traceroute', '-m', '10', 'www.google.com'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("路由跟踪结果:")
            print(result.stdout)
        else:
            print("路由跟踪失败")
    except Exception as e:
        print(f"路由跟踪测试异常: {e}")

def check_firewall():
    """检查防火墙状态"""
    print_section("防火墙检查")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], capture_output=True, text=True, encoding='gbk')
            if result.returncode == 0:
                print("Windows防火墙状态:")
                print(result.stdout)
            else:
                print("无法获取防火墙状态")
        else:
            print("非Windows系统，跳过防火墙检查")
    except Exception as e:
        print(f"防火墙检查失败: {e}")

def check_proxy_settings():
    """检查代理设置"""
    print_section("代理设置检查")
    
    # 检查系统代理
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY']
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"环境变量 {var}: {value}")
        else:
            print(f"环境变量 {var}: 未设置")
    
    # 检查Windows注册表代理设置
    if platform.system() == "Windows":
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                try:
                    proxy_enable = winreg.QueryValueEx(key, "ProxyEnable")[0]
                    if proxy_enable:
                        proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                        print(f"Windows代理已启用: {proxy_server}")
                    else:
                        print("Windows代理已禁用")
                except FileNotFoundError:
                    print("Windows代理设置未找到")
        except Exception as e:
            print(f"检查Windows代理设置失败: {e}")

def generate_report():
    """生成诊断报告"""
    print_header("网络诊断报告")
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_system_info()
    check_python_environment()
    check_network_interfaces()
    test_dns_resolution()
    test_network_connectivity()
    test_ping()
    test_traceroute()
    check_firewall()
    check_proxy_settings()
    
    print_header("诊断完成")
    print("如果发现问题，请参考 NETWORK_TROUBLESHOOTING.md 文件")
    print("常见解决方案:")
    print("1. 检查防火墙设置")
    print("2. 检查代理配置")
    print("3. 尝试使用VPN")
    print("4. 更换DNS服务器")
    print("5. 重启网络服务")

def main():
    """主函数"""
    try:
        generate_report()
    except KeyboardInterrupt:
        print("\n\n诊断被用户中断")
    except Exception as e:
        print(f"\n诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
