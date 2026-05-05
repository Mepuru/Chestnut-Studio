"""翻译面板卡片模块"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel, QFrame


class TranslateCard(QDockWidget):
    """翻译面板卡片
    
    功能：
    - 显示当前选中的原始字幕
    - 翻译文本输入
    - 保存翻译到指定轨道
    
    TODO: Phase 4 实现完整功能
    """
    
    # 默认停靠区域
    default_area = Qt.BottomDockWidgetArea
    
    def __init__(self, parent=None):
        super().__init__("翻译", parent)
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
        hint = QLabel("选中字幕后可在此输入翻译")
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
