import os
import importlib
import sys
from urllib.parse import urlparse


class ParserFactory:
    """
    解析器工厂类，用于根据域名获取相应的解析器实例
    """
    
    # 解析器注册表
    _parsers = {}
    
    @classmethod
    def _get_parsers_dir(cls):
        """
        获取parsers目录路径，兼容PyInstaller打包环境
        """
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe环境
            # PyInstaller会将数据文件放在sys._MEIPASS目录中
            bundle_dir = sys._MEIPASS
            parsers_dir = os.path.join(bundle_dir, 'parsers')
        else:
            # 开发环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parsers_dir = os.path.join(current_dir, 'parsers')
        return parsers_dir
    
    @classmethod
    def _load_parsers(cls):
        """
        自动加载并注册所有解析器
        """
        if cls._parsers:  # 如果已经加载过，就不再重复加载
            return
            
        # 获取parsers目录路径
        parsers_dir = cls._get_parsers_dir()
        print(f"查找解析器目录: {parsers_dir}")  # 调试信息
        
        if not os.path.exists(parsers_dir):
            print(f"警告: 找不到parsers目录: {parsers_dir}")
            return
            
        # 遍历parsers目录下的所有解析器文件
        for filename in os.listdir(parsers_dir):
            if filename.endswith('_parser.py') and filename != 'base_parser.py':
                module_name = filename[:-3]  # 移除.py后缀
                try:
                    # 动态导入模块
                    if getattr(sys, 'frozen', False):
                        # 打包环境 - 直接从_MEIPASS目录加载
                        spec = importlib.util.spec_from_file_location(
                            module_name, 
                            os.path.join(parsers_dir, filename)
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    else:
                        # 开发环境
                        module = importlib.import_module(f'parsers.{module_name}')
                    
                    # 获取类名（假设类名是文件名的驼峰命名，去掉_parser后缀）
                    class_name = ''.join(word.capitalize() for word in module_name.split('_')[:-1]) + 'Parser'
                    
                    # 获取解析器类并实例化
                    parser_class = getattr(module, class_name)
                    parser_instance = parser_class()
                    
                    # 注册解析器
                    cls.register_parser(parser_instance)
                    print(f"成功加载解析器: {class_name}")  # 调试信息
                except (ImportError, AttributeError) as e:
                    print(f"警告: 无法加载解析器 {module_name}: {e}")
    
    @classmethod
    def register_parser(cls, parser):
        """
        注册解析器
        
        Args:
            parser: 解析器实例
        """
        for domain in parser.domains:
            cls._parsers[domain] = parser
    
    @classmethod
    def get_parser(cls, url):
        """
        根据URL获取相应的解析器
        
        Args:
            url (str): 要解析的URL
            
        Returns:
            解析器实例，如果没有找到则返回None
        """
        cls._load_parsers()  # 确保解析器已加载
        domain = urlparse(url).netloc
        return cls._parsers.get(domain)
    
    @classmethod
    def is_registered_domain(cls, url):
        """
        检查域名是否已注册
        
        Args:
            url (str): 要检查的URL
            
        Returns:
            bool: 如果域名已注册返回True，否则返回False
        """
        cls._load_parsers()  # 确保解析器已加载
        domain = urlparse(url).netloc
        return domain in cls._parsers


# 初始化时自动加载所有解析器
ParserFactory._load_parsers()