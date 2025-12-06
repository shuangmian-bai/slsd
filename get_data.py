from pprint import pprint

import requests
import urllib.parse
import re
from html import unescape
import time
import os
from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Inches
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from requests_toolbelt.multipart.encoder import MultipartEncoder

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,ru;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': 'https://www.hnslsdxy.com/page/default.aspx',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
    'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

# 创建锁对象，用于线程安全地访问文件系统
lock = threading.Lock()

# 确保数据目录存在
data_dir = "data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 确保图片缓存目录存在
img_dir = "img"
if not os.path.exists(img_dir):
    os.makedirs(img_dir)

# 解析一页新闻
def parse_page(url):
    req = requests.get(url, headers=headers)
    soup  = BeautifulSoup(req.text, 'html.parser')

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
        article_data = parse_page(url)
        
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
                # 收集外部链接而不是立即打印
                external_links.append(link)
                continue
            link = 'https://www.hnslsdxy.com/page/' +  link
            links.append(link)
    
    return links, external_links

if __name__ == "__main__":
    # 输出欢迎信息和ASCII艺术字
    print("欢迎使用双面的湖南水利水电官网信息检索工具")
    print(r"""
  _   _                            ____          _  __     ____  _             _             
 | \ | |_   _ _ __ ___   ___ _ __ / ___|   _ ___(_)/ _|   |  _ \| |_   _  __ _(_)_ __   __ _ 
 |  \| | | | | '_ ` _ \ / _ \ '__| |  | | | / __| | |_    | |_) | | | | |/ _` | | '_ \ / _` |
 | |\  | |_| | | | | | |  __/ |  | |__| |_| \__ \ |  _|   |  __/| | |_| | (_| | | | | | (_| |
 |_| \_|\__,_|_| |_| |_|\___|_|   \____\__,_|___/_|_|     |_|   |_|\__,_|\__, |_|_| |_|\__, |
                                                                         |___/         |___/ 
    """)
    
    # 获取用户输入的搜索关键词
    search_key = input("请输入搜索关键词（直接回车默认为'信息安全'）: ").strip()
    if not search_key:
        search_key = "信息安全"
    
    # 获取用户输入的线程数
    while True:
        try:
            thread_input = input("请输入线程数量（直接回车默认为5）: ").strip()
            if not thread_input:
                max_threads = 5
            else:
                max_threads = int(thread_input)
                if max_threads <= 0:
                    print("线程数量必须大于0，请重新输入")
                    continue
            break
        except ValueError:
            print("请输入有效的数字")
    
    print(f"正在搜索关键词: {search_key}")
    print(f"使用线程数: {max_threads}")
    data, external_links = get_links(search_key)
    print(f"总共找到 {len(data)} 个内部链接")
    
    # 统计变量
    success_count = 0
    skip_count = 0
    failed_articles = []  # 记录处理失败的文章
    
    # 使用线程池处理文章
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # 提交所有任务
        future_to_url = {executor.submit(process_article, url): url for url in data}
        
        # 处理完成的任务
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result, error_msg, message, title = future.result()
                print(message)
                if result:
                    success_count += 1
                else:
                    skip_count += 1
                    # 如果处理失败，记录失败信息
                    if error_msg:  # 只有真正出错的情况才记录
                        failed_articles.append({'title': title, 'url': url, 'error': error_msg})
            except Exception as e:
                print(f"处理 {url} 时发生异常: {e}")
                failed_articles.append({'title': "未知标题", 'url': url, 'error': str(e)})
    
    # 输出汇总信息
    print(f"\n处理完成! 成功保存: {success_count} 篇, 跳过已存在: {skip_count} 篇")
    
    # 在程序结束时输出所有处理失败的文章
    if failed_articles:
        print(f"\n发现 {len(failed_articles)} 个处理失败的文章:")
        for i, article in enumerate(failed_articles, 1):
            print(f"{i}. 标题: {article['title']}")
            print(f"   链接: {article['url']}")
            print(f"   错误: {article['error']}\n")
    else:
        print("\n所有文章处理成功，无失败项")
    
    # 在程序结束时输出所有外部链接
    if external_links:
        print(f"发现 {len(external_links)} 个外部链接需要手动访问:")
        for i, link in enumerate(external_links, 1):
            print(f"{i}. {link}")

    else:
        print("\n没有发现外部链接")
    input("回车后继续")