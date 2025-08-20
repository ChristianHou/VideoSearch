# -*- coding: utf-8 -*-

import time
import googleapiclient.discovery
import googleapiclient.errors
import os # Added for os.environ

from ..config import AppConfig
from ..utils.datetime_utils import normalize_rfc3339_date, parse_rfc3339_datetime


class YouTubeSearchAPI:
    def __init__(self):
        self.youtube = None

    def authenticate(self, credentials) -> bool:
        try:
            # 检查系统代理设置并配置环境变量
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                    r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
                proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if proxy_enable:
                    proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    winreg.CloseKey(key)
                    
                    # 设置环境变量来配置代理
                    if ':' in proxy_server:
                        host, port = proxy_server.split(':', 1)
                        proxy_url = f"http://{host}:{port}"
                        os.environ['HTTP_PROXY'] = proxy_url
                        os.environ['HTTPS_PROXY'] = proxy_url
                        print(f"检测到系统代理: {proxy_server}，已配置环境变量")
                    else:
                        print(f"代理地址格式不正确: {proxy_server}")
                else:
                    winreg.CloseKey(key)
                    print("未检测到系统代理")
            except Exception as e:
                print(f"无法检测系统代理设置: {e}")
            
            # 使用标准的认证方法，让googleapiclient自动处理代理
            self.youtube = googleapiclient.discovery.build(
                AppConfig.YT_API_SERVICE_NAME,
                AppConfig.YT_API_VERSION,
                credentials=credentials,
                cache_discovery=False
            )
            
            # 测试连接
            try:
                # 尝试一个简单的API调用来验证连接
                test_request = self.youtube.search().list(part='snippet', q='test', maxResults=1)
                test_request.execute()
                print("YouTube API认证成功，连接测试通过")
                return True
            except Exception as test_error:
                print(f"连接测试失败: {test_error}")
                return False
                
        except Exception as e:
            print(f"认证失败: {e}")
            return False

    def search_videos(self, query, max_results=25, published_after=None,
                      published_before=None, region_code=None, relevance_language=None,
                      video_duration=None, video_definition=None, video_embeddable=None,
                      video_license=None, video_syndicated=None, video_type=None, order_by='relevance'):
        if not self.youtube:
            return {"error": "API未认证"}

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                search_params = {
                    'part': 'snippet',
                    'q': query,
                    'maxResults': max_results,
                    'type': 'video',
                    'order': order_by  # 新增：排序参数
                }

                if published_after:
                    search_params['publishedAfter'] = normalize_rfc3339_date(published_after, end_of_day=False)
                if published_before:
                    search_params['publishedBefore'] = normalize_rfc3339_date(published_before, end_of_day=True)

                pa = search_params.get('publishedAfter')
                pb = search_params.get('publishedBefore')
                if pa and pb:
                    d_pa = parse_rfc3339_datetime(pa)
                    d_pb = parse_rfc3339_datetime(pb)
                    if d_pa and d_pb and d_pa > d_pb:
                        return {"error": "published_after 不应晚于 published_before，请调整日期范围"}

                if region_code:
                    search_params['regionCode'] = region_code
                if relevance_language:
                    search_params['relevanceLanguage'] = relevance_language
                if video_duration:
                    search_params['videoDuration'] = video_duration
                if video_definition:
                    search_params['videoDefinition'] = video_definition
                if video_embeddable:
                    search_params['videoEmbeddable'] = video_embeddable
                if video_license:
                    search_params['videoLicense'] = video_license
                if video_syndicated:
                    search_params['videoSyndicated'] = video_syndicated
                if video_type:
                    search_params['videoType'] = video_type

                # 记录实际发送给API的参数
                print(f"YouTube API搜索参数:")
                for key, value in search_params.items():
                    print(f"  {key}: {value}")

                request = self.youtube.search().list(**search_params)
                response = request.execute()

                return {
                    "success": True,
                    "data": response,
                    "total_results": response.get('pageInfo', {}).get('totalResults', 0)
                }

            except googleapiclient.errors.HttpError as e:
                error_msg = f"API请求失败: {e}"
                if attempt < max_retries - 1:
                    print(f"遇到错误 :{error_msg} 尝试 {attempt + 1}/{max_retries} 失败，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return {"error": error_msg}

            except Exception as e:
                error_msg = f"搜索失败: {e}"
                error_str = str(e)
                
                # 详细的网络错误诊断
                if "WinError 10061" in error_str:
                    error_msg = "连接被拒绝 (WinError 10061)。可能原因：1) 代理配置问题 2) 防火墙阻止 3) 网络配置问题。请检查系统代理设置或联系网络管理员。"
                elif "WinError 10060" in error_str or "timeout" in error_str.lower():
                    if attempt < max_retries - 1:
                        print(f"网络超时，尝试 {attempt + 1}/{max_retries}，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    error_msg = "网络连接超时，请检查网络设置或稍后重试"
                elif "WinError 10065" in error_str:
                    error_msg = "目标主机无法访问 (WinError 10065)。请检查网络连接和DNS设置。"
                elif "WinError 10054" in error_str:
                    error_msg = "连接被远程主机关闭 (WinError 10054)。请稍后重试。"
                elif "WinError 10013" in error_str:
                    error_msg = "权限被拒绝 (WinError 10013)。请检查防火墙设置。"
                
                print(f"网络错误详情: {error_str}")
                return {"error": error_msg}

        return {"error": "搜索失败，已达到最大重试次数"}


# 单例服务
youtube_service = YouTubeSearchAPI()
