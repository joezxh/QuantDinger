"""
Logging utilities (local-only friendly).
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger():
    """配置全局日志"""
    log_level = os.getenv('LOG_LEVEL', 'DEBUG')
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    debug_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    effective_format = debug_format if log_level.upper() == 'DEBUG' else log_format

    # 创建日志目录
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 文件处理器（记录所有级别）
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    file_handler.setFormatter(logging.Formatter(effective_format))

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    console_handler.setFormatter(logging.Formatter(effective_format))

    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    # 清除已有 handler 避免重复
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 过滤 werkzeug 的 INFO 级别日志（减少噪音）
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)

    # 过滤 kline 路由的 INFO 级别日志（减少噪音）
    kline_logger = logging.getLogger('app.routes.kline')
    kline_logger.setLevel(logging.WARNING)

    # USDT 对账：即使 LOG_LEVEL=WARNING，也保留本模块 INFO
    _usdt = logging.getLogger("app.services.usdt_payment_service")
    _usdt.setLevel(logging.INFO)
    _billing = logging.getLogger("app.routes.billing")
    _billing.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        Logger 实例
    """
    return logging.getLogger(name)

