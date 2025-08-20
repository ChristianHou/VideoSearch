#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    from app import create_app
    app = create_app()
    print('✅ 应用创建成功')
    print('注册的路由:')
    for rule in app.url_map._rules:
        print(f'  {rule.rule} -> {rule.endpoint}')
    
    # 检查爬虫相关路由
    crawler_routes = [rule for rule in app.url_map._rules if 'crawler' in rule.endpoint]
    if crawler_routes:
        print('\n✅ 爬虫路由注册成功:')
        for rule in crawler_routes:
            print(f'  {rule.rule} -> {rule.endpoint}')
    else:
        print('\n❌ 未找到爬虫路由')
        
except Exception as e:
    print(f'❌ 应用创建失败: {e}')
    import traceback
    traceback.print_exc()
