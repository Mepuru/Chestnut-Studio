"""打轴编辑卡片模块"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QLabel, QVBoxLayout, QWidget


class TimelineCard(QDockWidget):
    """打轴编辑卡片

    功能：
    - 101行×5列动态表格
    - 轨道切换 + 间隔设置
    - 完整的快捷键支持
    - 右键上下文菜单
    - 双击编辑字幕文本

    TODO: Phase 3 实现完整功能
    """

    # 默认停靠区域
    default_area = Qt.RightDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("时间轴", parent)
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI"""
        content = QWidget()
        content.setStyleSheet("""
            QWidget {
                background: #0f0f14;
                border: 1px solid #27272a;
                border-top: none;
            }
        """)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        # 内部容器
        inner = QWidget()
        inner.setStyleSheet("background: transparent; border: none;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(24, 24, 24, 24)

        # 占位提示
        hint = QLabel("打开视频后可开始打轴")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("""
            QLabel {
                color: #52525b;
                font-size: 10pt;
                background: transparent;
                border: none;
            }
        """)
        inner_layout.addWidget(hint)

        layout.addWidget(inner)
        self.setWidget(content)
