import requests
from bs4 import BeautifulSoup
from .base_parser import BaseParser


class VocParser(BaseParser):
    """
    m.voc.com.cn 网站解析器
    """
    
    def __init__(self, headers=None):
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
        }
    
    def parse(self, url):
        """
        解析 m.voc.com.cn 网站的页面
        
        Args:
            url (str): 要解析的页面URL
            
        Returns:
            dict: 包含标题、日期、正文等内容的字典
        """
        req = requests.get(url, headers=self.headers)
        req.encoding = 'utf-8'
        soup = BeautifulSoup(req.text, 'html.parser')

        # 根据实际网站结构调整选择器
        title = soup.select('#main_title')[0].text if soup.select('#main_title') else "未知标题"
        date = soup.select('#main_info')[0].text if soup.select('#main_info') else ""
        
        # 根据实际网站结构调整内容选择器
        content_div = soup.select('#content')[0] if soup.select('#content') else soup
        
        # 提取文本内容
        body = content_div.get_text()

        return {
            'title': title,
            'date': date,
            'body': body,
            'content_div': content_div
        }
    
    @property
    def domains(self):
        """
        返回该解析器支持的域名列表
        
        Returns:
            list: 支持的域名列表
        """
        return ['m.voc.com.cn']
