# 湖南水利水电职业技术学院官网信息检索工具项目文档

## 1. 项目概述

本项目是一个专门针对湖南水利水电职业技术学院官网的信息检索和采集工具。它能够根据关键词搜索学院官网的相关文章，并将其保存为 Word 文档格式，方便离线阅读和研究。

## 2. 项目架构

```
项目根目录/
├── main.py                  # 主程序入口
├── get_data.py              # 数据获取和处理核心逻辑
├── parser_factory.py        # 解析器工厂模式实现
├── manage.py                # 解析器管理工具
├── data/                    # 保存抓取的文章（Word文档格式）
├── img/                     # 保存文章中的图片
└── parsers/                 # 各网站解析器目录
    ├── __init__.py
    ├── base_parser.py       # 解析器基类
    └── hnslsdxy_parser.py   # 湖南水利水电职业技术学院网站解析器
```

## 3. 核心模块说明

### 3.1 main.py - 主程序入口

这是程序的主要入口点，负责：

1. 接收用户输入：
   - 搜索关键词（默认为"信息安全"）
   - 并发线程数（默认为5）

2. 调用 [get_links](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/get_data.py#L166-L180) 函数获取搜索结果链接

3. 使用线程池并发处理文章抓取和保存

4. 显示处理统计信息，包括：
   - 成功保存的文章数
   - 跳过的已存在文章数
   - 处理失败的文章及其错误信息
   - 发现的外部链接

### 3.2 get_data.py - 数据获取和处理核心

这个模块包含了抓取和处理文章的核心功能：

#### 主要函数：

1. [get_links(search_key)](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/get_data.py#L166-L180) - 根据关键词搜索文章链接
   - 向学院官网的搜索API发送请求
   - 解析返回的JSON数据获取文章链接
   - 区分内部链接和外部链接

2. [process_article(url)](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/get_data.py#L117-L163) - 处理单篇文章
   - 根据URL获取对应的解析器
   - 使用解析器解析页面内容
   - 调用 [save_to_word](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/get_data.py#L36-L114) 保存为Word文档

3. [save_to_word(article_data, filename)](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/get_data.py#L36-L114) - 保存文章为Word文档
   - 创建Word文档并添加标题、日期等元信息
   - 解析文章内容中的文本和图片
   - 下载并插入图片到文档中
   - 保存文档到 [data](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/data) 目录

### 3.3 parser_factory.py - 解析器工厂

采用工厂模式管理不同网站的解析器：

1. 自动扫描 [parsers](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/parsers) 目录下的解析器文件
2. 动态加载解析器模块
3. 根据URL域名提供对应的解析器实例
4. 支持扩展新的网站解析器

### 3.4 parsers/ - 网站解析器目录

#### base_parser.py - 解析器基类

定义了解析器的抽象接口：
- [parse(url)](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/parsers/hnslsdxy_parser.py#L19-L44) 方法：解析指定URL的页面内容
- [domains](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/parsers/hnslsdxy_parser.py#L47-L51) 属性：返回该解析器支持的域名列表

#### hnslsdxy_parser.py - 湖南水利水电职业技术学院网站解析器

实现了针对学院官网的页面解析逻辑：
- 解析文章标题（选择器: `#Labtitle`）
- 解析文章信息（选择器: `#Labinfo`）
- 解析文章正文内容（选择器: `.content_div`）

### 3.5 manage.py - 解析器管理工具

提供了命令行工具用于管理解析器：
1. 创建新的解析器模板
2. 删除现有解析器
3. 列出所有可用解析器

使用方法：
```bash
# 创建新解析器
python manage.py create_parser example --domains example.com www.example.com

# 删除解析器
python manage.py delete_parser example

# 列出所有解析器
python manage.py list_parsers
```

## 4. 工作流程

1. 用户运行 [main.py](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/main.py) 并输入搜索关键词和线程数
2. 程序调用 [get_links](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/get_data.py#L166-L180) 获取搜索结果中的文章链接
3. 为每个链接创建处理任务并放入线程池执行
4. 每个线程：
   - 通过 [ParserFactory](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/parser_factory.py#L6-L119) 获取对应网站的解析器
   - 使用解析器提取文章内容
   - 调用 [save_to_word](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/get_data.py#L36-L114) 保存为Word文档
5. 程序收集处理结果并显示统计信息

## 5. 特色功能

### 5.1 多线程并发处理
支持自定义线程数，默认5个线程并发抓取，提高处理效率。

### 5.2 图片处理
- 自动识别并下载文章中的图片
- 将图片保存到 [img](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/img) 目录
- 在Word文档中插入图片，保持原始尺寸
- 处理图片加载失败的情况

### 5.3 重名文件处理
当保存文件时如果发现同名文件已存在，则跳过保存，避免重复抓取。

### 5.4 工厂模式解析器
- 支持为不同网站编写专门的解析器
- 自动加载和注册解析器
- 易于扩展新网站的支持

### 5.5 异常处理
完善的异常处理机制，确保单个文章处理失败不影响整体流程，并会记录详细的错误信息。

## 6. 技术栈

- Python 3.x
- requests - HTTP库
- beautifulsoup4 - HTML解析库
- python-docx - Word文档操作库
- 标准库：urllib, re, os, concurrent.futures等

## 7. 使用方法

1. 安装依赖：
   ```
   pip install requests beautifulsoup4 python-docx
   ```

2. 运行程序：
   ```
   python main.py
   ```

3. 根据提示输入搜索关键词和线程数

4. 查看生成的Word文档位于 [data](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/data) 目录

## 8. 扩展性说明

项目具有良好的扩展性：

1. 添加新网站支持：
   - 使用 `python manage.py create_parser 网站名 --domains 域名列表` 创建解析器模板
   - 修改解析器实现具体的页面解析逻辑
   - 程序会自动加载新的解析器

2. 调整并发数：
   - 可根据网络情况和目标服务器负载调整并发线程数

3. 自定义文档格式：
   - 可修改 [save_to_word](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/get_data.py#L36-L114) 函数来自定义Word文档的样式和格式