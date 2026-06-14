import requests
from bs4 import BeautifulSoup
import sys
import os
import re
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from parsers.base_parser import BaseParser
except ImportError:
    try:
        from base_parser import BaseParser
    except ImportError:
        BaseParser = None
        print("警告: 无法导入BaseParser")


class XuexiParser(BaseParser if BaseParser else object):
    """
    学习强国网站解析器
    通过 boot-source.xuexi.cn/data/app/{id}.js 获取文章数据
    """

    # 文章详情页 URL 模式
    DETAIL_URL_PATTERN = 'https://www.xuexi.cn/lgpage/detail/index.html?id={article_id}'
    # JS 数据文件 URL 模式
    JS_DATA_PATTERN = 'https://boot-source.xuexi.cn/data/app/{article_id}.js'

    def __init__(self, headers=None):
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'Referer': 'https://www.xuexi.cn/',
        }

    def _extract_article_id(self, url):
        """从 URL 中提取文章 ID"""
        match = re.search(r'id=(\d+)', url)
        return match.group(1) if match else None

    def _parse_jsonp(self, text):
        """解析 JSONP callback({...}) 格式，提取 JSON 对象"""
        # 去掉 callback( 前缀和 ); 后缀
        match = re.search(r'callback\((.*)\);?\s*$', text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # 尝试直接解析（可能没有 callback 包装）
            json_str = text
        return json.loads(json_str)

    def _fetch_js_data(self, article_id):
        """获取并解析 JS 数据文件"""
        js_url = self.JS_DATA_PATTERN.format(article_id=article_id)
        resp = requests.get(js_url, headers=self.headers, timeout=30)
        resp.encoding = 'utf-8'
        return self._parse_jsonp(resp.text)

    def _extract_videos(self, data):
        """提取视频信息列表"""
        videos = []
        for video in data.get('videos', []):
            video_info = {
                'url': None,
                'thumbnail': None,
                'duration': video.get('video_meta_settings', {}).get('play_length', 0),
            }
            # 获取 MP4 直链
            for storage in video.get('video_storage_info', []):
                if storage.get('format', '').startswith('mov,mp4') or storage.get('normal', '').endswith('.mp4'):
                    video_info['url'] = storage.get('normal')
                    break
            # 如果没有 MP4，取第一个可用链接
            if not video_info['url'] and video.get('video_storage_info'):
                video_info['url'] = video['video_storage_info'][0].get('normal')

            # 获取封面图
            thumbnails = video.get('thumbnails', [])
            if thumbnails and thumbnails[0].get('data'):
                video_info['thumbnail'] = thumbnails[0]['data'][0].get('url')

            if video_info['url']:
                videos.append(video_info)
        return videos

    def _extract_images(self, data):
        """提取文章配图列表"""
        images = []
        for img in data.get('image', []):
            url = img.get('url')
            if url:
                images.append({
                    'url': url,
                    'desc': img.get('desc', ''),
                })
        return images

    def parse(self, url):
        """
        解析学习强国文章页面

        Args:
            url (str): 文章详情页 URL

        Returns:
            dict: 包含 title, date, body, content_div, videos, images 的字典
        """
        article_id = self._extract_article_id(url)
        if not article_id:
            raise ValueError(f"无法从 URL 中提取文章 ID: {url}")

        data = self._fetch_js_data(article_id)

        # 标题
        title = data.get('title', '未知标题')

        # 发布时间
        date = data.get('publish_time', '')

        # 正文 HTML
        content_html = data.get('content', '')
        content_div = BeautifulSoup(content_html, 'html.parser')

        # 纯文本
        body = data.get('normalized_content', content_div.get_text())

        # 视频
        videos = self._extract_videos(data)

        # 图片
        images = self._extract_images(data)

        return {
            'title': title,
            'date': date,
            'body': body,
            'content_div': content_div,
            'videos': videos,
            'images': images,
        }

    @property
    def domains(self):
        return ['www.xuexi.cn', 'xuexi.cn']
