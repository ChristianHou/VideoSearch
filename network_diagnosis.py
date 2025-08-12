#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
网络诊断脚本
用于诊断YouTube API连接问题
"""

import os
import sys
import requests
import socket
import subprocess
from urllib.parse import urlparse

def test_basic_connectivity():
    """测试基本网络连接"""
    print("=== 基本网络连接测试 ===")
    
    # 测试DNS解析
    try:
        ip = socket.gethostbyname('www.googleapis.com')
        print(f"✓ DNS解析成功: www.googleapis.com -> {ip}")
    except socket.gaierror as e:
        print(f"✗ DNS解析失败: {e}")
        return False
    
    # 测试端口连接
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('www.googleapis.com', 443))
        sock.close()
        if result == 0:
            print("✓ 端口443连接成功")
        else:
            print(f"✗ 端口443连接失败，错误码: {result}")
            return False
    except Exception as e:
        print(f"✗ 端口连接测试失败: {e}")
        return False
    
    return True

def test_http_requests():
    """测试HTTP请求"""
    print("\n=== HTTP请求测试 ===")
    
    # 测试Google APIs Discovery
    try:
        response = requests.get('https://www.googleapis.com/discovery/v1/apis', timeout=10)
        if response.status_code == 200:
            print("✓ Google APIs Discovery 连接成功")
        else:
            print(f"✗ Google APIs Discovery 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Google APIs Discovery 连接失败: {e}")
        return False
    
    # 测试YouTube Data API
    try:
        response = requests.get('https://www.googleapis.com/youtube/v3', timeout=10)
        if response.status_code in [200, 404]:  # 404也是正常的，表示端点存在
            print("✓ YouTube Data API 端点可访问")
        else:
            print(f"✗ YouTube Data API 状态码: {response.status_code}")
    except Exception as e:
        print(f"✗ YouTube Data API 连接失败: {e}")
    
    return True

def test_proxy_settings():
    """测试代理设置"""
    print("\n=== 代理设置检查 ===")
    
    # 检查环境变量
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"⚠ 发现代理设置: {var} = {value}")
        else:
            print(f"✓ 未设置代理: {var}")
    
    # 检查Windows代理设置
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
        proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
        if proxy_enable:
            proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
            print(f"⚠ Windows代理已启用: {proxy_server}")
        else:
            print("✓ Windows代理未启用")
        winreg.CloseKey(key)
    except Exception as e:
        print(f"无法检查Windows代理设置: {e}")
    
    return True  # 总是返回True，因为这只是检查，不是测试

def test_firewall():
    """测试防火墙设置"""
    print("\n=== 防火墙测试 ===")
    
    # 测试出站连接
    try:
        # 尝试连接到Google的多个端口
        ports = [80, 443, 8080]
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('8.8.8.8', port))
                sock.close()
                if result == 0:
                    print(f"✓ 出站连接测试成功: 8.8.8.8:{port}")
                else:
                    print(f"✗ 出站连接测试失败: 8.8.8.8:{port}, 错误码: {result}")
            except Exception as e:
                print(f"✗ 出站连接测试异常: {e}")
    except Exception as e:
        print(f"防火墙测试失败: {e}")

def test_python_network():
    """测试Python网络库"""
    print("\n=== Python网络库测试 ===")
    
    try:
        import httplib2
        print("✓ httplib2 库可用")
        
        # 测试httplib2连接
        http = httplib2.Http(timeout=10)
        try:
            response, content = http.request('https://www.googleapis.com/discovery/v1/apis')
            if response.status == 200:
                print("✓ httplib2 连接测试成功")
            else:
                print(f"✗ httplib2 连接测试失败，状态码: {response.status}")
        except Exception as e:
            print(f"✗ httplib2 连接测试异常: {e}")
            
    except ImportError:
        print("✗ httplib2 库不可用")
    except Exception as e:
        print(f"✗ httplib2 测试失败: {e}")

def main():
    """主函数"""
    print("YouTube API 网络诊断工具")
    print("=" * 50)
    
    # 运行所有测试
    tests = [
        test_basic_connectivity,
        test_http_requests,
        test_proxy_settings,
        test_firewall,
        test_python_network
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试 {test.__name__} 异常: {e}")
            results.append(False)
    
    # 总结
    print("\n" + "=" * 50)
    print("诊断结果总结:")
    passed = sum(results)
    total = len(results)
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有网络测试通过！")
        print("如果仍然遇到问题，可能是认证或API配额问题。")
    else:
        print("⚠️ 部分测试失败，请根据上述信息检查网络配置。")
        print("\n建议解决方案:")
        print("1. 检查系统代理设置")
        print("2. 检查防火墙配置")
        print("3. 尝试使用VPN或更换网络环境")
        print("4. 联系网络管理员")

if __name__ == '__main__':
    main()
