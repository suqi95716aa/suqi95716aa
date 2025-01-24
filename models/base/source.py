import abc
from typing import List, Union, Dict

from dataclasses import dataclass, field


@dataclass
class SourceDatabaseConfig:
    """记录数据库相关的连接信息"""
    Label: str = field(default=None)
    Host: str = field(default=None)
    Port: int = field(default=None)
    User: str = field(default=None)
    Password: str = field(default=None)
    Database: str = field(default=None)
    Charset: str = field(default="utf8mb4")

    def __post_init__(self):
        if self.Port:
            self.Port = int(self.Port)


@dataclass
class SourceNativeConfig:
    """记录本地文件的相关信息"""
    Label: str = ""
    Paths: List = ""
    GroupList: List = ""
    Encodings: str = "utf-8"


class DataSourceBaseModel(abc.ABC):
    def __init__(self, Config: Union[SourceDatabaseConfig, SourceNativeConfig]):
        self.Config = Config

    def __enter__(self):
        """创建类时自动连接"""
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动销毁连接"""
        pass

    @abc.abstractmethod
    def format(self, **kwargs) -> Dict:
        """执行SQL"""
        pass






