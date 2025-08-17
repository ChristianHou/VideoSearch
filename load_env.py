#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量加载脚本
使用python-dotenv安全加载环境变量
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv 未安装，将使用基础环境变量加载")


def load_env_file():
    """加载 .env 文件到环境变量"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env 文件不存在")
        print("请复制 env.example 为 .env 并填入正确的配置值")
        print("或者运行: cp env.example .env")
        return False
    
    try:
        if DOTENV_AVAILABLE:
            # 使用python-dotenv加载
            load_dotenv(env_file)
            print("✅ 环境变量加载成功 (使用python-dotenv)")
        else:
            # 基础环境变量加载
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ 环境变量加载成功 (基础方式)")
        
        return True
        
    except Exception as e:
        print(f"❌ 加载环境变量失败: {e}")
        return False


if __name__ == "__main__":
    load_env_file()
