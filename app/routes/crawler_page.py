#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

crawler_page_bp = Blueprint('crawler_page', __name__)

@crawler_page_bp.route('/crawler')
def crawler_page():
    """爬虫管理页面"""
    return render_template('crawler.html')
