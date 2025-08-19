#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time

def test_navigation():
    """测试所有页面的导航功能"""
    
    base_url = "http://localhost:5000"
    pages = [
        {"name": "首页 (YouTube搜索)", "url": "/", "expected_title": "YouTube搜索API管理平台"},
        {"name": "事件管理", "url": "/events", "expected_title": "事件管理系统"},
        {"name": "视频下载", "url": "/downloads", "expected_title": "YouTube视频下载"}
    ]
    
    print("🧭 正在测试页面导航功能...")
    print("=" * 50)
    
    for page in pages:
        try:
            print(f"\n📄 测试页面: {page['name']}")
            print(f"🔗 URL: {base_url}{page['url']}")
            
            # 发送请求
            response = requests.get(f"{base_url}{page['url']}")
            
            if response.status_code == 200:
                print(f"✅ 状态码: {response.status_code}")
                
                # 检查页面标题
                if page['expected_title'] in response.text:
                    print(f"✅ 页面标题正确: {page['expected_title']}")
                else:
                    print(f"⚠️  页面标题可能不正确")
                
                # 检查导航栏链接
                nav_links = [
                    ('/">', 'YouTube搜索'),
                    ('/events">', '事件管理'),
                    ('/downloads">', '视频下载')
                ]
                
                missing_links = []
                for link_url, link_text in nav_links:
                    if link_url in response.text and link_text in response.text:
                        print(f"✅ 导航链接: {link_text}")
                    else:
                        missing_links.append(link_text)
                
                if missing_links:
                    print(f"❌ 缺失的导航链接: {', '.join(missing_links)}")
                else:
                    print("✅ 所有导航链接正常")
                
            else:
                print(f"❌ 状态码错误: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败：无法连接到服务器")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
        
        # 添加延迟避免请求过快
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("🎯 导航测试完成！")
    print("\n📋 测试结果说明:")
    print("✅ 状态码 200: 页面正常加载")
    print("✅ 页面标题: 页面内容正确")
    print("✅ 导航链接: 所有页面都能相互跳转")
    print("❌ 缺失链接: 需要检查导航栏代码")

if __name__ == "__main__":
    test_navigation()
