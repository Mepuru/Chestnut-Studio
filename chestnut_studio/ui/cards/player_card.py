"""视频播放卡片模块"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QLabel, QVBoxLayout, QWidget


class PlayerCard(QDockWidget):
    """视频播放卡片

    功能：
    - 视频渲染 + 字幕叠加预览
    - 播放控制（播放/暂停/停止/音量/倍速）
    - 进度条拖拽 + 时间显示
    - 滚轮缩放 + 拖放打开

    TODO: Phase 1 实现完整功能
    """

    # 默认停靠区域
    default_area = Qt.LeftDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("视频预览", parent)
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
        hint = QLabel("拖入视频文件或使用菜单打开")
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
