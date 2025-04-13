# utils/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any
from pathlib import Path


# todo:补充一下logger逻辑
class LogManager:
    _initialized = False
    _loggers = {}  # 缓存已创建的logger

    @classmethod
    def initialize(cls,
                   log_dir: str = "logs",
                   console_level: str = "INFO",
                   file_level: str = "DEBUG",
                   max_bytes: int = 10 * 1024 * 1024,  # 10MB
                   backup_count: int = 5,
                   enable_file_log: bool = True):
        """
        初始化全局日志配置
        :param log_dir: 日志存储目录
        :param console_level: 控制台日志级别
        :param file_level: 文件日志级别
        :param max_bytes: 单个日志文件最大大小（字节）
        :param backup_count: 保留的备份文件数量
        :param enable_file_log: 是否启用文件日志
        """
        if cls._initialized:
            return

        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # 基础日志格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)

        # 文件Handler（按大小轮转）
        handlers = [console_handler]

        if enable_file_log:
            # 主日志文件
            file_handler = RotatingFileHandler(
                filename=log_path / "app.log",
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(file_level)
            handlers.append(file_handler)

            # 错误日志单独记录
            error_handler = RotatingFileHandler(
                filename=log_path / "error.log",
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.WARNING)
            handlers.append(error_handler)

        # 配置根logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        for handler in handlers:
            root_logger.addHandler(handler)

        cls._initialized = True

        # 添加未捕获异常处理
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            logger = logging.getLogger("UnhandledException")
            logger.critical(
                "未捕获的异常:",
                exc_info=(exc_type, exc_value, exc_traceback)
            )

        sys.excepthook = handle_exception

    @classmethod
    def get_logger(cls,
                   name: Optional[str] = None,
                   extra_handlers: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """
        获取logger实例
        :param name: logger名称（通常使用__name__）
        :param extra_handlers: 额外的处理器配置
        """
        if not cls._initialized:
            cls.initialize()

        logger = logging.getLogger(name)

        # 避免重复添加handler
        if name not in cls._loggers:
            # 添加额外处理器
            if extra_handlers:
                for handler_config in extra_handlers.values():
                    handler = cls._create_handler(**handler_config)
                    logger.addHandler(handler)

            cls._loggers[name] = True

        return logger

    @classmethod
    def _create_handler(cls,
                        handler_type: str = "rotate_file",
                        level: str = "DEBUG",
                        filename: Optional[str] = None,
                        **kwargs) -> logging.Handler:
        """创建日志处理器"""
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        if handler_type == "rotate_file":
            handler = RotatingFileHandler(
                filename=filename,
                encoding='utf-8',
                **kwargs
            )
        elif handler_type == "timed_rotate":
            handler = TimedRotatingFileHandler(
                filename=filename,
                encoding='utf-8',
                **kwargs
            )
        elif handler_type == "console":
            handler = logging.StreamHandler(sys.stdout)
        else:
            raise ValueError(f"不支持的handler类型: {handler_type}")

        handler.setFormatter(formatter)
        handler.setLevel(level)
        return handler


# 初始化日志配置（在项目启动时调用）
LogManager.initialize(
    log_dir="logs",
    console_level="INFO",
    file_level="DEBUG",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=7,
    enable_file_log=True
)

# 快捷访问方式
get_logger = LogManager.get_logger
