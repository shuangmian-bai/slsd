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

```bash
python main.py
```

按提示输入搜索关键词和线程数即可开始检索。

### 打包为exe

```bash
python build_exe.py
```

打包完成后，可在dist目录找到可执行文件。

## 解析器开发

项目支持为不同网站开发专用解析器。

### 创建新的解析器

1. 复制 [parsers/parser_template.py](file:///C:/Users/Administrator/Desktop/%E5%88%98%E9%99%A2%E9%95%BF/slsd/parsers/parser_template.py) 并重命名为网站名_parser.py
2. 修改类名和domains属性
3. 根据目标网站结构调整parse方法中的选择器
4. 测试确保能正确提取内容

### 解析器模板说明

模板文件中已包含PyInstaller兼容的导入方式，避免打包后出现导入错误。

## 项目结构

```
.
├── main.py              # 主程序入口
├── get_data.py          # 数据获取模块
├── parser_factory.py    # 解析器工厂
├── parsers/             # 各网站解析器
│   ├── base_parser.py   # 解析器基类
│   ├── hnslsdxy_parser.py  # 湖南水利水电职院解析器
│   └── voc_parser.py    # m.voc.com.cn解析器
├── requirements.txt     # 项目依赖
├── build_exe.py         # 打包脚本
└── README.md            # 说明文档
```

## 注意事项

1. 第一次运行时会自动创建data和img目录用于存储文档和图片
2. 已存在的文章不会重复下载
3. 网络请求使用随机延迟避免过于频繁
