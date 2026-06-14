# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在本仓库中工作时提供指导。

## 语言规则

与用户的所有交互（日志、询问、文档输出）均使用中文。

## 项目概述

湖南水利水电信息检索工具 —— 从湖南水利水电职业技术学院官网及其他支持的网站抓取文章，保存为 Word 文档（.docx）。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 CLI 版本
python cli_main.py

# 运行 GUI 版本（PyQt6，面向 Windows）
python ui_main.py

# 解析器管理
python manage.py list_parsers
python manage.py create_parser NAME --domains example.com www.example.com
python manage.py delete_parser NAME

# 打包为可执行文件（PyInstaller）
python build_gui.py    # GUI exe → dist/（无控制台窗口）
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
6. `save_to_word()` 将文本和图片保存为 .docx 文件到 `data/word/`

### 解析器插件系统

核心架构模式是 **自动发现的解析器工厂**（`parser_factory.py`）：

- 扫描 `parsers/` 目录下所有 `*_parser.py` 文件（排除 `base_parser.py`）
- 类名由文件名推断：`foo_parser.py` → `FooParser`
- 每个解析器通过 `domains` 属性注册；`ParserFactory.get_parser(url)` 按域名查找
- 未注册的域名回退为外部链接处理

**解析器契约**（`parsers/base_parser.py`）：
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, url) -> dict:
        # 必须返回：{'title': str, 'date': str, 'body': str, 'content_div': BeautifulSoup}

    @property
    @abstractmethod
    def domains(self) -> list:
        # 必须返回支持的域名列表
```

**创建新解析器：**
1. `python manage.py create_parser name --domains example.com`
2. 编辑生成的 `parsers/name_parser.py` —— 调整目标网站的 CSS 选择器
3. 解析器在导入时自动注册，无需手动配置

### PyInstaller 兼容性

每个解析器文件使用多重回退导入模式来兼容开发环境和打包环境。新解析器必须遵循此模式 —— 参见 `parsers/parser_template.py` 中的标准模板。工厂在运行时也处理了 PyInstaller 的 `sys._MEIPASS` 目录以定位解析器文件。

### 线程安全

`get_data.py` 使用 `threading.Lock` 保护并发保存文章时的文件系统操作。网络请求使用随机延迟以避免频率限制。

## 平台说明

GUI 使用 `os.startfile()`，该函数仅 Windows 可用。本应用主要面向 Windows 用户。
