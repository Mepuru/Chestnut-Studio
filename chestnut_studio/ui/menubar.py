"""菜单栏模块"""

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenuBar


class MenuBar(QMenuBar):
    """菜单栏
    
    功能：
    - 文件菜单：打开视频、导入字幕、导出字幕、退出
    - 视图菜单：卡片显示/隐藏、布局切换、全屏
    - 帮助菜单：快捷键说明
    """
    
    # 信号定义
    open_video = Signal()
    open_subtitle = Signal()
    save_subtitle = Signal()
    quit_app = Signal()
    toggle_fullscreen = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_menus()
    
    def _setup_menus(self):
        """设置菜单结构"""
        # 文件菜单
        self._create_file_menu()
        
        # 视图菜单
        self._create_view_menu()
        
        # 帮助菜单
        self._create_help_menu()
    
    def _create_file_menu(self):
        """创建文件菜单"""
        file_menu = self.addMenu("文件(&F)")
        
        # 打开视频
        open_video_action = QAction("打开视频(&O)...", self)
        open_video_action.setShortcut(QKeySequence("Ctrl+O"))
        open_video_action.triggered.connect(self.open_video.emit)
        file_menu.addAction(open_video_action)
        
        # 导入字幕
        open_subtitle_action = QAction("导入字幕(&I)...", self)
        open_subtitle_action.setShortcut(QKeySequence("Ctrl+I"))
        open_subtitle_action.triggered.connect(self.open_subtitle.emit)
        file_menu.addAction(open_subtitle_action)
        
        # 导出字幕
        save_subtitle_action = QAction("导出字幕(&S)...", self)
        save_subtitle_action.setShortcut(QKeySequence("Ctrl+S"))
        save_subtitle_action.triggered.connect(self.save_subtitle.emit)
        file_menu.addAction(save_subtitle_action)
        
        # 分隔线
        file_menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.quit_app.emit)
        file_menu.addAction(quit_action)
    
    def _create_view_menu(self):
        """创建视图菜单"""
        view_menu = self.addMenu("视图(&V)")
        
        # 卡片子菜单
        cards_menu = view_menu.addMenu("卡片(&C)")
        
        # 获取主窗口的卡片引用
        main_window = self.parent()
        if main_window:
            # 添加卡片切换动作
            if hasattr(main_window, 'player_card'):
                cards_menu.addAction(main_window.player_card.toggleViewAction())
            if hasattr(main_window, 'timeline_card'):
                cards_menu.addAction(main_window.timeline_card.toggleViewAction())
            if hasattr(main_window, 'waveform_card'):
                cards_menu.addAction(main_window.waveform_card.toggleViewAction())
            if hasattr(main_window, 'translate_card'):
                cards_menu.addAction(main_window.translate_card.toggleViewAction())
        
        # 分隔线
        view_menu.addSeparator()
        
        # 布局子菜单
        layout_menu = view_menu.addMenu("布局(&L)")
        
        # 默认布局
        default_layout_action = QAction("默认布局", self)
        default_layout_action.triggered.connect(self._reset_layout)
        layout_menu.addAction(default_layout_action)
        
        # TODO: 添加更多布局预设
        
        # 分隔线
        view_menu.addSeparator()
        
        # 全屏
        fullscreen_action = QAction("全屏(&F)", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self.toggle_fullscreen.emit)
        view_menu.addAction(fullscreen_action)
    
    def _create_help_menu(self):
        """创建帮助菜单"""
        help_menu = self.addMenu("帮助(&H)")
        
        # 快捷键说明
        hotkey_action = QAction("快捷键说明(&K)...", self)
        hotkey_action.triggered.connect(self._show_hotkey_dialog)
        help_menu.addAction(hotkey_action)
    
    def _reset_layout(self):
        """重置为默认布局"""
        # TODO: 实现布局重置
        pass
    
    def _show_hotkey_dialog(self):
        """显示快捷键说明对话框"""
        # TODO: 实现快捷键说明对话框
        pass
