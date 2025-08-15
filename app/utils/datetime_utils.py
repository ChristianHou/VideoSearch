# -*- coding: utf-8 -*-

import re
import datetime
from datetime import timezone, timedelta
from typing import Optional

# 东八区时区
EAST_8_TZ = timezone(timedelta(hours=8))

def get_east8_time():
    """获取东八区当前时间"""
    return datetime.datetime.now(EAST_8_TZ)


def normalize_rfc3339_date(date_str: str, end_of_day: bool = False) -> str:
    """将日期字符串规范化为RFC3339时间戳。

    接受格式:
    - YYYY-MM-DD
    - YYYY-MM-DDTHH:MM
    - YYYY-MM-DDTHH:MM:SS
    - YYYY-MM-DDTHH:MM:SSZ
    - 含偏移的ISO字符串
    """
    if not date_str:
        return date_str

    # 已包含Z或时区偏移
    if 'T' in date_str and (date_str.endswith('Z') or re.search(r"[\+\-]\d{2}:?\d{2}$", date_str)):
        return date_str

    # 仅日期: YYYY-MM-DD
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if m:
        return f"{date_str}T23:59:59Z" if end_of_day else f"{date_str}T00:00:00Z"

    # 包含时间的格式: YYYY-MM-DDTHH:MM 或 YYYY-MM-DDTHH:MM:SS
    if 'T' in date_str:
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        except Exception:
            return date_str

    # 其他情况尽量解析
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    except Exception:
        return date_str


def parse_rfc3339_datetime(ts: str) -> Optional[datetime.datetime]:
    try:
        if ts.endswith('Z'):
            ts = ts.replace('Z', '+00:00')
        return datetime.datetime.fromisoformat(ts)
    except Exception:
        return None
