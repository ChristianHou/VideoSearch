# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
import requests
import datetime


utils_bp = Blueprint('utils', __name__)


@utils_bp.get('/network-test')
def test_network():
    try:
        response = requests.get('https://www.google.com', timeout=10)
        google_status = "正常" if response.status_code == 200 else f"状态码: {response.status_code}"
    except Exception as e:
        google_status = f"连接失败: {str(e)}"

    try:
        response = requests.get('https://www.googleapis.com/discovery/v1/apis', timeout=10)
        api_status = "正常" if response.status_code == 200 else f"状态码: {response.status_code}"
    except Exception as e:
        api_status = f"连接失败: {str(e)}"

    return jsonify({
        "success": True,
        "network_test": {
            "google": google_status,
            "youtube_api": api_status,
            "timestamp": datetime.datetime.now().isoformat()
        }
    })


@utils_bp.get('/regions')
def get_regions():
    regions = [
        {"code": "US", "name": "美国"},
        {"code": "GB", "name": "英国"},
        {"code": "CA", "name": "加拿大"},
        {"code": "AU", "name": "澳大利亚"},
        {"code": "DE", "name": "德国"},
        {"code": "FR", "name": "法国"},
        {"code": "JP", "name": "日本"},
        {"code": "KR", "name": "韩国"},
        {"code": "CN", "name": "中国"},
        {"code": "IN", "name": "印度"},
        {"code": "BR", "name": "巴西"},
        {"code": "MX", "name": "墨西哥"}
    ]
    return jsonify({"success": True, "regions": regions})


@utils_bp.get('/languages')
def get_languages():
    languages = [
        {"code": "en", "name": "英语"},
        {"code": "zh", "name": "中文"},
        {"code": "ja", "name": "日语"},
        {"code": "ko", "name": "韩语"},
        {"code": "de", "name": "德语"},
        {"code": "fr", "name": "法语"},
        {"code": "es", "name": "西班牙语"},
        {"code": "pt", "name": "葡萄牙语"},
        {"code": "ru", "name": "俄语"},
        {"code": "ar", "name": "阿拉伯语"}
    ]
    return jsonify({"success": True, "languages": languages})
