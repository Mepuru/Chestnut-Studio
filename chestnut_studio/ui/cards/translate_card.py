"""翻译面板卡片模块

功能：
- 显示当前选中的字幕时间点和轨道
- 提供文本输入框编辑当前轨道的字幕文本
- 支持快速跳转：Ctrl+Enter 保存后自动跳转到下一条
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.track_config import get_track_color
from chestnut_studio.utils.time_utils import ms_to_time_str

# 按钮样式
BTN_STYLE = """
    QPushButton {
        background: #27272a;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        font-size: 9pt;
        padding: 4px 16px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background: #3f3f46;
    }
    QPushButton:pressed {
        background: #18181b;
    }
    QPushButton:disabled {
        color: #52525b;
        background: #1e1e22;
    }
"""

# 保存按钮样式（蓝色高亮）
SAVE_BTN_STYLE = """
    QPushButton {
        background: #2563eb;
        border: 1px solid #3b82f6;
        color: #ffffff;
        font-size: 9pt;
        padding: 4px 16px;
        border-radius: 3px;
        font-weight: bold;
    }
    QPushButton:hover {
        background: #3b82f6;
    }
    QPushButton:pressed {
        background: #1d4ed8;
    }
    QPushButton:disabled {
        color: #93c5fd;
        background: #1e3a5f;
    }
"""

# 输入框样式
TEXT_EDIT_STYLE = """
    QTextEdit {
        background: #18181b;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        font-size: 11pt;
        padding: 8px;
        border-radius: 4px;
    }
    QTextEdit:focus {
        border-color: #3b82f6;
    }
