# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言规则

与用户的所有交互（日志、询问、文档输出）均使用中文。

## 项目概述

湖南水利水电信息检索工具 —— 从湖南水利水电职业技术学院官网及其他支持的网站抓取文章，保存为 Word 文档（.docx）。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 CLI 版本（交互式搜索模式）
python cli_main.py

# 全站扫描模式（dzk.hnslsdxy.com，自动去重）
python cli_main.py --scan
python cli_main.py --scan --threads 10

# 运行 GUI 版本（PyQt6，面向 Windows）
python ui_main.py

# 解析器管理
python manage.py list_parsers
python manage.py create_parser NAME --domains example.com www.example.com
python manage.py delete_parser NAME

# 打包为可执行文件（PyInstaller --onefile 模式）
python build_gui.py    # GUI exe → dist/（无控制台窗口，含 Gui.ui 和 icon/）
python build_cli.py    # CLI exe → dist/（有控制台窗口）
```

本项目无测试套件、无 linter 配置、无 CI/CD。

## 架构

### 核心数据流

1. 用户输入搜索关键词和线程数（CLI 或 GUI）
2. `get_data.py:get_links()` 查询 hnslsdxy.com 搜索 API 收集文章 URL
3. 通过 `ThreadPoolExecutor` 将 URL 分发给 `get_data.py:process_article()`
4. `ParserFactory.get_parser(url)` 根据域名选择对应解析器
5. 解析器提取标题、日期和正文内容
6. `save_to_word()` 将文本和图片保存为 .docx 文件到 `data/word/`，视频缓存到 `data/video/`

### 全站扫描器（scanner.py）

用于 `dzk.hnslsdxy.com` 和 `www.hnslsdxy.com` 全站文章抓取，通过 `--scan` 参数触发（默认 20 线程）：

- 多线程爬取主页发现所有 `contentlist.aspx?id=xxx` 列表页
- 每个列表页自动检测分页（解析 "当前为N/M页"），遍历全部 `&page=N`
- 多线程并发扫描所有列表页的全部分页，收集两类文章链接：
  - 内部文章：`contentshow.aspx?id=xxx`
  - 外部文章：指向其他域名的完整 URL（如媒体聚焦栏目）
- 内部文章以文章 ID 为唯一标识，外部文章以 URL 为唯一标识，通过 `data/record.json` 记录
- 去重：跳过 record.json 中已存在的记录 + `save_to_word` 文件存在检查兜底
- 多线程调用 `process_article()` 抓取新文章（含无解析器的外部文章），增量抓取
- 扫描结束后输出所有未注册域名汇总及对应的 `create_parser` 命令

### 解析器插件系统

核心架构模式是 **自动发现的解析器工厂**（`parser_factory.py`）：

- 扫描 `parsers/` 目录下所有 `*_parser.py` 文件（排除 `base_parser.py`）
- 类名由文件名推断：`foo_parser.py` → `FooParser`
- 每个解析器通过 `domains` 属性注册；`ParserFactory.get_parser(url)` 按域名查找
- 未注册的域名回退为外部链接处理
- 工厂在模块导入时自动调用 `_load_parsers()` 完成初始化

**解析器契约**（`parsers/base_parser.py`）：
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, url) -> dict:
        # 必须返回：{'title': str, 'date': str, 'body': str, 'content_div': BeautifulSoup}
        # 可选返回：'videos': [{'url', 'thumbnail', 'duration'}]
        #           'images': [{'url', 'desc'}]

    @property
    @abstractmethod
    def domains(self) -> list:
        # 必须返回支持的域名列表
```

**特殊解析器 — 学习强国（xuexi.cn）：**

xuexi.cn 是 SPA 动态渲染站点，无法通过常规 HTML 解析获取内容。`XuexiParser` 通过 JS 数据文件接口获取数据：
- 数据源：`https://boot-source.xuexi.cn/data/app/{文章ID}.js`（JSONP 格式）
- 返回扩展字段：`videos`（含 MP4 直链和封面图）、`images`（文章配图）

**视频支持：**

`save_to_word()` 处理 `videos` 字段时：
1. 下载视频封面图插入 Word
2. 下载 MP4 视频到 `data/video/` 缓存目录
3. 在 Word 中插入缓存路径文本

**已注册域名：**

| 解析器 | 域名 |
|--------|------|
| HnslsdxyParser | `www.hnslsdxy.com`, `hnslsdxy.com`, `dzk.hnslsdxy.com` |
| VocParser | `m.voc.com.cn` |
| HnjyParser | `news.hnjy.com.cn` |
| HnedutvParser | `m.hnedutv.com`, `www.m.hnedutv.com` |
| XuexiParser | `www.xuexi.cn`, `xuexi.cn` |

**创建新解析器：**
1. `python manage.py create_parser name --domains example.com`
2. 编辑生成的 `parsers/name_parser.py` —— 调整目标网站的 CSS 选择器
3. 解析器在导入时自动注册，无需手动配置

### PyInstaller 兼容性

每个解析器文件使用多重回退导入模式来兼容开发环境和打包环境。新解析器必须遵循此模式 —— 参见 `parsers/parser_template.py` 中的标准模板。工厂在运行时也处理了 PyInstaller 的 `sys._MEIPASS` 目录以定位解析器文件。

### 线程安全

`get_data.py` 使用 `threading.Lock` 保护并发保存文章时的文件系统操作。`scanner.py` 使用独立的 `record_lock` 保护 `record.json` 的读写。网络请求使用随机延迟以避免频率限制。

## 运行时数据目录

```
data/
├── word/          # 生成的 .docx 文件
├── img/           # 下载的图片缓存
├── video/         # 下载的视频缓存（MP4）
└── record.json    # 扫描器已处理文章记录
```

## 平台说明

GUI 使用 `os.startfile()`，该函数仅 Windows 可用。本应用主要面向 Windows 用户。
