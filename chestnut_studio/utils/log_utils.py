"""日志工具函数 — 自动记录方法级操作日志的装饰器"""

from __future__ import annotations

import functools
import inspect

from chestnut_studio.utils.log_manager import LogLevel, LogManager


def log_operation(
    message: str = "",
    source: str = "UI",
    level: LogLevel = LogLevel.INFO,
):
    """自动记录方法级操作日志的装饰器。

    在方法调用前记录日志。支持使用 {param_name} 占位符绑定到方法参数。

    用法:
        @log_operation("打开视频: {path}")
        def _on_open_video(self, path: str):
            ...

        @log_operation("打开百宝箱")
        def _open_debug_box(self):
            ...

        @log_operation("解码视频信息", source="FFmpeg", level=LogLevel.DEBUG)
        def get_video_info(self, video_path: str):
            ...

    Args:
        message: 日志消息模板。支持 {param_name} 格式占位符，
                 自动替换为同名的函数参数值。为空时不记录日志。
        source: 日志源标识，默认 "UI"。
        level: 日志级别，默认 INFO。
    """
    if not message:
        # 空消息时不记录日志，等同于不使用装饰器
        return lambda func: func

    def decorator(func):
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            try:
                formatted = message.format(**bound.arguments)
            except (KeyError, ValueError):
                formatted = message
            LogManager.instance().get_logger(source).log(level, formatted)
            return func(*args, **kwargs)

        return wrapper

    return decorator
