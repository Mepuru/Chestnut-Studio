"""信号订阅装饰器

提供装饰器方式声明信号订阅，简化开发。

使用方式：
    from chestnut_studio.ui.signal_decorator import subscribe, relay

    class WaveformCard(BaseCard):
        @subscribe("player.position_changed")
        def update_position(self, ms): ...

        @subscribe("player.duration_changed")
        def set_duration(self, ms): ...

        @relay("translate.jump_to_next")
        def _handle_jump_to_next(self, col, start_ms): ...
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


# 存储订阅信息的属性名
_SUBSCRIBE_ATTR = "_signal_subscriptions"
_RELAY_ATTR = "_signal_relays"


def subscribe(source_key: str) -> Callable:
    """装饰器：声明方法订阅某个信号

    Args:
        source_key: 信号源，格式 "card_id.signal_name"

    Usage:
        @subscribe("player.position_changed")
        def update_position(self, ms): ...
    """
    def decorator(func: Callable) -> Callable:
        if not hasattr(func, _SUBSCRIBE_ATTR):
            setattr(func, _SUBSCRIBE_ATTR, {})
        getattr(func, _SUBSCRIBE_ATTR)[source_key] = func.__name__
        return func
    return decorator


def relay(source_key: str) -> Callable:
    """装饰器：声明方法作为中转处理函数

    与 subscribe 类似，但用于 MainWindow 中转处理。

    Args:
        source_key: 信号源，格式 "card_id.signal_name"

    Usage:
        @relay("translate.jump_to_next")
        def _on_jump_to_next(self, col, start_ms): ...
    """
    def decorator(func: Callable) -> Callable:
        if not hasattr(func, _RELAY_ATTR):
            setattr(func, _RELAY_ATTR, {})
        getattr(func, _RELAY_ATTR)[source_key] = func.__name__
        return func
    return decorator


def collect_subscriptions(obj: Any) -> dict[str, str]:
    """收集对象上所有 @subscribe 装饰器声明的订阅

    Args:
        obj: 要收集订阅的对象

    Returns:
        {source_key: handler_name} 字典
    """
    subscriptions = {}

    # 遍历对象的所有方法
    for attr_name in dir(obj):
        if attr_name.startswith("_"):
            continue
        attr = getattr(obj, attr_name, None)
        if callable(attr) and hasattr(attr, _SUBSCRIBE_ATTR):
            subscriptions.update(getattr(attr, _SUBSCRIBE_ATTR))

    return subscriptions


def collect_relays(obj: Any) -> dict[str, str]:
    """收集对象上所有 @relay 装饰器声明的中转处理

    Args:
        obj: 要收集中转处理的对象

    Returns:
        {source_key: handler_name} 字典
    """
    relays = {}

    # 遍历对象的所有方法
    for attr_name in dir(obj):
        attr = getattr(obj, attr_name, None)
        if callable(attr) and hasattr(attr, _RELAY_ATTR):
            relays.update(getattr(attr, _RELAY_ATTR))

    return relays
