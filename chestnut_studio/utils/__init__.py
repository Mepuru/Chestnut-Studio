"""工具函数模块"""

from chestnut_studio.utils.log_manager import (
    Logger,
    LogLevel,
    LogManager,
    LogRecord,
)
from chestnut_studio.utils.time_utils import ms_to_time_str, split_time
from chestnut_studio.utils.version import get_version


def get_logger(source: str) -> Logger:
    """获取或创建日志器的快捷函数

    Args:
        source: 日志源标识（模块名）

    Returns:
        Logger 实例
    """
    return LogManager.instance().get_logger(source)


__all__ = [
    "LogLevel",
    "LogManager",
    "LogRecord",
    "Logger",
    "get_logger",
    "ms_to_time_str",
    "split_time",
    "get_version",
]
