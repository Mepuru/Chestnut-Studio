"""主窗口模块

B站风格三区域布局：左侧视频播放器 + 右侧笔记列表 + 底部输入栏。
纯 QWidget 布局，无 QDockWidget。
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.ffmpeg import FFmpeg
from chestnut_studio.core.note_manager import NoteManager
from chestnut_studio.resources import get_icon_path
from chestnut_studio.ui.cards.player_card import PlayerCard
from chestnut_studio.ui.input_bar import InputBar
from chestnut_studio.ui.note_panel import NotePanel
from chestnut_studio.utils.version import get_version


class MainWindow(QMainWindow):
    """主窗口

    布局结构：
    ┌─────────────────────────┬──────────────────────┐
    │                         │                      │
    │     PlayerCard          │    NotePanel          │
    │     (视频+控制栏)       │    (笔记列表)         │
    │                         │                      │
    ├─────────────────────────┴──────────────────────┤
    │     InputBar (类型选择 + 输入框 + 发送)         │
    └────────────────────────────────────────────────┘
    """

    VIDEO_FILTER = "视频文件 (*.mp4 *.avi *.flv *.mkv *.mov *.wmv *.mp3 *.wav *.aac);;所有文件 (*)"
    NOTE_FILTER = "笔记文件 (*.json);;所有文件 (*)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chestnut Studio v{get_version()}")
        self.resize(1200, 700)
        self.setMinimumSize(800, 500)

        # 设置窗口图标
        icon_path = get_icon_path()
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 数据模型
        self._note_manager = NoteManager()
        self._ffmpeg = FFmpeg()

        # 创建 UI
        self._setup_menu_bar()
        self._setup_central_widget()
        self._connect_signals()
        self._setup_drop()

    # ── UI 构建 ──

    def _setup_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        menu_bar.setObjectName("mainMenuBar")

        # 文件菜单
        file_menu = menu_bar.addMenu("文件(&F)")

        open_video_action = QAction("打开视频(&O)...", self)
        open_video_action.setShortcut(QKeySequence("Ctrl+O"))
        open_video_action.triggered.connect(self._on_open_video)
        file_menu.addAction(open_video_action)

        file_menu.addSeparator()

        export_action = QAction("导出笔记(&E)...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._on_export_notes)
        file_menu.addAction(export_action)

        import_action = QAction("导入笔记(&I)...", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._on_import_notes)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    def _setup_central_widget(self):
        """创建中央区域布局"""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 左侧播放器 + 右侧笔记列表（可拖拽分割） ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.setHandleWidth(1)

        # 左侧：视频播放器
        self.player_card = PlayerCard(self)
        self.player_card.setMinimumWidth(400)
        splitter.addWidget(self.player_card)

        # 右侧：笔记列表
        self.note_panel = NotePanel(self._note_manager, self)
        self.note_panel.setMinimumWidth(240)
        self.note_panel.setMaximumWidth(400)
        splitter.addWidget(self.note_panel)

        # 默认比例 65:35
        splitter.setSizes([700, 300])
        main_layout.addWidget(splitter, 1)

        # ── 底部：输入栏 ──
        self.input_bar = InputBar(self)
        main_layout.addWidget(self.input_bar)

    def _connect_signals(self):
        """连接信号"""
        # 播放器位置变化 → 更新输入栏时间戳
        self.player_card.position_changed.connect(self.input_bar.set_timestamp)

        # 视频打开 → 更新窗口标题
        self.player_card.video_opened.connect(self._on_video_opened)

        # 输入栏发送笔记 → 添加到管理器 + 刷新列表
        self.input_bar.note_sent.connect(self._on_note_sent)

        # 笔记列表双击 → 跳转到视频位置
        self.note_panel.jump_to_position.connect(self.player_card.set_position)

    def _setup_drop(self):
        """设置拖放支持"""
        self.setAcceptDrops(True)

    # ── 视频操作 ──

    def _on_open_video(self):
        """打开视频文件对话框"""
        path, _ = QFileDialog.getOpenFileName(self, "打开视频文件", "", self.VIDEO_FILTER)
        if path:
            self.player_card.open_video(path)

    def _on_video_opened(self, path: str):
        """视频打开后更新标题和信息"""
        filename = Path(path).name
        self.setWindowTitle(f"Chestnut Studio — {filename}")

        # 获取视频信息
        try:
            info = self._ffmpeg.get_video_info(path)
            fps_text = f"{info.fps:.0f}fps " if info.fps else ""
            res_text = f"{info.width}×{info.height} " if info.width else ""
            status = f"已打开: {filename}  |  {res_text}{fps_text}"
            self.statusBar().showMessage(status, 5000)
        except Exception:
            self.statusBar().showMessage(f"已打开: {filename}", 5000)

    # ── 笔记操作 ──

    def _on_note_sent(self, note_type: str, timestamp_ms: int, text: str):
        """收到新笔记"""
        self._note_manager.add(timestamp_ms=timestamp_ms, text=text, note_type=note_type)
        self.note_panel.refresh()

    def _on_export_notes(self):
        """导出笔记为 JSON"""
        if self._note_manager.count() == 0:
            QMessageBox.information(self, "导出笔记", "没有笔记可导出。")
            return

        path, _ = QFileDialog.getSaveFileName(self, "导出笔记", "notes.json", self.NOTE_FILTER)
        if path:
            self._note_manager.export_json(path)
            self.statusBar().showMessage(f"已导出 {self._note_manager.count()} 条笔记", 3000)

    def _on_import_notes(self):
        """从 JSON 导入笔记"""
        path, _ = QFileDialog.getOpenFileName(self, "导入笔记", "", self.NOTE_FILTER)
        if path:
            count = self._note_manager.import_json(path)
            self.note_panel.refresh()
            self.statusBar().showMessage(f"已导入 {count} 条笔记", 3000)

    # ── 快捷键 ──

    def keyPressEvent(self, event):
        """全局快捷键"""
        key = event.key()

        if key == Qt.Key_Space:
            self.player_card.play_pause()
            event.accept()
            return

        # 输入框有焦点时不拦截 Enter
        if self.input_bar._input.hasFocus():
            super().keyPressEvent(event)
            return

        super().keyPressEvent(event)

    # ── 拖放支持 ──

    VIDEO_EXTENSIONS = {".mp4", ".avi", ".flv", ".mkv", ".mov", ".wmv", ".mp3", ".wav", ".aac"}

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            if any(Path(p).suffix.lower() in self.VIDEO_EXTENSIONS for p in paths):
                event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in self.VIDEO_EXTENSIONS:
                self.player_card.open_video(path)
                break
