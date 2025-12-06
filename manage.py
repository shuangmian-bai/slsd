#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from pathlib import Path


def create_parser(parser_name, domains):
    """
    创建一个新的解析器
    
    Args:
        parser_name (str): 解析器名称
        domains (list): 支持的域名列表
    """
    # 确保parsers目录存在
    parsers_dir = Path("parsers")
    if not parsers_dir.exists():
        print(f"错误: 找不到parsers目录")
        return False
    
    # 创建解析器文件
    parser_file = parsers_dir / f"{parser_name.lower()}_parser.py"
    if parser_file.exists():
        print(f"错误: 解析器文件 {parser_file} 已存在")
        return False
    
    # 解析器模板
    template = f'''import requests
from bs4 import BeautifulSoup
from .base_parser import BaseParser


class {parser_name.capitalize()}Parser(BaseParser):
    """
    {parser_name} 网站解析器
    """
    
    def __init__(self, headers=None):
        self.headers = headers or {{
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
        }}
    
    def parse(self, url):
        """
        解析 {parser_name} 网站的页面
        
        Args:
            url (str): 要解析的页面URL
            
        Returns:
            dict: 包含标题、日期、正文等内容的字典
        """
        req = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(req.text, 'html.parser')

        # TODO: 根据实际网站结构调整选择器
        title = soup.select('h1')[0].text if soup.select('h1') else "未知标题"
        date = soup.select('.date')[0].text if soup.select('.date') else ""
        
        # TODO: 根据实际网站结构调整内容选择器
        content_div = soup.select('.content')[0] if soup.select('.content') else soup
        
        # 提取文本内容
        body = content_div.get_text()

        return {{
            'title': title,
            'date': date,
            'body': body,
            'content_div': content_div
        }}
    
    @property
    def domains(self):
        """
        返回该解析器支持的域名列表
        
        Returns:
            list: 支持的域名列表
        """
        return {domains}


if __name__ == "__main__":
    parser = {parser_name.capitalize()}Parser()
    # TODO: 添加测试代码
'''

    # 写入文件
    try:
        with open(parser_file, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"成功创建解析器: {parser_file}")
        
        # 提示用户需要注册解析器
        print(f"请记得在 parser_factory.py 中注册新的解析器:")
        print(f"1. 在文件开头添加导入: from parsers.{parser_name.lower()}_parser import {parser_name.capitalize()}Parser")
        print(f"2. 在文件末尾添加注册代码:")
        print(f"   _parser = {parser_name.capitalize()}Parser()")
        print(f"   ParserFactory.register_parser(_parser)")
        return True
    except Exception as e:
        print(f"创建解析器失败: {e}")
        return False


def delete_parser(parser_name):
    """
    删除一个解析器
    
    Args:
        parser_name (str): 解析器名称
    """
    parsers_dir = Path("parsers")
    parser_file = parsers_dir / f"{parser_name.lower()}_parser.py"
    
    if not parser_file.exists():
        print(f"错误: 解析器文件 {parser_file} 不存在")
        return False
    
    try:
        # 删除解析器文件
        parser_file.unlink()
        print(f"成功删除解析器: {parser_file}")
        return True
    except Exception as e:
        print(f"删除解析器失败: {e}")
        return False


def list_parsers():
    """
    列出所有可用的解析器
    """
    parsers_dir = Path("parsers")
    if not parsers_dir.exists():
        print("错误: 找不到parsers目录")
        return
    
    print("可用的解析器:")
    for file in parsers_dir.glob("*_parser.py"):
        if file.name != "base_parser.py":
            parser_name = file.name.replace("_parser.py", "")
            print(f"  - {parser_name}")


def main():
    parser = argparse.ArgumentParser(description="网络爬虫管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建解析器命令
    create_parser_cmd = subparsers.add_parser('create_parser', help='创建新的解析器')
    create_parser_cmd.add_argument('name', help='解析器名称')
    create_parser_cmd.add_argument('--domains', nargs='+', required=True, 
                                  help='支持的域名列表 (例如: --domains example.com www.example.com)')
    
    # 删除解析器命令
    delete_parser_cmd = subparsers.add_parser('delete_parser', help='删除解析器')
    delete_parser_cmd.add_argument('name', help='要删除的解析器名称')
    
    # 列出解析器命令
    subparsers.add_parser('list_parsers', help='列出所有解析器')
    
    args = parser.parse_args()
    
    if args.command == 'create_parser':
        create_parser(args.name, args.domains)
    elif args.command == 'delete_parser':
        delete_parser(args.name)
    elif args.command == 'list_parsers':
        list_parsers()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()