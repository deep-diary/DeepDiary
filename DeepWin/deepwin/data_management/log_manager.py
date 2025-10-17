# src/data_management/log_manager.py
# 日志管理器

import logging
import os
from datetime import datetime
import sys

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

    def __init__(self, log_dir="logs", log_file_name="deepwin", console_level=logging.WARNING, file_level=logging.INFO):
        if self._initialized:
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
            # 文件处理器 - 记录INFO及以上级别
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