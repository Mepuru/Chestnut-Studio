"""菜单栏模块"""

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar


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
    reset_layout = Signal()  # 重置为默认布局
    dump_layout = Signal()  # 打印当前布局信息
    toggle_debug_console = Signal()  # 切换调试控制台

    def __init__(self, parent=None):
        super().__init__(parent)
        self._card_submenu = None
        self._layout_submenu = None
        self._setup_menus()

    def set_card_submenu(self, submenu: QMenu):
        """设置自动生成的卡片子菜单"""
        self._card_submenu = submenu
        # 重新构建视图菜单
        self._rebuild_view_menu()

    def set_layout_submenu(self, submenu: QMenu):
        """设置自动生成的布局子菜单"""
        self._layout_submenu = submenu
        # 重新构建视图菜单
        self._rebuild_view_menu()

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
        self._view_menu = self.addMenu("视图(&V)")

        # 卡片子菜单（使用自动生成的或手动创建的）
        if self._card_submenu:
            self._view_menu.addMenu(self._card_submenu)
        else:
            # 备用：手动创建卡片子菜单
            cards_menu = self._view_menu.addMenu("卡片(&C)")
            main_window = self.parent()
            if main_window:
                if hasattr(main_window, "player_card"):
                    cards_menu.addAction(main_window.player_card.toggleViewAction())
                if hasattr(main_window, "timeline_card"):
                    cards_menu.addAction(main_window.timeline_card.toggleViewAction())
                if hasattr(main_window, "waveform_card"):
                    cards_menu.addAction(main_window.waveform_card.toggleViewAction())
                if hasattr(main_window, "translate_card"):
                    cards_menu.addAction(main_window.translate_card.toggleViewAction())

        # 分隔线
        self._view_menu.addSeparator()

        # 布局子菜单（使用自动生成的或手动创建的）
        if self._layout_submenu:
            self._view_menu.addMenu(self._layout_submenu)
        else:
            # 备用：手动创建布局子菜单
            layout_menu = self._view_menu.addMenu("布局(&L)")
            default_layout_action = QAction("默认布局", self)
            default_layout_action.triggered.connect(self._reset_layout)
            layout_menu.addAction(default_layout_action)

            # 打印布局信息（调试用）
            layout_menu.addSeparator()
            dump_layout_action = QAction("打印当前布局", self)
            dump_layout_action.triggered.connect(self.dump_layout.emit)
            layout_menu.addAction(dump_layout_action)

        # 分隔线
        self._view_menu.addSeparator()

        # 全屏
        fullscreen_action = QAction("全屏(&F)", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self.toggle_fullscreen.emit)
        self._view_menu.addAction(fullscreen_action)

        # 分隔线
        self._view_menu.addSeparator()

        # 调试控制台
        debug_console_action = QAction("调试控制台(&D)", self)
        debug_console_action.setShortcut(QKeySequence("F12"))
        debug_console_action.triggered.connect(self.toggle_debug_console.emit)
        self._view_menu.addAction(debug_console_action)

    def _rebuild_view_menu(self):
        """重新构建视图菜单"""
        # 找到视图菜单的位置
        for action in self.actions():
            if action.menu() and action.menu().title() == "视图(&V)":
                # 移除旧的视图菜单
                self.removeAction(action)
                break

        # 重新创建视图菜单
        self._create_view_menu()

    def _create_help_menu(self):
        """创建帮助菜单"""
        help_menu = self.addMenu("帮助(&H)")

        # 快捷键说明
        hotkey_action = QAction("快捷键说明(&K)...", self)
        hotkey_action.triggered.connect(self._show_hotkey_dialog)
        help_menu.addAction(hotkey_action)

    def _reset_layout(self):
        """重置为默认布局"""
        self.reset_layout.emit()

    def _show_hotkey_dialog(self):
        """显示快捷键说明对话框"""
        from chestnut_studio.ui.dialogs.hotkey_dialog import HotkeyDialog

        dialog = HotkeyDialog(self)
        dialog.exec()
