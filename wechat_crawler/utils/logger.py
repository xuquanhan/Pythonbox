#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块

提供统一的日志配置和管理功能
"""

import os
import logging
import logging.handlers
from logging import Logger
from typing import Optional

class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self.loggers = {}
        self.log_dir = 'logs'
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def get_logger(self, name: str, level: int = logging.INFO) -> Logger:
        """获取日志记录器"""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False  # 避免重复日志
        
        # 清除已有的处理器
        for handler in logger.handlers:
            logger.removeHandler(handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # 文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, f'{name}.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        self.loggers[name] = logger
        return logger
    
    def set_level(self, name: str, level: int):
        """设置日志级别"""
        if name in self.loggers:
            logger = self.loggers[name]
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)
    
    def shutdown(self):
        """关闭所有日志处理器"""
        for logger in self.loggers.values():
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()
        self.loggers.clear()

# 全局日志管理器
logger_manager = LoggerManager()

def get_logger(name: str, level: int = logging.INFO) -> Logger:
    """获取日志记录器的便捷函数"""
    return logger_manager.get_logger(name, level)

def setup_logging(level: int = logging.INFO):
    """设置全局日志"""
    # 配置根日志
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除已有的处理器
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # 文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join('logs', 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # 添加处理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def shutdown_logging():
    """关闭日志"""
    logger_manager.shutdown()
    # 关闭根日志处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.close()
    root_logger.handlers.clear()

# 预设的日志记录器
app_logger = get_logger('app')
crawler_logger = get_logger('crawler')
storage_logger = get_logger('storage')
scheduler_logger = get_logger('scheduler')
utils_logger = get_logger('utils')

__all__ = [
    'LoggerManager',
    'logger_manager',
    'get_logger',
    'setup_logging',
    'shutdown_logging',
    'app_logger',
    'crawler_logger',
    'storage_logger',
    'scheduler_logger',
    'utils_logger'
]
