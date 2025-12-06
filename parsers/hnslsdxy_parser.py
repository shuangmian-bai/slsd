import requests
from bs4 import BeautifulSoup
from .base_parser import BaseParser


class HnslsdxyParser(BaseParser):
    """
    湖南水利水电职业技术学院网站解析器
    """
    
    def __init__(self, headers=None):
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
        }
    
    def parse(self, url):
        """
        解析湖南水利水电职业技术学院网站的页面
        
        Args:
            url (str): 要解析的页面URL
            
        Returns:
            dict: 包含标题、日期、正文等内容的字典
        """
        req = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(req.text, 'html.parser')

        # 获取标题 #Labtitle
        title = soup.select('#Labtitle')[0].text
        date = soup.select('#Labinfo')[0].text
        # 真文 #content_div
        content_div = soup.select('.content_div')[0]
        
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
        return ['www.hnslsdxy.com', 'hnslsdxy.com']