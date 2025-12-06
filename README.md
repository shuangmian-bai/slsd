# 湖南水利水电信息检索工具

这是一个用于检索湖南水利水电职业技术学院官网信息的工具。

## 功能特点

- 支持多线程并发抓取
- 自动保存文章为Word文档
- 支持多种网站解析器
- 可自定义搜索关键词和线程数

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 开发环境运行

有两种方式可以运行程序：

1. 命令行版本:
```bash
python cli_main.py
```

2. 图形界面版本:
```bash
python ui_main.py
```

按提示输入搜索关键词和线程数即可开始检索。

### 打包为exe

项目现在提供了两个独立的打包脚本，用于将CLI和GUI版本分别打包为exe文件：

1. 打包图形界面版本（无CMD窗口，多文件版本）:
```bash
python build_gui.py
```

2. 打包命令行版本（有CMD窗口，多文件版本）:
```bash
python build_cli.py
```

打包完成后，可在dist目录找到对应的可执行文件夹。图形界面版本将生成一个包含所有依赖文件的文件夹，运行其中的exe文件即可启动程序。

## 解析器管理

项目支持为不同网站开发专用解析器，并提供了完整的解析器管理功能。

### 查看所有解析器

列出当前项目中所有可用的解析器：

```bash
python manage.py list_parsers
```

### 创建新的解析器

使用内置的命令行工具创建解析器：

```bash
python manage.py create_parser 网站名 --domains example.com www.example.com
```

例如：

```bash
python manage.py create_parser news --domains news.example.com www.news.example.com
```

创建完成后，解析器会自动被系统识别，无需手动注册。

### 删除解析器

如果需要删除某个解析器：

```bash
python manage.py delete_parser 网站名
```

例如：

```bash
python manage.py delete_parser news
```

注意：此操作将永久删除解析器文件，请谨慎操作。

## 解析器开发

### 解析器工作原理

解析器基于工厂模式设计，系统会自动扫描parsers目录下所有以`_parser.py`结尾的文件，
并通过文件名推断类名来动态加载解析器。每个解析器都需要继承[BaseParser](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/slsd/parsers/base_parser.py#L3-L30)基类并实现相应的方法。

### 解析器结构要求

1. 文件名必须以`_parser.py`结尾，如`news_parser.py`
2. 类名必须遵循驼峰命名规则，且以`Parser`结尾，如`NewsParser`
3. 必须实现[domains](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/slsd/parsers/hnslsdxy_parser.py#L69-L70)属性，返回支持的域名列表
4. 必须实现[parse](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/slsd/parsers/hnslsdxy_parser.py#L33-L59)方法，用于解析网页并返回结构化数据

### 创建解析器详细步骤

1. 使用管理命令创建解析器模板：
   ```bash
   python manage.py create_parser website --domains example.com
   ```

2. 修改生成的解析器文件：
   - 调整CSS选择器以适配目标网站结构
   - 根据需要修改请求头或添加其他处理逻辑

3. 测试解析器确保能正确提取内容

### 解析器返回数据格式

每个解析器的[parse](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/slsd/parsers/hnslsdxy_parser.py#L33-L59)方法应该返回一个包含以下字段的字典：

```python
{
    'title': '文章标题',
    'date': '发布日期',
    'body': '正文文本内容',
    'content_div': BeautifulSoup对象，包含完整的正文内容
}
```

其中[content_div](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/slsd/get_data.py#L41-L41)会被用于提取文本和图片，所以需要包含完整的HTML结构。

### 解析器模板说明

模板文件中已包含PyInstaller兼容的导入方式，避免打包后出现导入错误。

## 项目结构

```
.
├── cli_main.py          # 命令行版本主程序
├── ui_main.py           # 图形界面版本主程序
├── Gui.ui               # 图形界面设计文件
├── get_data.py          # 数据获取模块
├── parser_factory.py    # 解析器工厂
├── parsers/             # 各网站解析器
│   ├── base_parser.py   # 解析器基类
│   ├── hnslsdxy_parser.py  # 湖南水利水电职院解析器
│   └── voc_parser.py    # m.voc.com.cn解析器
├── manage.py            # 解析器管理工具
├── build_gui.py         # GUI版本打包脚本
├── build_cli.py         # CLI版本打包脚本
├── requirements.txt     # 项目依赖
└── README.md            # 说明文档
```

## 注意事项

1. 第一次运行时会自动创建data和img目录用于存储文档和图片
2. 已存在的文章不会重复下载
3. 网络请求使用随机延迟避免过于频繁