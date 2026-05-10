"""布局引擎模块

根据 LayoutConfig 将卡片应用到 MainWindow 的布局。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

if TYPE_CHECKING:
    from chestnut_studio.ui.cards.base_card import BaseCard
    from chestnut_studio.ui.layout_config import LayoutConfig


def apply_layout(
    window: QMainWindow,
    config: LayoutConfig,
    cards: dict[str, BaseCard],
) -> None:
    """将布局配置应用到 MainWindow。

    Args:
        window: 主窗口实例
        config: 布局配置
        cards: card_id -> BaseCard 实例映射
    """
    # 1. 移除所有现有卡片
    for card in cards.values():
        window.removeDockWidget(card)

    # 2. 按列布局
    first_in_row: list[BaseCard | None] = []
    for col_idx, col_config in enumerate(config.columns):
        first_in_row.append(None)

        for row_idx, row_config in enumerate(col_config.rows):
            card = cards.get(row_config.card)
            if card is None:
                continue

            area = Qt.LeftDockWidgetArea if col_idx == 0 else Qt.RightDockWidgetArea

            if row_idx == 0:
                # 列的第一行：直接添加到区域
                window.addDockWidget(area, card)
                first_in_row[col_idx] = card
            else:
                # 后续行：与列首垂直分割
                if first_in_row[col_idx] is not None:
                    window.splitDockWidget(first_in_row[col_idx], card, Qt.Vertical)

    # 3. 确保所有卡片可见
    for card in cards.values():
        card.setVisible(True)

    # 4. 应用尺寸比例
    _apply_sizes(window, config, cards)


def _apply_sizes(
    window: QMainWindow,
    config: LayoutConfig,
    cards: dict[str, BaseCard],
) -> None:
    """按配置比例调整各卡片尺寸。"""
    win_w = window.width()
    win_h = window.height() - 45  # 减去工具栏/菜单栏

    # 水平比例
    h_docks = []
    h_sizes = []
    for col_config in config.columns:
        for row_config in col_config.rows:
            card = cards.get(row_config.card)
            if card:
                h_docks.append(card)
                h_sizes.append(int(win_w * col_config.width_ratio))

    if h_docks:
        window.resizeDocks(h_docks, h_sizes, Qt.Horizontal)

    # 垂直比例
    v_docks = []
    v_sizes = []
    for col_config in config.columns:
        col_h = int(win_h)  # 整列高度
        for row_config in col_config.rows:
            card = cards.get(row_config.card)
            if card:
                v_docks.append(card)
                v_sizes.append(int(col_h * row_config.height_ratio))

    if v_docks:
        window.resizeDocks(v_docks, v_sizes, Qt.Vertical)


def save_current_layout(
    window: QMainWindow,
    cards: dict[str, BaseCard],
    name: str = "自定义布局",
) -> dict:
    """将当前窗口布局导出为配置字典。

    通过查询各卡片的 dockWidgetArea 和相对尺寸生成配置。

    Args:
        window: 主窗口实例
        cards: card_id -> BaseCard 实例映射
        name: 布局名称

    Returns:
        布局配置字典
    """
    config = {"name": name, "version": 1, "columns": []}

    # 按区域分组
    left_cards = []
    right_cards = []
    for card_id, card in cards.items():
        area = window.dockWidgetArea(card)
        if area == Qt.LeftDockWidgetArea:
            left_cards.append(card_id)
        elif area == Qt.RightDockWidgetArea:
            right_cards.append(card_id)

    # 生成列配置
    if left_cards:
        config["columns"].append({
            "width_ratio": 0.39,
            "rows": [{"card": cid, "height_ratio": 1.0 / len(left_cards)} for cid in left_cards],
        })
    if right_cards:
        config["columns"].append({
            "width_ratio": 0.61,
            "rows": [{"card": cid, "height_ratio": 1.0 / len(right_cards)} for cid in right_cards],
        })

    return config
