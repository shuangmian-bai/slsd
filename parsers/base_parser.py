from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    解析器基类，定义了解析器的接口
    """

    @abstractmethod
    def parse(self, url):
        """
        解析给定URL的页面内容
        
        Args:
            url (str): 要解析的页面URL
            
        Returns:
            dict: 包含标题、日期、正文等内容的字典
        """
        pass

    @property
    @abstractmethod
    def domains(self):
        """
        返回该解析器支持的域名列表
        
        Returns:
            list: 支持的域名列表
        """
        pass