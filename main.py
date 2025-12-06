#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from get_data import get_links, process_article
from concurrent.futures import ThreadPoolExecutor, as_completed


def safe_input(prompt, default_value=None):
    """
    安全的input函数，在打包为exe时可能丢失stdin的情况下提供默认值
    """
    try:
        result = input(prompt).strip()
        if not result and default_value is not None:
            return default_value
        return result
    except RuntimeError:
        # 当打包为exe且使用--windowed参数时，stdin可能不可用
        print(f"{prompt} (由于环境限制，使用默认值)")
        return default_value if default_value is not None else ""


def main():
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
    search_key = safe_input("请输入搜索关键词（直接回车默认为'信息安全'）: ", "信息安全")

    # 获取用户输入的线程数
    while True:
        try:
            thread_input = safe_input("请输入线程数量（直接回车默认为5）: ", "5")
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
    
    try:
        input("回车后继续")
    except RuntimeError:
        pass  # 忽略无法等待输入的情况


if __name__ == "__main__":
    main()