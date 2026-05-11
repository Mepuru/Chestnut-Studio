"""日志装饰器

提供声明式方式定义日志源和记录方法调用。

核心装饰器：
- @log_source: 类装饰器，声明日志源
- @log_call: 方法装饰器，自动记录调用

使用示例：
    from chestnut_studio.utils.log_decorator import log_source, log_call
    from chestnut_studio.utils.log_manager import LogLevel

    @log_source("FFmpeg")
    class FFmpeg:
        @log_call(LogLevel.INFO)
        def get_video_info(self, path: str):
            pass
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from chestnut_studio.utils.log_manager import LogLevel, LogManager

F = TypeVar("F", bound=Callable[..., Any])


def log_source(source: str) -> Callable[[type], type]:
    """类装饰器：声明类的日志源

    被装饰的类会添加 _log_source 属性，供 @log_call 使用。

    Args:
        source: 日志源标识（如 "FFmpeg"、"波形"）

    Returns:
        装饰后的类

    Example:
        >>> @log_source("FFmpeg")
        ... class FFmpeg:
        ...     pass
        >>> FFmpeg._log_source
        'FFmpeg'
    """

    def decorator(cls: type) -> type:
        cls._log_source = source
        return cls

    return decorator


def log_call(
    level: LogLevel = LogLevel.INFO,
    message: str | None = None,
) -> Callable[[F], F]:
    """方法装饰器：自动记录方法调用

    自动记录方法的开始和结束，以及异常情况。
    被装饰的类应使用 @log_source 声明日志源。

    Args:
        level: 日志级别
        message: 自定义日志消息（默认使用方法名）

    Returns:
        装饰后的函数

    Example:
        >>> @log_source("FFmpeg")
        ... class FFmpeg:
        ...     @log_call(LogLevel.INFO)
        ...     def get_video_info(self, path: str):
        ...         pass
        ...
        ...     @log_call(LogLevel.INFO, message="获取视频信息")
        ...     def get_video_info_custom(self, path: str):
        ...         pass
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取日志源（从 self._log_source 或默认值）
            source = getattr(args[0], "_log_source", "Unknown") if args else "Unknown"
            logger = LogManager.instance().get_logger(source)

            # 输出方法开始日志
            msg = message or func.__name__
            logger.log(level, f"{msg} 开始")

            try:
                result = func(*args, **kwargs)
                # 输出方法成功日志
                logger.log(level, f"{msg} 成功")
                return result
            except Exception as e:
                # 输出方法失败日志
                logger.error(f"{msg} 失败: {e}")
                raise

        return wrapper  # type: ignore[return-value]

    return decorator
