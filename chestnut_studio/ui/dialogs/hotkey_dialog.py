"""快捷键说明对话框"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


# 对话框样式
DIALOG_STYLE = """
    QDialog {
        background: #0f0f14;
        color: #e4e4e7;
    }
"""

# 标题样式
TITLE_STYLE = """
    QLabel {
        color: #e4e4e7;
        font-size: 11pt;
        font-weight: bold;
        padding: 8px 0 4px 0;
    }
"""

# 快捷键表格样式
TABLE_STYLE = """
    QLabel {
        color: #a1a1aa;
        font-size: 9pt;
        padding: 2px 0;
    }
"""

# 快捷键按键样式
KEY_STYLE = """
    QLabel {
        background: #27272a;
        border: 1px solid #3f3f46;
        border-radius: 3px;
        color: #e4e4e7;
        font-size: 9pt;
        font-family: Consolas, monospace;
        padding: 2px 6px;
        min-width: 20px;
    }
"""

# 关闭按钮样式
CLOSE_BTN_STYLE = """
    QPushButton {
        background: #27272a;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        font-size: 9pt;
        padding: 6px 24px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background: #3f3f46;
    }
    QPushButton:pressed {
        background: #18181b;
    }
"""


class HotkeyDialog(QDialog):
    """快捷键说明对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("快捷键说明")
        self.setMinimumSize(500, 450)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title = QLabel("快捷键说明")
        title.setStyleSheet("""
            QLabel {
                color: #fafafa;
                font-size: 14pt;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 标签页
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background: #0f0f14;
                border: 1px solid #27272a;
            }
            QTabBar::tab {
                background: #18181b;
                color: #a1a1aa;
                border: 1px solid #27272a;
                padding: 6px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #0f0f14;
                color: #fafafa;
                border-bottom-color: #0f0f14;
            }
            QTabBar::tab:hover {
                background: #27272a;
            }
        """)

        # 添加标签页
        tab_widget.addTab(self._create_global_tab(), "全局")
        tab_widget.addTab(self._create_waveform_tab(), "波形图")
        tab_widget.addTab(self._create_timeline_tab(), "时间轴")
        tab_widget.addTab(self._create_translate_tab(), "翻译")

        layout.addWidget(tab_widget)

        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(CLOSE_BTN_STYLE)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _create_hotkey_row(self, key: str, description: str) -> QWidget:
        """创建快捷键行"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        # 快捷键标签
        key_label = QLabel(key)
        key_label.setStyleSheet(KEY_STYLE)
        key_label.setFixedWidth(100)
        key_label.setAlignment(Qt.AlignCenter)

        # 说明标签
        desc_label = QLabel(description)
        desc_label.setStyleSheet(TABLE_STYLE)

        layout.addWidget(key_label)
        layout.addWidget(desc_label)
        layout.addStretch()

        return widget

    def _create_section_title(self, title: str) -> QLabel:
        """创建分组标题"""
        label = QLabel(title)
        label.setStyleSheet(TITLE_STYLE)
        return label

    def _create_global_tab(self) -> QWidget:
        """创建全局快捷键标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #18181b;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #3f3f46;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #52525b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # 内容容器
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(4)

        # 播放控制
        content_layout.addWidget(self._create_section_title("播放控制"))
        content_layout.addWidget(self._create_hotkey_row("Space", "播放 / 暂停"))

        content_layout.addSpacing(8)

        # AB 循环
        content_layout.addWidget(self._create_section_title("AB 循环"))
        content_layout.addWidget(self._create_hotkey_row("[", "设置 A 点（循环起点）"))
        content_layout.addWidget(self._create_hotkey_row("]", "设置 B 点（循环终点）"))
        content_layout.addWidget(self._create_hotkey_row("\\", "清除 AB 循环"))

        content_layout.addSpacing(8)

        # 打轴
        content_layout.addWidget(self._create_section_title("打轴"))
        content_layout.addWidget(self._create_hotkey_row("I", "标记字幕开始点"))
        content_layout.addWidget(self._create_hotkey_row("O", "标记字幕结束点"))

        content_layout.addSpacing(8)

        # 轨道切换
        content_layout.addWidget(self._create_section_title("轨道切换"))
        content_layout.addWidget(self._create_hotkey_row("1 / 2 / 3 / 4", "快速切换到对应轨道"))

        content_layout.addSpacing(8)

        # 编辑模式
        content_layout.addWidget(self._create_section_title("编辑模式"))
        content_layout.addWidget(self._create_hotkey_row("Enter", "确认编辑"))
        content_layout.addWidget(self._create_hotkey_row("Escape", "取消编辑"))

        content_layout.addSpacing(8)

        # 文件操作
        content_layout.addWidget(self._create_section_title("文件操作"))
        content_layout.addWidget(self._create_hotkey_row("Ctrl+O", "打开视频文件"))
        content_layout.addWidget(self._create_hotkey_row("Ctrl+I", "导入字幕文件"))
        content_layout.addWidget(self._create_hotkey_row("Ctrl+S", "导出字幕文件"))
        content_layout.addWidget(self._create_hotkey_row("Ctrl+Q", "退出应用"))
        content_layout.addWidget(self._create_hotkey_row("F11", "切换全屏"))

        content_layout.addStretch()

        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)

        return widget

    def _create_waveform_tab(self) -> QWidget:
        """创建波形图快捷键标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        # 鼠标操作
        layout.addWidget(self._create_section_title("鼠标操作"))
        layout.addWidget(self._create_hotkey_row("左键点击", "跳转到点击位置"))
        layout.addWidget(self._create_hotkey_row("Shift+左键拖动", "平移视窗"))
        layout.addWidget(self._create_hotkey_row("滚轮", "缩放视窗（以鼠标位置为中心）"))

        layout.addSpacing(8)

        # 打轴操作
        layout.addWidget(self._create_section_title("打轴操作"))
        layout.addWidget(self._create_hotkey_row("I", "标记字幕开始点"))
        layout.addWidget(self._create_hotkey_row("O", "标记字幕结束点"))

        layout.addSpacing(8)

        # 编辑模式操作
        layout.addWidget(self._create_section_title("编辑模式"))
        layout.addWidget(self._create_hotkey_row("I", "设为起点"))
        layout.addWidget(self._create_hotkey_row("O", "设为终点"))
        layout.addWidget(self._create_hotkey_row("Enter", "确认编辑"))
        layout.addWidget(self._create_hotkey_row("Escape", "取消编辑"))

        layout.addStretch()
        return widget

    def _create_timeline_tab(self) -> QWidget:
        """创建时间轴快捷键标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        # 列表操作
        layout.addWidget(self._create_section_title("列表操作"))
        layout.addWidget(self._create_hotkey_row("双击行", "跳转到字幕起始点"))

        layout.addSpacing(8)

        # 编辑操作
        layout.addWidget(self._create_section_title("编辑操作"))
        layout.addWidget(self._create_hotkey_row("Ctrl+Z", "撤销"))
        layout.addWidget(self._create_hotkey_row("Ctrl+Y", "重做"))
        layout.addWidget(self._create_hotkey_row("Delete", "删除选中字幕"))

        layout.addStretch()
        return widget

    def _create_translate_tab(self) -> QWidget:
        """创建翻译面板快捷键标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        # 导航操作
        layout.addWidget(self._create_section_title("导航操作"))
        layout.addWidget(self._create_hotkey_row("Ctrl+Enter", "保存并跳转到下一条字幕"))
        layout.addWidget(self._create_hotkey_row("Shift+Enter", "跳转到上一条字幕"))
        layout.addWidget(self._create_hotkey_row("Enter", "换行（文本框内）"))

        layout.addStretch()
        return widget
