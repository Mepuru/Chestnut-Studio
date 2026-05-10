"""卡片注册表模块

提供卡片自动发现与注册功能，消除 MainWindow 对具体卡片类的硬编码依赖。

使用方式：
    from chestnut_studio.ui.cards.registry import register_card

    @register_card
    class MyCard(BaseCard):
        card_id = "my_card"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chestnut_studio.ui.cards.base_card import BaseCard

_CARD_REGISTRY: dict[str, type[BaseCard]] = {}


def register_card(cls: type[BaseCard]) -> type[BaseCard]:
    """类装饰器：将卡片类注册到全局注册表。

    用法：
        @register_card
        class MyCard(BaseCard):
            card_id = "my_card"

    Args:
        cls: 要注册的卡片类，必须声明 card_id 类属性

    Returns:
        原始类（不修改）

    Raises:
        ValueError: 如果 card_id 未声明或已被注册
    """
    card_id = getattr(cls, "card_id", None)
    if not card_id:
        raise ValueError(f"{cls.__name__} 必须声明 card_id 类属性")
    if card_id in _CARD_REGISTRY:
        raise ValueError(f"card_id '{card_id}' 已被 {_CARD_REGISTRY[card_id].__name__} 注册")
    _CARD_REGISTRY[card_id] = cls
    return cls


def get_registry() -> dict[str, type[BaseCard]]:
    """返回注册表的只读副本。

    Returns:
        card_id -> 卡片类 的字典副本
    """
    return _CARD_REGISTRY.copy()


def get_ordered_cards() -> list[tuple[str, type[BaseCard]]]:
    """按 order 属性排序返回注册表。

    Returns:
        (card_id, 卡片类) 的列表，按 order 属性升序排列
    """
    return sorted(
        _CARD_REGISTRY.items(),
        key=lambda item: getattr(item[1], "order", 999),
    )


def get_card_class(card_id: str) -> type[BaseCard] | None:
    """根据 card_id 获取卡片类。

    Args:
        card_id: 卡片的唯一标识符

    Returns:
        卡片类，如果未注册则返回 None
    """
    return _CARD_REGISTRY.get(card_id)


def create_card(card_id: str, parent=None) -> BaseCard | None:
    """根据 card_id 创建卡片实例。

    Args:
        card_id: 卡片的唯一标识符
        parent: 父组件

    Returns:
        卡片实例，如果未注册则返回 None
    """
    cls = _CARD_REGISTRY.get(card_id)
    if cls is None:
        return None
    return cls(parent)
