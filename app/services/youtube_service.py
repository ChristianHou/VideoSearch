# -*- coding: utf-8 -*-

import time
import googleapiclient.discovery
import googleapiclient.errors

from ..config import AppConfig
from ..utils.datetime_utils import normalize_rfc3339_date, parse_rfc3339_datetime


class YouTubeSearchAPI:
    def __init__(self):
        self.youtube = None

    def authenticate(self, credentials) -> bool:
        try:
            self.youtube = googleapiclient.discovery.build(
                AppConfig.YT_API_SERVICE_NAME,
                AppConfig.YT_API_VERSION,
                credentials=credentials,
                cache_discovery=False,
            )
            return True
        except Exception as e:
            print(f"认证失败: {e}")
            return False

    def search_videos(self, query, max_results=25, published_after=None,
                      published_before=None, region_code=None, relevance_language=None,
                      video_duration=None, video_definition=None, video_embeddable=None,
                      video_license=None, video_syndicated=None, video_type=None):
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
                    'type': 'video'
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
                if "WinError 10060" in str(e) or "timeout" in str(e).lower():
                    if attempt < max_retries - 1:
                        print(f"网络超时，尝试 {attempt + 1}/{max_retries}，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    error_msg = "网络连接超时，请检查网络设置或稍后重试"
                return {"error": error_msg}

        return {"error": "搜索失败，已达到最大重试次数"}


# 单例服务
youtube_service = YouTubeSearchAPI()
