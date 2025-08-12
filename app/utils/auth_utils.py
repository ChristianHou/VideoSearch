# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from ..config import AppConfig
from ..database import db_manager
from ..models import AuthCredentials, get_east8_time


def credentials_to_dict(credentials):
    """将Credentials对象转换为字典"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }


def dict_to_credentials(credentials_dict):
    """将字典转换为Credentials对象"""
    expiry = None
    if credentials_dict.get('expiry'):
        try:
            expiry = datetime.fromisoformat(credentials_dict['expiry'])
        except:
            pass
    
    return Credentials(
        token=credentials_dict.get('token'),
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict.get('token_uri'),
        client_id=credentials_dict.get('client_id'),
        client_secret=credentials_dict.get('client_secret'),
        scopes=credentials_dict.get('scopes'),
        expiry=expiry
    )


class DatabaseCredentialStore:
    """基于数据库的凭证存储，支持持久化和自动刷新"""
    
    def __init__(self):
        self._cached_credentials = None
        self._cache_timestamp = None
        self._cache_duration = timedelta(minutes=1)  # 缓存1分钟
    
    def _get_db_session(self):
        """获取数据库会话"""
        return db_manager.get_session()
    
    def _is_cache_valid(self):
        """检查缓存是否有效"""
        if not self._cached_credentials or not self._cache_timestamp:
            return False
        # 确保使用相同的时区格式进行比较
        current_time = datetime.now()
        if self._cache_timestamp.tzinfo is None:
            # 如果缓存时间戳没有时区信息，使用本地时间
            return current_time - self._cache_timestamp < self._cache_duration
        else:
            # 如果缓存时间戳有时区信息，转换为本地时间进行比较
            local_timestamp = self._cache_timestamp.replace(tzinfo=None)
            return current_time - local_timestamp < self._cache_duration
    
    def _clear_cache(self):
        """清除缓存"""
        self._cached_credentials = None
        self._cache_timestamp = None
    
    def set_credentials(self, credentials_dict, user_id='default'):
        """设置凭证到数据库"""
        db = self._get_db_session()
        try:
            # 检查是否已存在凭证
            existing = db.query(AuthCredentials).filter(
                AuthCredentials.user_id == user_id,
                AuthCredentials.is_active == True
            ).first()
            
            # 计算过期时间
            expiry = None
            if credentials_dict.get('expiry'):
                try:
                    expiry = datetime.fromisoformat(credentials_dict['expiry'])
                    # 确保过期时间是时区感知的
                    if expiry.tzinfo is None:
                        # 如果没有时区信息，假设是UTC时间
                        from ..models import EAST_8_TZ
                        expiry = expiry.replace(tzinfo=timezone.utc)
                except:
                    pass
            
            if existing:
                # 更新现有凭证
                existing.token = credentials_dict['token']
                existing.refresh_token = credentials_dict.get('refresh_token')
                existing.token_uri = credentials_dict['token_uri']
                existing.client_id = credentials_dict['client_id']
                existing.client_secret = credentials_dict['client_secret']
                existing.scopes = json.dumps(credentials_dict['scopes'])
                existing.expires_at = expiry
                existing.updated_at = get_east8_time()
            else:
                # 创建新凭证
                new_credentials = AuthCredentials(
                    user_id=user_id,
                    token=credentials_dict['token'],
                    refresh_token=credentials_dict.get('refresh_token'),
                    token_uri=credentials_dict['token_uri'],
                    client_id=credentials_dict['client_id'],
                    client_secret=credentials_dict['client_secret'],
                    scopes=json.dumps(credentials_dict['scopes']),
                    expires_at=expiry
                )
                db.add(new_credentials)
            
            db.commit()
            self._clear_cache()  # 清除缓存
            print(f"认证凭证已保存到数据库，用户: {user_id}")
            
        except Exception as e:
            db.rollback()
            print(f"保存认证凭证到数据库失败: {e}")
            raise
        finally:
            db.close()
    
    def get_credentials(self, user_id='default'):
        """从数据库获取凭证"""
        # 检查缓存
        if self._is_cache_valid():
            return self._cached_credentials
        
        db = self._get_db_session()
        try:
            # 查询活跃的凭证
            auth_record = db.query(AuthCredentials).filter(
                AuthCredentials.user_id == user_id,
                AuthCredentials.is_active == True
            ).first()
            
            if not auth_record:
                self._clear_cache()
                return None
            
            # 检查是否需要刷新
            if auth_record.needs_refresh():
                print(f"凭证需要刷新，用户: {user_id}")
                refreshed_credentials = self._refresh_credentials(auth_record, db)
                if refreshed_credentials:
                    self._cached_credentials = refreshed_credentials
                    self._cache_timestamp = datetime.now()
                    return refreshed_credentials
                else:
                    # 刷新失败，标记为不活跃
                    auth_record.is_active = False
                    db.commit()
                    self._clear_cache()
                    return None
            
            # 检查是否已过期
            if auth_record.is_expired():
                print(f"凭证已过期，用户: {user_id}")
                auth_record.is_active = False
                db.commit()
                self._clear_cache()
                return None
            
            # 转换并缓存凭证
            credentials_dict = {
                'token': auth_record.token,
                'refresh_token': auth_record.refresh_token,
                'token_uri': auth_record.token_uri,
                'client_id': auth_record.client_id,
                'client_secret': auth_record.client_secret,
                'scopes': json.loads(auth_record.scopes),
                'expiry': auth_record.expires_at.isoformat() if auth_record.expires_at else None
            }
            
            credentials = dict_to_credentials(credentials_dict)
            self._cached_credentials = credentials
            self._cache_timestamp = datetime.now()
            
            return credentials
            
        except Exception as e:
            print(f"从数据库获取认证凭证失败: {e}")
            self._clear_cache()
            return None
        finally:
            db.close()
    
    def _refresh_credentials(self, auth_record, db):
        """刷新过期的凭证"""
        try:
            # 创建凭证对象
            credentials_dict = {
                'token': auth_record.token,
                'refresh_token': auth_record.refresh_token,
                'token_uri': auth_record.token_uri,
                'client_id': auth_record.client_id,
                'client_secret': auth_record.client_secret,
                'scopes': json.loads(auth_record.scopes),
                'expiry': auth_record.expires_at.isoformat() if auth_record.expires_at else None
            }
            
            credentials = dict_to_credentials(credentials_dict)
            
            # 尝试刷新
            if credentials and credentials.refresh_token:
                credentials.refresh(Request())
                
                # 更新数据库中的凭证
                auth_record.token = credentials.token
                if credentials.expiry:
                    auth_record.expires_at = credentials.expiry
                auth_record.updated_at = get_east8_time()
                
                db.commit()
                print(f"凭证刷新成功，用户: {auth_record.user_id}")
                return credentials
            else:
                print(f"无法刷新凭证，缺少refresh_token，用户: {auth_record.user_id}")
                return None
                
        except Exception as e:
            print(f"刷新凭证失败: {e}")
            return None
    
    def is_authenticated(self, user_id='default'):
        """检查用户是否已认证"""
        credentials = self.get_credentials(user_id)
        return credentials is not None
    
    def clear_credentials(self, user_id='default'):
        """清除用户的认证凭证"""
        db = self._get_db_session()
        try:
            # 标记所有凭证为不活跃
            db.query(AuthCredentials).filter(
                AuthCredentials.user_id == user_id
            ).update({
                'is_active': False,
                'updated_at': get_east8_time()
            })
            db.commit()
            self._clear_cache()
            print(f"用户 {user_id} 的认证凭证已清除")
            
        except Exception as e:
            db.rollback()
            print(f"清除认证凭证失败: {e}")
        finally:
            db.close()
    
    def get_active_users(self):
        """获取所有活跃认证用户"""
        db = self._get_db_session()
        try:
            active_users = db.query(AuthCredentials.user_id).filter(
                AuthCredentials.is_active == True
            ).distinct().all()
            return [user[0] for user in active_users]
        except Exception as e:
            print(f"获取活跃用户失败: {e}")
            return []
        finally:
            db.close()


# 全局凭证存储实例（基于数据库）
global_credential_store = DatabaseCredentialStore()
