#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

downloads_page_bp = Blueprint('downloads_page', __name__)

@downloads_page_bp.route('/downloads')
def downloads_page():
    """YouTube视频下载页面"""
    return render_template('downloads.html')
