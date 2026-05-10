"""信号管理模块

集中管理所有卡片和组件间的信号连接，让 MainWindow 不需要关心信号细节。

使用方式：
    signal_mgr = SignalManager(main_window)
    signal_mgr.register_cards(cards)
    signal_mgr.register_special("toolbar", toolbar)
    signal_mgr.register_special("statusbar", status_bar)
    signal_mgr.connect_all()
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from chestnut_studio.ui.cards.base_card import BaseCard


class SignalManager:
    """信号管理器

    职责：
    - 收集所有卡片的信号声明（包括 @subscribe 装饰器）
    - 管理中转处理函数（包括 @relay 装饰器）
    - 自动连接所有信号
    """

    def __init__(self, main_window: Any):
        self._main_window = main_window
        self._cards: dict[str, BaseCard] = {}
        self._special_components: dict[str, Any] = {}

        # 中转处理函数注册表 {source_key: handler}
        self._relay_handlers: dict[str, Callable] = {}

        # 动态中转处理函数（由组件动态注册）
        self._dynamic_relays: dict[str, list[Callable]] = {}

    def register_main_window(self, main_window: Any) -> None:
        """注册主窗口，自动收集 @relay 装饰器声明"""
        self._main_window = main_window

        # 自动收集 MainWindow 的 @relay 装饰器声明
        from chestnut_studio.ui.signal_decorator import collect_relays
        relays = collect_relays(main_window)
        for source_key, handler_name in relays.items():
            handler = getattr(main_window, handler_name, None)
            if handler:
                self._relay_handlers[source_key] = handler

    def register_cards(self, cards: dict[str, BaseCard]) -> None:
        """注册所有卡片"""
        self._cards = cards

        # 自动收集 @relay 装饰器声明
        from chestnut_studio.ui.signal_decorator import collect_relays
        for card_id, card in cards.items():
            relays = collect_relays(card)
            for source_key, handler_name in relays.items():
                handler = getattr(card, handler_name, None)
                if handler:
                    self._relay_handlers[source_key] = handler

    def register_special(self, component_id: str, component: Any) -> None:
        """注册特殊组件（toolbar、statusbar 等）"""
        self._special_components[component_id] = component

    def register_relay(self, source_key: str, handler: Callable) -> None:
        """注册中转处理函数

        Args:
            source_key: 格式 "card_id.signal_name"
            handler: 处理函数
        """
        self._relay_handlers[source_key] = handler

    def register_relays(self, relays: dict[str, Callable]) -> None:
        """批量注册中转处理函数"""
        self._relay_handlers.update(relays)

    def register_dynamic_relay(self, source_key: str, handler: Callable) -> None:
        """注册动态中转处理函数（可多个）

        用于非卡片组件订阅信号，如状态栏订阅播放位置。
        """
        if source_key not in self._dynamic_relays:
            self._dynamic_relays[source_key] = []
        self._dynamic_relays[source_key].append(handler)

    def connect_all(self) -> None:
        """自动连接所有信号"""
        # 收集所有需要连接的信号 {source_key: [handlers]}
        signal_connections: dict[str, list[Callable]] = {}

        # 1. 添加中转处理函数
        for source_key, handler in self._relay_handlers.items():
            if source_key not in signal_connections:
                signal_connections[source_key] = []
            signal_connections[source_key].append(handler)

        # 2. 添加动态中转处理函数
        for source_key, handlers in self._dynamic_relays.items():
            if source_key not in signal_connections:
                signal_connections[source_key] = []
            signal_connections[source_key].extend(handlers)

        # 3. 添加卡片间声明式信号
        for card_id, card in self._cards.items():
            subscriptions = card.listens_to()
            for source_key, handler in subscriptions.items():
                if source_key not in signal_connections:
                    signal_connections[source_key] = []

                # 获取处理函数
                if callable(handler):
                    slot = handler
                else:
                    slot = getattr(card, handler, None)
                if slot is not None:
                    signal_connections[source_key].append(slot)

        # 4. 添加特殊组件的声明式信号
        for comp_id, comp in self._special_components.items():
            if hasattr(comp, 'listens_to'):
                subscriptions = comp.listens_to()
                for source_key, handler in subscriptions.items():
                    if source_key not in signal_connections:
                        signal_connections[source_key] = []

                    # 获取处理函数
                    if callable(handler):
                        slot = handler
                    else:
                        slot = getattr(comp, handler, None)
                    if slot is not None:
                        signal_connections[source_key].append(slot)

        # 4. 统一连接所有信号
        for source_key, handlers in signal_connections.items():
            parts = source_key.split(".", 1)
            if len(parts) != 2:
                continue
            src_id, signal_name = parts

            # 获取源组件
            source = self._cards.get(src_id)
            if source is None:
                source = self._special_components.get(src_id)
            if source is None:
                print(f"[Signal] 未知源: {src_id}")
                continue

            # 获取信号
            signal = getattr(source, signal_name, None)
            if signal is None:
                print(f"[Signal] {src_id} 没有信号 {signal_name}")
                continue

            # 连接所有处理函数
            for handler in handlers:
                try:
                    signal.connect(handler)
                except Exception as e:
                    print(f"[Signal] 连接失败: {source_key} -> {handler}: {e}")

    def get_component(self, component_id: str) -> Any | None:
        """获取组件（卡片或特殊组件）"""
        return self._cards.get(component_id) or self._special_components.get(component_id)
