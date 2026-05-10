"""菜单自动生成模块

基于卡片注册表自动构建"视图"菜单，新增卡片零维护成本。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenu

if TYPE_CHECKING:
    from collections.abc import Callable

    from chestnut_studio.ui.cards.base_card import BaseCard
    from chestnut_studio.ui.layout_config import LayoutConfig


def build_card_submenu(
    parent,
    cards: dict[str, BaseCard],
    on_toggle_card: Callable[[str, bool], None],
) -> QMenu:
    """自动构建"显示/隐藏卡片"子菜单。

    Args:
        parent: 菜单父对象
        cards: card_id -> BaseCard 实例
        on_toggle_card: (card_id: str, visible: bool) -> None

    Returns:
        构建好的 QMenu
    """
    menu = QMenu("卡片(&C)", parent)

    for card_id, card in cards.items():
        action = card.toggleViewAction()
        menu.addAction(action)

    return menu


def build_layout_submenu(
    parent,
    layouts: dict[str, LayoutConfig],
    on_apply_layout: Callable[[str], None],
    on_reset_layout: Callable[[], None],
) -> QMenu:
    """自动构建"布局"子菜单。

    Args:
        parent: 菜单父对象
        layouts: layout_name -> LayoutConfig
        on_apply_layout: (layout_name: str) -> None
        on_reset_layout: () -> None

    Returns:
        构建好的 QMenu
    """
    menu = QMenu("布局(&L)", parent)

    # 默认布局
    default_action = QAction("默认布局", parent)
    default_action.triggered.connect(on_reset_layout)
    menu.addAction(default_action)

    # 其他布局
    if layouts:
        menu.addSeparator()
        layout_group = QActionGroup(parent)
        layout_group.setExclusive(True)

        for name, config in layouts.items():
            if name == "default":
                continue  # 跳过默认布局，已经添加过了
            action = QAction(config.name or name, parent, checkable=True)
            action.setActionGroup(layout_group)
            action.triggered.connect(lambda checked, n=name: on_apply_layout(n))
            menu.addAction(action)

    return menu
