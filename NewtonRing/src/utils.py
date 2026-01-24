"""
工具函数模块
文件名: utils.py
位置: src/utils.py

提供通用的辅助函数
"""

import os
import logging
from datetime import datetime


def setup_logger(name, log_file=None, level=logging.INFO):
    """
    设置日志记录器
    
    参数:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        level: 日志级别
    
    返回:
        logger对象
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定）
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def ensure_dir(directory):
    """
    确保目录存在，不存在则创建
    
    参数:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"✅ 创建目录: {directory}")


def get_timestamp():
    """
    获取当前时间戳字符串
    
    返回:
        格式: YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# 常量定义
DEFAULT_WAVELENGTH = 589.3  # 钠光波长（nm）
PIXEL_TO_MM = 0.01  # 默认像素到毫米的转换系数（需要标定）
