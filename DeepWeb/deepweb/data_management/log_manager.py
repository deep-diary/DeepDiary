# src/data_management/log_manager.py
# 日志管理器

import logging
import os
from datetime import datetime
import sys

# 尝试导入 colorlog，如果失败则使用标准 logging
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

class LogManager:
    """
    统一的日志管理类。
    提供获取 logger 实例的方法，并配置日志输出到文件和控制台。
    """
    _instance = None # 单例模式
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir="logs", log_file_name="deepweb", console_level=logging.WARNING, file_level=logging.INFO):
        # 如果已经初始化，更新日志级别和格式化器（如果提供了新的级别）
        if self._initialized:
            # 更新控制台日志级别（如果提供了新的级别且与默认值不同）
            if console_level != logging.WARNING:
                self.set_console_level(console_level)
            if file_level != logging.INFO:
                self.set_file_level(file_level)
            # 更新控制台格式化器（确保使用最新的颜色格式）
            self._update_console_formatter()
            return

        self.log_dir = log_dir
        # log_file_name 增加时间戳
        self.log_file_name = f"{log_file_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.log_file_path = os.path.join(self.log_dir, self.log_file_name)

        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)

        # 配置根 logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG) # 根级别保持DEBUG，让handlers控制输出

        # 避免重复添加 handlers
        if not self.root_logger.handlers:
            # 文件处理器 - 记录INFO及以上级别（文件不使用颜色）
            file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
            file_handler.setLevel(file_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.root_logger.addHandler(file_handler)

            # 控制台处理器 - 默认WARNING级别，减少控制台输出
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(console_level)
            
            # 如果 colorlog 可用，使用带颜色的格式化器
            # 参考服务器端格式：时间[模块名]-级别-消息
            if COLORLOG_AVAILABLE:
                console_formatter = colorlog.ColoredFormatter(
                    '%(green)s%(asctime)s%(reset)s[%(cyan)s%(name)s%(reset)s]-'
                    '%(log_color)s%(levelname)s%(reset)s-'
                    '%(message)s',
                    datefmt='%y%m%d %H:%M:%S',  # 与服务器端格式一致：YYMMDD HH:mm:ss
                    reset=True,
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    },
                    secondary_log_colors={},
                    style='%'
                )
            else:
                # 回退到标准格式化器
                console_formatter = logging.Formatter(
                    '%(levelname)s - %(filename)s:%(funcName)s - %(message)s'
                )
            
            console_handler.setFormatter(console_formatter)
            self.root_logger.addHandler(console_handler)

        self._initialized = True
        self.get_logger(__name__).info("LogManager: 日志系统初始化完成。")

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的 logger 实例。
        Args:
            name (str): logger 的名称，通常是模块的 __name__。
        Returns:
            logging.Logger: logger 实例。
        """
        return logging.getLogger(name)
    
    def set_console_level(self, level: int):
        """
        设置控制台日志级别
        Args:
            level (int): 日志级别，如 logging.INFO, logging.WARNING, logging.ERROR
        """
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
                self.get_logger(__name__).info(f"控制台日志级别已设置为: {logging.getLevelName(level)}")
    
    def set_file_level(self, level: int):
        """
        设置文件日志级别
        Args:
            level (int): 日志级别，如 logging.DEBUG, logging.INFO, logging.WARNING
        """
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
                self.get_logger(__name__).info(f"文件日志级别已设置为: {logging.getLevelName(level)}")
    
    def set_all_levels(self, console_level: int, file_level: int):
        """
        同时设置控制台和文件的日志级别
        Args:
            console_level (int): 控制台日志级别
            file_level (int): 文件日志级别
        """
        self.set_console_level(console_level)
        self.set_file_level(file_level)
    
    def _update_console_formatter(self):
        """
        更新控制台格式化器，确保使用最新的颜色格式
        用于在应用运行时更新格式化器（例如安装 colorlog 后）
        """
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                # 重新检查 colorlog 是否可用（可能在运行时安装）
                try:
                    import colorlog
                    # 使用带颜色的格式化器
                    console_formatter = colorlog.ColoredFormatter(
                        '%(green)s%(asctime)s%(reset)s[%(cyan)s%(name)s%(reset)s]-'
                        '%(log_color)s%(levelname)s%(reset)s-'
                        '%(message)s',
                        datefmt='%y%m%d %H:%M:%S',  # 与服务器端格式一致：YYMMDD HH:mm:ss
                        reset=True,
                        log_colors={
                            'DEBUG': 'cyan',
                            'INFO': 'green',
                            'WARNING': 'yellow',
                            'ERROR': 'red',
                            'CRITICAL': 'red,bg_white',
                        },
                        secondary_log_colors={},
                        style='%'
                    )
                    handler.setFormatter(console_formatter)
                except ImportError:
                    # colorlog 不可用，使用标准格式化器（带时间戳）
                    console_formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s',
                        datefmt='%y%m%d %H:%M:%S'
                    )
                    handler.setFormatter(console_formatter)
                break