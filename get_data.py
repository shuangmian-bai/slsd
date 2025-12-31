import requests
import urllib.parse
import re
import os
from bs4 import BeautifulSoup
from docx import Document
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import urlparse

# 导入解析器工厂
from parser_factory import ParserFactory

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
}

# 创建锁对象，用于线程安全地访问文件系统
lock = threading.Lock()

# 确保数据目录存在
import sys
if getattr(sys, 'frozen', False):
    # 打包后的可执行文件
    base_dir = os.path.dirname(sys.executable)
else:
    # 开发环境
    base_dir = os.path.dirname(os.path.abspath(__file__))

data_dir = os.path.join(base_dir, "data", "word")
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 确保图片缓存目录存在
img_dir = os.path.join(base_dir, "data", "img")
if not os.path.exists(img_dir):
    os.makedirs(img_dir)

# 将文章保存为Word文档
def save_to_word(article_data, filename):
    # 完整文件路径
    full_path = os.path.join(data_dir, filename)
    
    # 检查文件是否已存在
    if os.path.exists(full_path):
        return False, full_path
    
    # 创建Word文档
    doc = Document()
    
    # 添加标题
    doc.add_heading(article_data['title'], 0)
    
    # 添加日期和来源信息
    doc.add_paragraph(article_data['date'])
    
    # 添加正文内容
    # 解析内容中的文本和图片
    content_div = article_data['content_div']
    
    # 遍历内容中的所有元素
    paragraph = None
    for element in content_div.descendants:
        if element.name == 'p':
            # 处理段落
            paragraph = doc.add_paragraph(element.get_text().strip())
        elif element.name == 'div':
            # 处理div中的内容
            div_text = element.get_text().strip()
            if div_text:
                paragraph = doc.add_paragraph(div_text)
        elif element.name == 'img':
            # 处理图片
            img_src = element.get('src')
            if img_src:
                try:
                    # 处理相对路径和绝对路径
                    if img_src.startswith('/'):
                        img_url = 'https://www.hnslsdxy.com' + img_src
                    elif not img_src.startswith('http'):
                        # 相对路径处理
                        base_url = 'https://www.hnslsdxy.com/page/'
                        img_url = base_url + img_src
                    else:
                        img_url = img_src
                        
                    # 下载图片
                    img_response = requests.get(img_url, headers=headers, timeout=30)
                    if img_response.status_code == 200:
                        # 保存图片到img文件夹
                        img_filename = os.path.basename(img_url.split('?')[0])
                        if not img_filename:
                            img_filename = 'image.jpg'
                            
                        img_path = os.path.join(img_dir, img_filename)
                        counter = 1
                        original_img_path = img_path
                        while os.path.exists(img_path):
                            name, ext = os.path.splitext(original_img_path)
                            img_path = f"{name}_{counter}{ext}"
                            counter += 1
                            
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # 添加图片到文档，保持原始尺寸
                        doc.add_picture(img_path)
                    else:
                        # 图片下载失败时添加提示文字
                        doc.add_paragraph(f"[图片加载失败: {img_url}]")
                except Exception as e:
                    # 出现异常时添加提示文字
                    doc.add_paragraph(f"[图片处理失败: {str(e)}]")
        elif element.name is None and element.strip() and paragraph:
            # 处理纯文本节点（可能是段落内的文本）
            if not paragraph.text:  # 如果段落为空，则添加文本
                paragraph.text = element.strip()
                
    # 保存文档
    doc.save(full_path)
    return True, full_path

# 处理单个链接的文章获取和保存
def process_article(url):
    try:
        # 根据URL获取对应的解析器
        parser = ParserFactory.get_parser(url)
        
        # 如果没有对应的解析器，标记为外部链接
        if not parser:
            domain = urlparse(url).netloc
            return False, None, f"外部链接: {url} (域名 {domain} 未注册解析器)", "外部链接"
        
        # 使用对应的解析器解析页面
        article_data = parser.parse(url)
        
        # 根据标题生成文件名，清理非法字符
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', article_data['title'])
        filename = f"{filename}.docx"
        
        # 保存为Word文档
        with lock:
            saved, full_path = save_to_word(article_data, filename)
            
        if saved:
            return True, None, f"文章 '{article_data['title']}' 已保存为 {full_path}", article_data['title']
        else:
            return False, None, f"文件 {full_path} 已存在，跳过保存", article_data['title']
    except Exception as e:
        return False, str(e), f"处理 {url} 时出错: {e}", "未知标题"

def get_links(search_key):
    # 对搜索关键词进行URL编码
    encoded_key = urllib.parse.quote(search_key)
    
    params = {
        'statictype': '0',
        'key': encoded_key,
        'topic': '',
        'type': 'T',
        'btime': '',
        'etime': '',
        'page': '1',
        'webid': '2014052022542170611',
    }

    response = requests.get('https://www.hnslsdxy.com/api/web_search.ashx', params=params, headers=headers)
    data = response.json()
    # 获取总页数
    page = data['pagecount']
    links = []
    external_links = []  # 收集外部链接

    for i in range(page):
        i += 1
        params['page'] = str(i)
        response = requests.get('https://www.hnslsdxy.com/api/web_search.ashx', params=params, headers=headers)
        data = response.json()
        for item in data['content']:
            link  = item['title'].split('href=')[2]
            link  = link.split("'")[1]
            if link[0:4] == 'http':
                # 检查该链接是否属于我们已注册解析器支持的域名
                if ParserFactory.is_registered_domain(link):
                    # 如果是已注册的域名，则将其作为内部链接处理
                    links.append(link)
                else:
                    # 否则将其作为真正的外部链接收集
                    external_links.append(link)
                continue
            link = 'https://www.hnslsdxy.com/page/' +  link
            links.append(link)
    
    return links, external_links