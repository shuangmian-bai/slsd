import os
import importlib
from urllib.parse import urlparse


class ParserFactory:
    """
    解析器工厂类，用于根据域名获取相应的解析器实例
    """
    
    # 解析器注册表
    _parsers = {}
    
    @classmethod
    def _load_parsers(cls):
        """
        自动加载并注册所有解析器
        """
        if cls._parsers:  # 如果已经加载过，就不再重复加载
            return
            
        # 获取parsers目录路径
        parsers_dir = os.path.join(os.path.dirname(__file__), 'parsers')
        if not os.path.exists(parsers_dir):
            return
            
        # 遍历parsers目录下的所有解析器文件
        for filename in os.listdir(parsers_dir):
            if filename.endswith('_parser.py') and filename != 'base_parser.py':
                module_name = filename[:-3]  # 移除.py后缀
                try:
                    # 动态导入模块
                    module = importlib.import_module(f'parsers.{module_name}')
                    
                    # 获取类名（假设类名是文件名的驼峰命名，去掉_parser后缀）
                    class_name = ''.join(word.capitalize() for word in module_name.split('_')[:-1]) + 'Parser'
                    
                    # 获取解析器类并实例化
                    parser_class = getattr(module, class_name)
                    parser_instance = parser_class()
                    
                    # 注册解析器
                    cls.register_parser(parser_instance)
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