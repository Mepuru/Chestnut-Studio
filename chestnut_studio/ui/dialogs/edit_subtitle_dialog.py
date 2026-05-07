"""编辑字幕对话框模块

功能：
- 调整字幕的开始时间和结束时间
- 支持 ±100ms 微调
- 显示持续时间
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from chestnut_studio.utils.time_utils import ms_to_time_str

# 微调按钮样式
ADJ_BTN_STYLE = """
    QPushButton {
        background: #27272a;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        font-size: 9pt;
        padding: 2px 8px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background: #3f3f46;
    }
    QPushButton:pressed {
        background: #18181b;
    }
"""


class EditSubtitleDialog(QDialog):
    """编辑字幕对话框

    Args:
        start_ms: 当前开始时间 (ms)
        end_ms: 当前结束时间 (ms)
        duration_ms: 视频总时长 (ms)
        parent: 父组件
    """

    def __init__(self, start_ms: int, end_ms: int, duration_ms: int, parent=None):
        super().__init__(parent)
        self._start_ms = start_ms
        self._end_ms = end_ms
        self._duration_ms = duration_ms
        self._step_ms = 100  # 微调步长

        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        """初始化 UI"""
        self.setWindowTitle("编辑字幕")
        self.setMinimumWidth(360)
        self.setStyleSheet("""
            QDialog {
                background: #1e1e22;
                color: #e4e4e7;
            }
            QLabel {
                color: #e4e4e7;
                font-size: 10pt;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("编辑字幕区间")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e4e4e7;")
        layout.addWidget(title)

        # 时间编辑区
        grid = QGridLayout()
        grid.setSpacing(8)

        # 开始时间行
        start_label = QLabel("开始时间:")
        start_label.setStyleSheet("color: #a1a1aa;")
        grid.addWidget(start_label, 0, 0)

        self._start_time_label = QLabel()
        self._start_time_label.setStyleSheet("font-family: Consolas; font-size: 11pt; color: #22c55e; min-width: 80px;")
        self._start_time_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(self._start_time_label, 0, 1)

        start_back_btn = QPushButton("← 100ms")
        start_back_btn.setStyleSheet(ADJ_BTN_STYLE)
        start_back_btn.clicked.connect(lambda: self._adjust_start(-self._step_ms))
        grid.addWidget(start_back_btn, 0, 2)

        start_fwd_btn = QPushButton("100ms →")
        start_fwd_btn.setStyleSheet(ADJ_BTN_STYLE)
        start_fwd_btn.clicked.connect(lambda: self._adjust_start(self._step_ms))
        grid.addWidget(start_fwd_btn, 0, 3)

        # 结束时间行
        end_label = QLabel("结束时间:")
        end_label.setStyleSheet("color: #a1a1aa;")
        grid.addWidget(end_label, 1, 0)

        self._end_time_label = QLabel()
        self._end_time_label.setStyleSheet("font-family: Consolas; font-size: 11pt; color: #f59e0b; min-width: 80px;")
        self._end_time_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(self._end_time_label, 1, 1)

        end_back_btn = QPushButton("← 100ms")
        end_back_btn.setStyleSheet(ADJ_BTN_STYLE)
        end_back_btn.clicked.connect(lambda: self._adjust_end(-self._step_ms))
        grid.addWidget(end_back_btn, 1, 2)

        end_fwd_btn = QPushButton("100ms →")
        end_fwd_btn.setStyleSheet(ADJ_BTN_STYLE)
        end_fwd_btn.clicked.connect(lambda: self._adjust_end(self._step_ms))
        grid.addWidget(end_fwd_btn, 1, 3)

        layout.addLayout(grid)

        # 时长显示
        self._duration_label = QLabel()
        self._duration_label.setStyleSheet("font-family: Consolas; font-size: 10pt; color: #a1a1aa;")
        self._duration_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._duration_label)

        # 分隔线
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: #3f3f46;")
        layout.addWidget(separator)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setStyleSheet("""
            QPushButton {
                background: #27272a;
                border: 1px solid #3f3f46;
                color: #e4e4e7;
                font-size: 10pt;
                padding: 6px 20px;
                border-radius: 4px;
                min-width: 60px;
            }
            QPushButton:hover {
                background: #3f3f46;
            }
            QPushButton:pressed {
                background: #18181b;
            }
        """)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _update_display(self):
        """更新时间显示"""
        self._start_time_label.setText(ms_to_time_str(self._start_ms))
        self._end_time_label.setText(ms_to_time_str(self._end_ms))
        duration = self._end_ms - self._start_ms
        self._duration_label.setText(f"时长: {duration / 1000:.2f}s")

    def _adjust_start(self, delta_ms: int):
        """调整开始时间"""
        new_start = self._start_ms + delta_ms
        # 不能小于 0，不能大于等于结束时间
        new_start = max(0, min(new_start, self._end_ms - 10))
        self._start_ms = new_start
        self._update_display()

    def _adjust_end(self, delta_ms: int):
        """调整结束时间"""
        new_end = self._end_ms + delta_ms
        # 不能小于等于开始时间，不能超过视频时长
        new_end = max(self._start_ms + 10, min(new_end, self._duration_ms))
        self._end_ms = new_end
        self._update_display()

    def get_result(self) -> tuple[int, int]:
        """获取编辑结果

        Returns:
            (start_ms, end_ms)
        """
        return self._start_ms, self._end_ms