"""


class TranslateCard(QDockWidget):
    """翻译面板卡片

    功能：
    - 显示当前选中的字幕时间点和轨道
    - 提供文本输入框编辑当前轨道的字幕文本
    - 支持快速跳转：Ctrl+Enter 保存后自动跳转到下一条

    信号：
    - text_saved(col, start_ms, text): 文本保存时发射
    - jump_to_next(col, start_ms): 请求跳转到下一条
    - jump_to_prev(col, start_ms): 请求跳转到上一条
    """

    # 信号
    text_saved = Signal(int, int, str)  # (col, start_ms, text)
    jump_to_next = Signal(int, int)  # (col, start_ms)
    jump_to_prev = Signal(int, int)  # (col, start_ms)
    editing_subtitle = Signal(int, int)  # (col, start_ms) 正在编辑的字幕

    # 默认停靠区域
    default_area = Qt.BottomDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("翻译", parent)
        self._current_col = -1  # 当前字幕轨道号
        self._current_start_ms = -1  # 当前字幕开始时间
        self._subtitle_data = None  # 字幕数据引用（从外部设置）
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
        inner_layout.setContentsMargins(16, 12, 16, 12)
        inner_layout.setSpacing(8)

        # --- 顶部信息栏 ---
        info_bar = QWidget()
        info_bar.setStyleSheet("background: transparent; border: none;")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # 时间点显示
        self._time_label = QLabel("未选中字幕")
        self._time_label.setStyleSheet("""
            QLabel {
                color: #a1a1aa;
                font-size: 10pt;
                font-family: Consolas;
                background: transparent;
                border: none;
            }
        """)

        # 轨道显示
        self._track_label = QLabel("")
        self._track_label.setStyleSheet("""
            QLabel {
                color: #a1a1aa;
                font-size: 10pt;
                background: transparent;
                border: none;
            }
        """)

        # 快捷键提示
        self._hotkey_hint = QLabel("Ctrl+Enter: 保存/下一条  Shift+Enter: 上一条")
        self._hotkey_hint.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 8pt;
                background: transparent;
                border: none;
            }
        """)

        info_layout.addWidget(self._time_label)
        info_layout.addSpacing(16)
        info_layout.addWidget(self._track_label)
        info_layout.addStretch()
        info_layout.addWidget(self._hotkey_hint)

        inner_layout.addWidget(info_bar)

        # --- 文本输入区域 ---
        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        self._text_edit = QTextEdit()
        self._text_edit.setStyleSheet(TEXT_EDIT_STYLE)
        self._text_edit.setPlaceholderText("请输入字幕文本...")
        self._text_edit.setMinimumHeight(80)
        self._text_edit.setMaximumHeight(200)

        text_layout.addWidget(self._text_edit)

        inner_layout.addWidget(text_container)

        # --- 底部按钮栏 ---
        button_bar = QWidget()
        button_bar.setStyleSheet("background: transparent; border: none;")
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(0, 4, 0, 0)
        button_layout.setSpacing(8)

        # 清空按钮
        self._clear_btn = QPushButton("清空")
        self._clear_btn.setStyleSheet(BTN_STYLE)
        self._clear_btn.setToolTip("清空输入框")
        self._clear_btn.clicked.connect(self.clear_input)
        self._clear_btn.setEnabled(False)

        # 上一条按钮
        self._prev_btn = QPushButton("上一条")
        self._prev_btn.setStyleSheet(BTN_STYLE)
        self._prev_btn.setToolTip("跳转到上一条字幕 (Shift+Enter)")
        self._prev_btn.clicked.connect(self._on_prev_clicked)
        self._prev_btn.setEnabled(False)

        # 保存/下一条按钮
        self._save_next_btn = QPushButton("保存/下一条")
        self._save_next_btn.setStyleSheet(SAVE_BTN_STYLE)
        self._save_next_btn.setToolTip("保存并跳转到下一条 (Ctrl+Enter)")
        self._save_next_btn.clicked.connect(self._on_save_next_clicked)
        self._save_next_btn.setEnabled(False)

        button_layout.addStretch()
        button_layout.addWidget(self._clear_btn)
        button_layout.addWidget(self._prev_btn)
        button_layout.addWidget(self._save_next_btn)

        inner_layout.addWidget(button_bar)

        layout.addWidget(inner)
        self.setWidget(content)

    def set_subtitle_data(self, subtitle_data: dict):
        """设置字幕数据引用（从外部传入）

        Args:
            subtitle_data: SubtitleManager.data 的引用
        """
        self._subtitle_data = subtitle_data

    def show_subtitle(self, col: int, start_ms: int):
        """显示选中的字幕

        Args:
            col: 字幕轨道号 (1-4)
            start_ms: 字幕开始时间 (ms)
        """
        self._current_col = col
        self._current_start_ms = start_ms

        # 更新时间显示
        self._time_label.setText(f"{ms_to_time_str(start_ms)}")

        # 更新轨道显示
        color = get_track_color(col)
        self._track_label.setText(f"轨道 {col}")
        self._track_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 10pt;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)

        # 加载已有的文本
        self._load_existing_text(col, start_ms)

        # 启用按钮
        self._clear_btn.setEnabled(True)
        self._prev_btn.setEnabled(True)
        self._save_next_btn.setEnabled(True)

        # 发射正在编辑信号（用于高亮时间轴对应行）
        self.editing_subtitle.emit(col, start_ms)

        # 文本输入框获焦
        self._text_edit.setFocus()

    def _load_existing_text(self, col: int, start_ms: int):
        """加载已有的字幕文本

        Args:
            col: 字幕轨道号
            start_ms: 字幕开始时间
        """
        if self._subtitle_data is None:
            self._text_edit.clear()
            return

        # 从字幕数据中获取文本
        sub_data = self._subtitle_data.get(col, {})
        subtitle = sub_data.get(start_ms)

        if subtitle and len(subtitle) >= 2:
            text = subtitle[1]
            self._text_edit.setPlainText(text)
        else:
            self._text_edit.clear()

    def save_text(self):
        """保存当前文本"""
        if self._current_col < 0 or self._current_start_ms < 0:
            return

        text = self._text_edit.toPlainText().strip()
        self.text_saved.emit(self._current_col, self._current_start_ms, text)

    def _on_save_next_clicked(self):
        """保存并跳转到下一条"""
        self.save_text()
        if self._current_col >= 0 and self._current_start_ms >= 0:
            self.jump_to_next.emit(self._current_col, self._current_start_ms)

    def _on_prev_clicked(self):
        """跳转到上一条"""
        if self._current_col >= 0 and self._current_start_ms >= 0:
            self.jump_to_prev.emit(self._current_col, self._current_start_ms)

    def clear_input(self):
        """清空输入"""
        self._text_edit.clear()

    def keyPressEvent(self, event):
        """处理快捷键"""
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+Enter: 保存并跳转下一条
        if key in (Qt.Key_Return, Qt.Key_Enter) and modifiers == Qt.ControlModifier:
            self._on_save_next_clicked()
            event.accept()
            return

        # Shift+Enter: 跳转上一条
        if key in (Qt.Key_Return, Qt.Key_Enter) and modifiers == Qt.ShiftModifier:
            self._on_prev_clicked()
            event.accept()
            return

        super().keyPressEvent(event)
