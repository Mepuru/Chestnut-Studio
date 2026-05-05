"""音频波形卡片模块"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QLabel, QVBoxLayout, QWidget


class WaveformCard(QDockWidget):
    """音频波形卡片

    功能：
    - 主音轨波形显示
    - 红色时间线跟随播放
    - 字幕条覆盖显示
    - 点击跳转

    TODO: Phase 2 实现完整功能
    """

    # 默认停靠区域
    default_area = Qt.BottomDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("波形图", parent)
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
        inner_layout.setContentsMargins(24, 16, 24, 16)

        # 占位提示
        hint = QLabel("打开视频后显示音轨波形")
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
