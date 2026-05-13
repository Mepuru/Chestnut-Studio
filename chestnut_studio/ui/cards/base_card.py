"""BaseCard 基类模块

所有卡片组件的统一基类，提供：
- 标准化初始化流程
- 生命周期钩子
- 状态持久化接口
- 声明式属性（card_id, card_title, default_area 等）
- 声明式信号订阅（listens_to + @subscribe 装饰器）
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QDockWidget, QWidget


def _make_close_icon(color: str, size: int = 16) -> QIcon:
    """生成一个简洁的 X 形关闭图标"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    m = 3.5
    painter.drawLine(int(m), int(m), int(size - m), int(size - m))
    painter.drawLine(int(size - m), int(m), int(m), int(size - m))
    painter.end()
    return QIcon(pixmap)


class BaseCard(QDockWidget):
    """所有卡片组件的基类

    子类必须声明：
        card_id: str - 唯一标识符，用于注册表查找和布局配置
        card_title: str - 卡片标题，显示在标题栏

    子类可选声明：
        default_area: Qt.DockWidgetArea - 默认停靠区域
        default_ratio: float - 在所属区域内的默认占比 (0.0 ~ 1.0)
        min_size: tuple[int, int] - 最小尺寸 (width, height)
        features: QDockWidget.DockWidgetFeatures - DockWidget 特性标志

    子类应实现：
        _setup_ui() - 初始化 UI 布局
        _connect_internal_signals() - 连接卡片内部信号
        on_init() - 自定义初始化（替代重写 __init__）
        on_ready() - 所有卡片就绪后的回调
        on_save_state() - 返回需要持久化的状态字典
        on_load_state() - 从字典恢复状态
    """

    # ── 子类必须声明 ──
    card_id: str = ""
    """唯一标识符，用于注册表查找和布局配置。"""

    card_title: str = ""
    """卡片标题，显示在标题栏。支持 i18n key。"""

    # ── 子类可选声明 ──
    default_area: Qt.DockWidgetArea = Qt.LeftDockWidgetArea
    """默认停靠区域。"""

    default_ratio: float = 0.5
    """在所属区域内的默认占比 (0.0 ~ 1.0)。"""

    min_size: tuple[int, int] = (200, 150)
    """最小尺寸 (width, height)。"""

    features: QDockWidget.DockWidgetFeatures = (
        QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
    )
    """DockWidget 特性标志。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(self.card_title, parent)

        # 应用标准属性
        self.setObjectName(self.card_id)
        self.setFeatures(self.features)
        self.setMinimumSize(*self.min_size)

        # 设置标题栏按钮图标（延迟到按钮创建后）
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_title_bar_icons)

        # 子类初始化
        self._setup_ui()
        self._connect_internal_signals()

        # 生命周期钩子
        self.on_init()

    def _setup_ui(self) -> None:
        """初始化 UI 布局。子类必须实现此方法。"""
        pass

    def _connect_internal_signals(self) -> None:
        """连接卡片内部信号。子类可重写此方法。"""
        pass

    def _setup_title_bar_icons(self) -> None:
        """设置标题栏按钮的自定义图标，替换系统默认图标。"""
        close_btn = self.findChild(QWidget, "qt_dockwidget_closebutton")
        if close_btn:
            close_btn.setIcon(_make_close_icon("#a1a1aa"))
        float_btn = self.findChild(QWidget, "qt_dockwidget_floatbutton")
        if float_btn:
            float_btn.setIcon(_make_close_icon("#a1a1aa"))

    # ── 生命周期钩子 ──

    def on_init(self) -> None:
        """子类自定义初始化，替代重写 __init__。"""
        pass

    def on_ready(self) -> None:
        """所有卡片就绪后的回调，可安全引用其他卡片。"""
        pass

    def on_save_state(self) -> dict[str, Any]:
        """返回需要持久化的状态字典。默认返回空字典。

        Returns:
            dict: JSON 可序列化的状态字典
        """
        return {}

    def on_load_state(self, data: dict[str, Any]) -> None:
        """从字典恢复状态。默认空实现。

        Args:
            data: 之前保存的状态字典
        """
        pass

    def on_theme_changed(self) -> None:
        """主题切换时的回调。默认空实现。"""
        pass

    # ── 声明式信号订阅 ──

    def listens_to(self) -> dict[str, str | Callable]:
        """声明本卡片关心的外部信号。

        支持两种方式：
        1. 手动声明（重写此方法）
        2. 使用 @subscribe 装饰器（自动收集）

        两种方式可以混合使用，装饰器声明会自动合并。

        返回格式:
            {
                "<source_card_id>.<signal_name>": "<handler_method_name>",
                # 或
                "<source_card_id>.<signal_name>": self._handler_method,
            }

        示例:
            # 方式 1：手动声明
            def listens_to(self):
                return {
                    "player.position_changed": "update_position",
                }

            # 方式 2：装饰器声明
            @subscribe("player.position_changed")
            def update_position(self, ms): ...

        Returns:
            信号订阅声明字典
        """
        # 收集 @subscribe 装饰器声明
        from chestnut_studio.ui.signal_decorator import collect_subscriptions
        subscriptions = collect_subscriptions(self)

        # 允许子类通过重写 listens_to 添加更多订阅
        # 这里返回装饰器收集的结果
        return subscriptions
