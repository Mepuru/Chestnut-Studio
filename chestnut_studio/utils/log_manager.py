"""统一日志管理器

提供声明式、可扩展的日志系统，替代散落的 print() 调用。

核心组件：
- LogLevel: 日志级别枚举
- LogRecord: 日志记录数据类
- Logger: 日志器实例（按模块划分）
- LogManager: 日志管理器（单例，可插拔 handler）

每条日志自动添加 "ChestnutStudio vX.X: " 前缀。

使用示例：
    from chestnut_studio.utils.log_manager import LogManager

    logger = LogManager.instance().get_logger("FFmpeg")
    logger.info("视频信息: 1920x1080")
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from chestnut_studio.utils.version import get_version

# 日志前缀（运行时确定一次）
_LOG_PREFIX = f"ChestnutStudio v{get_version()}: "


class LogLevel(Enum):
    """日志级别"""

    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


@dataclass(frozen=True, slots=True)
class LogRecord:
    """日志记录

    Attributes:
        source: 日志源标识（如 "FFmpeg"、"波形"）
        level: 日志级别
        message: 日志消息
    """

    source: str
    level: LogLevel
    message: str


class Logger:
    """日志器实例

    每个模块（如 FFmpeg、波形）获取自己的 Logger 实例，
    通过 source 标识来源。

    Args:
        source: 日志源标识
    """

    def __init__(self, source: str) -> None:
        self.source = source

    def log(self, level: LogLevel, message: str) -> None:
        """输出指定级别的日志

        自动在消息前添加 "ChestnutStudio vX.X: " 前缀。

        Args:
            level: 日志级别
            message: 日志消息
        """
        LogManager.instance().emit(LogRecord(self.source, level, f"{_LOG_PREFIX}{message}"))

    def debug(self, message: str) -> None:
        """输出 DEBUG 级别日志"""
        self.log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        """输出 INFO 级别日志"""
        self.log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        """输出 WARNING 级别日志"""
        self.log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        """输出 ERROR 级别日志"""
        self.log(LogLevel.ERROR, message)


class LogManager:
    """日志管理器（单例）

    职责：
    - 管理所有日志源
    - 分发日志记录到处理器
    - 支持动态添加/移除处理器
    - 支持日志级别过滤

    使用示例：
        # 获取管理器实例
        manager = LogManager.instance()

        # 添加处理器（输出到标准输出）
        def stdout_handler(record: LogRecord):
            print(f"[{record.source}] {record.message}")
        manager.add_handler(stdout_handler)

        # 获取日志器并输出
        logger = manager.get_logger("MyModule")
        logger.info("Hello, world!")
    """

    _instance: LogManager | None = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._loggers: dict[str, Logger] = {}
        self._handlers: list[Callable[[LogRecord], None]] = []
        self._min_level: LogLevel = LogLevel.DEBUG
        self._handler_lock: threading.Lock = threading.Lock()

    @classmethod
    def instance(cls) -> LogManager:
        """获取单例实例

        Returns:
            LogManager 单例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例（仅用于测试）"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._initialized = False
                cls._instance = None

    def get_logger(self, source: str) -> Logger:
        """获取或创建日志器

        Args:
            source: 日志源标识（如 "FFmpeg"、"波形"）

        Returns:
            Logger 实例
        """
        if source not in self._loggers:
            self._loggers[source] = Logger(source)
        return self._loggers[source]

    def set_min_level(self, level: LogLevel) -> None:
        """设置最低日志级别

        低于此级别的日志将被忽略。

        Args:
            level: 最低日志级别
        """
        self._min_level = level

    def get_min_level(self) -> LogLevel:
        """获取当前最低日志级别

        Returns:
            当前最低日志级别
        """
        return self._min_level

    def add_handler(self, handler: Callable[[LogRecord], None]) -> None:
        """添加日志处理器

        Args:
            handler: 处理函数，接收 LogRecord 参数
        """
        with self._handler_lock:
            self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[LogRecord], None]) -> None:
        """移除日志处理器

        Args:
            handler: 之前添加的处理函数
        """
        with self._handler_lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def clear_handlers(self) -> None:
        """清空所有日志处理器"""
        with self._handler_lock:
            self._handlers.clear()

    def emit(self, record: LogRecord) -> None:
        """发射日志记录

        如果记录级别 >= 最低级别，分发到所有处理器。
        处理器异常会被捕获，不影响主程序。

        Args:
            record: 日志记录
        """
        if record.level.value < self._min_level.value:
            return

        with self._handler_lock:
            handlers = self._handlers.copy()

        for handler in handlers:
            try:
                handler(record)
            except Exception:  # 故意宽捕：handler 异常不影响主程序
                pass
