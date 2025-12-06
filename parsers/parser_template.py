import requests
from bs4 import BeautifulSoup
# 导入基类 - 使用兼容PyInstaller的导入方式
import sys
import os

# 添加当前目录到sys.path，确保可以导入base_parser
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from parsers.base_parser import BaseParser
except ImportError:
    # 在PyInstaller打包环境中尝试不同的导入方式
    try:
        from base_parser import BaseParser
    except ImportError:
        # 最后尝试直接从父模块导入
        BaseParser = None
        print("警告: 无法导入BaseParser")


class TemplateParser(BaseParser if BaseParser else object):
    """
    解析器模板 - 创建新解析器时请复制并修改此类
    """
    
    def __init__(self, headers=None):
        # 设置默认请求头，模拟浏览器访问
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
        }
    
    def parse(self, url):
        """
        解析页面内容 - 需要根据目标网站结构调整选择器
        
        Args:
            url (str): 要解析的页面URL
            
        Returns:
            dict: 包含标题、日期、正文等内容的字典
        """
        # 发送GET请求获取页面内容
        req = requests.get(url, headers=self.headers)
        # 处理编码问题（某些网站可能需要特殊处理）
        # req.encoding = 'utf-8'  # 如有需要可取消注释
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(req.text, 'html.parser')

        # 根据网站结构调整以下选择器
        # 示例选择器，需要根据实际情况修改：
        title = soup.select('h1')[0].text if soup.select('h1') else "未知标题"
        date = soup.select('.date')[0].text if soup.select('.date') else ""
        
        # 选择包含正文内容的元素
        content_div = soup.select('.content')[0] if soup.select('.content') else soup
        
        # 提取文本内容
        body = content_div.get_text()

        # 返回标准化的数据结构
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
        # 修改为实际支持的域名
        return ['example.com']


# 使用说明：
# 1. 复制此文件并重命名为 [网站名]_parser.py
# 2. 修改类名为 [网站名]Parser （遵循驼峰命名规范）
# 3. 修改domains属性为实际支持的域名列表
# 4. 根据目标网站结构调整parse方法中的选择器
# 5. 测试解析器确保能正确提取内容