#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dzk.hnslsdxy.com 全站文章扫描器
扫描全部栏目列表页，收集文章链接，多线程抓取并保存，本地记录已处理文章。
"""

import requests
import re
import os
import sys
import json
import threading
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

from get_data import process_article, data_dir

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
}

# 基础 URL
BASE_URL = 'https://dzk.hnslsdxy.com/page/'

# record.json 路径
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

RECORD_PATH = os.path.join(base_dir, 'data', 'record.json')

# 记录锁
record_lock = threading.Lock()


def load_record():
    """加载本地记录，返回已处理文章 ID 的集合"""
    if not os.path.exists(RECORD_PATH):
        return {}
    try:
        with open(RECORD_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_record(record):
    """保存记录到磁盘"""
    os.makedirs(os.path.dirname(RECORD_PATH), exist_ok=True)
    with open(RECORD_PATH, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def extract_article_id(url):
    """从 contentshow.aspx?id=xxx 中提取文章 ID"""
    match = re.search(r'id=(\d+)', url)
    return match.group(1) if match else None


def discover_list_pages(main_url):
    """
    爬取主页，提取所有 contentlist.aspx?id=xxx 列表页链接
    返回完整的列表页 URL 列表
    """
    print(f"正在扫描主页: {main_url}")
    try:
        resp = requests.get(main_url, headers=headers, timeout=30)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"主页请求失败: {e}")
        return []

    list_urls = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'contentlist.aspx' in href:
            full_url = urljoin(main_url, href)
            list_urls.add(full_url)

    print(f"发现 {len(list_urls)} 个列表页")
    return list(list_urls)


def discover_articles(list_url):
    """
    爬取单个列表页的所有分页，提取所有 contentshow.aspx?id=xxx 文章链接
    分页模式：contentlist.aspx?id=xxx&page=N
    返回文章 URL 列表
    """
    article_urls = set()

    # 先请求第 1 页，解析总页数
    try:
        resp = requests.get(list_url, headers=headers, timeout=30)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"  列表页请求失败: {list_url} - {e}")
        return []

    # 解析当前页文章
    def extract_articles(soup):
        urls = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'contentshow.aspx' in href:
                urls.add(urljoin(BASE_URL, href))
        return urls

    article_urls.update(extract_articles(soup))

    # 解析总页数：匹配 "当前为N/M页"
    total_pages = 1
    # 方法1：直接在页面文本中搜索
    page_text = soup.get_text()
    match = re.search(r'当前为(\d+)/(\d+)页', page_text)
    if match:
        total_pages = int(match.group(2))
    else:
        # 方法2：遍历所有文本节点
        from bs4 import NavigableString
        for node in soup.find_all(string=True):
            m = re.search(r'当前为(\d+)/(\d+)页', str(node))
            if m:
                total_pages = int(m.group(2))
                break

    if total_pages > 1:
        print(f"    分页检测: 共 {total_pages} 页")

    # 遍历剩余页面
    for page in range(2, total_pages + 1):
        sep = '&' if '?' in list_url else '?'
        page_url = f"{list_url}{sep}page={page}"
        try:
            resp = requests.get(page_url, headers=headers, timeout=30)
            resp.encoding = 'utf-8'
            page_soup = BeautifulSoup(resp.text, 'html.parser')
            article_urls.update(extract_articles(page_soup))
        except Exception as e:
            print(f"  第{page}页请求失败: {page_url} - {e}")
            continue

    return list(article_urls)


def discover_all_articles(main_url, threads=20):
    """
    多线程汇总所有列表页（含分页）的文章链接，去重后返回
    """
    list_pages = discover_list_pages(main_url)

    all_articles = set()
    lock = threading.Lock()
    counter = [0]

    def scan_one_list(list_url):
        articles = discover_articles(list_url)
        with lock:
            counter[0] += 1
            idx = counter[0]
        print(f"  扫描列表页 [{idx}/{len(list_pages)}]: {list_url} -> {len(articles)} 篇")
        return articles

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(scan_one_list, url): url for url in list_pages}
        for future in as_completed(futures):
            try:
                articles = future.result()
                all_articles.update(articles)
            except Exception as e:
                print(f"  列表页扫描异常: {futures[future]} - {e}")

    print(f"共发现 {len(all_articles)} 篇不重复文章")
    return list(all_articles)


def _existing_docx_files():
    """扫描 data/word/ 目录，返回已存在的 .docx 文件名集合"""
    if not os.path.exists(data_dir):
        return set()
    return {f for f in os.listdir(data_dir) if f.endswith('.docx')}


def scan_all(threads=20, main_url=None):
    """
    全站扫描主流程
    1. 加载本地记录 + 已有文件
    2. 多线程发现全部文章链接
    3. 过滤已处理文章（record.json + 文件存在）
    4. 多线程抓取并保存
    5. 更新记录
    """
    if main_url is None:
        main_url = BASE_URL + 'default.aspx'

    # 1. 加载记录
    record = load_record()
    processed_ids = set(record.keys())
    existing_files = _existing_docx_files()
    print(f"本地已有 {len(processed_ids)} 篇记录, {len(existing_files)} 个已下载文件")

    # 2. 多线程发现文章
    all_urls = discover_all_articles(main_url, threads=threads)
    if not all_urls:
        print("未发现任何文章")
        return

    # 3. 过滤已处理（record.json 中的 ID + 已存在的 docx 文件）
    new_urls = []
    for url in all_urls:
        article_id = extract_article_id(url)
        if not article_id:
            continue
        # 跳过已在记录中的
        if article_id in processed_ids:
            continue
        new_urls.append(url)

    print(f"新增 {len(new_urls)} 篇待处理文章（跳过 {len(all_urls) - len(new_urls)} 篇已处理）")
    if not new_urls:
        print("没有新文章需要处理")
        return

    # 4. 多线程处理
    success_count = 0
    skip_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_map = {executor.submit(process_article, url): url for url in new_urls}

        for future in as_completed(future_map):
            url = future_map[future]
            article_id = extract_article_id(url)
            try:
                result, error_msg, message, title = future.result()
                if result:
                    success_count += 1
                    print(f"  [成功] {title}")
                elif error_msg is None and "已存在" in message:
                    skip_count += 1
                    print(f"  [跳过] {title}")
                else:
                    fail_count += 1
                    print(f"  [失败] {message}")
            except Exception as e:
                fail_count += 1
                print(f"  [异常] {url} - {e}")
                title = "未知标题"

            # 更新记录
            if article_id:
                with record_lock:
                    record[article_id] = {
                        'url': url,
                        'title': title,
                        'processed_at': datetime.now().isoformat(),
                    }

    # 5. 保存记录
    save_record(record)

    print(f"\n扫描完成: 成功 {success_count}, 跳过 {skip_count}, 失败 {fail_count}")
    print(f"记录已保存至 {RECORD_PATH}")
