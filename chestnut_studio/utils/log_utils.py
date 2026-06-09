"""日志工具函数 — 自动记录方法级操作日志的装饰器"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from chestnut_studio.utils.log_manager import LogLevel, LogManager

F = TypeVar("F", bound=Callable[..., Any])


def log_operation(
    message: str = "",
    source: str = "UI",
    level: LogLevel = LogLevel.INFO,
    after: bool = False,
) -> Callable[[F], F]:
    """自动记录方法级操作日志的装饰器。

    支持两种模式：

    1. 前置模式（after=False，默认）— 方法调用前记录日志。
       模板支持 {param_name} 占位符绑定到方法参数。

    2. 后置模式（after=True）— 方法调用后记录日志。
       模板除 {param_name} 外额外支持 {result} 占位符，
       绑定到方法的返回值。

    用法:
        @log_operation("打开视频: {path}")
        def _on_open_video(self, path: str):
            ...

        @log_operation("打开百宝箱")
        def _open_debug_box(self):
            ...

        @log_operation("清空笔记 ({result} 条)", after=True)
        def _clear_all(self) -> int:
            ...
            return count

        @log_operation("{result}", after=True)
        def _toggle_play_pause(self) -> str:
            was_playing = self._is_playing
            self.play_pause()
            return "暂停" if was_playing else "播放"

        @log_operation("解码视频信息", source="FFmpeg", level=LogLevel.DEBUG)
        def get_video_info(self, video_path: str):
            ...

    Args:
        message: 日志消息模板。支持 {param_name} 格式占位符，
                 自动替换为同名的函数参数值。为空时不记录日志。
        source: 日志源标识，默认 "UI"。
        level: 日志级别，默认 INFO。
        after: 后置模式。设为 True 时，在方法执行后记录日志，
               message 中可使用 {result} 引用返回值。
    """
    if not message:
        return lambda func: func  # type: ignore[return-value]

    def decorator(func: F) -> F:
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            if not after:
                try:
                    formatted = message.format(**bound.arguments)
                except (KeyError, ValueError):
                    formatted = message
                LogManager.instance().get_logger(source).log(level, formatted)
                return func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                context = dict(bound.arguments)
                context["result"] = result
                try:
                    formatted = message.format(**context)
                except (KeyError, ValueError):
                    formatted = message
                LogManager.instance().get_logger(source).log(level, formatted)
                return result

        return wrapper  # type: ignore[return-value]

    return decorator
