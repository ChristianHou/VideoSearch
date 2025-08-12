# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, session, redirect, url_for
import google_auth_oauthlib.flow
import google.oauth2.credentials

from ..config import AppConfig
from ..utils.auth_utils import credentials_to_dict, global_credential_store


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        AppConfig.GOOGLE_CLIENT_SECRETS_FILE, scopes=AppConfig.YT_SCOPES)
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)


@auth_bp.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        AppConfig.GOOGLE_CLIENT_SECRETS_FILE, scopes=AppConfig.YT_SCOPES, state=state)
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)

    # 修复新版本API的兼容性问题
    try:
        # 新版本API
        flow.fetch_token(authorization_response=request.url)
    except TypeError:
        # 旧版本API
        flow.fetch_token(request.url)

    credentials = flow.credentials
    credentials_dict = credentials_to_dict(credentials)
    
    # 存储到session和数据库凭证存储
    session['credentials'] = credentials_dict
    global_credential_store.set_credentials(credentials_dict, user_id='default')
    
    return redirect(url_for('index'))


@auth_bp.route('/logout')
def logout():
    if 'credentials' in session:
        del session['credentials']
    # 清除数据库中的认证凭证
    global_credential_store.clear_credentials(user_id='default')
    
    # 返回一个简单的登出成功页面，然后重定向
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>登出成功</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h2 class="success">登出成功！</h2>
        <p>您已成功登出系统。</p>
        <script>
            // 延迟2秒后重定向到主页
            setTimeout(function() {
                window.location.href = '/';
            }, 2000);
        </script>
    </body>
    </html>
    '''


@auth_bp.route('/api/auth/status')
def auth_status():
    """检查认证状态"""
    try:
        # 从数据库检查认证状态
        is_authenticated = global_credential_store.is_authenticated(user_id='default')
        
        if is_authenticated:
            return jsonify({
                "success": True,
                "authenticated": True,
                "message": "用户已认证"
            })
        else:
            return jsonify({
                "success": True,
                "authenticated": False,
                "message": "用户未认证"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "authenticated": False,
            "error": str(e)
        })


@auth_bp.route('/api/auth/refresh')
def refresh_credentials():
    """手动刷新认证凭证"""
    try:
        credentials = global_credential_store.get_credentials(user_id='default')
        if credentials:
            return jsonify({
                "success": True,
                "message": "凭证刷新成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": "无法刷新凭证，请重新登录"
            }), 401
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
