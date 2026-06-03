"""主窗口模块

三区域布局：左侧视频播放器 + 右侧笔记列表 + 底部输入栏。
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
from chestnut_studio.core.track_config import NOTE_TYPES, load_track_colors, save_track_colors, set_config_path
from chestnut_studio.resources import get_icon_path
from chestnut_studio.ui.cards.player_card import PlayerCard
from chestnut_studio.ui.input_bar import InputBar
from chestnut_studio.ui.note_panel import NotePanel
from chestnut_studio.utils.time_utils import ms_to_time_str
from chestnut_studio.utils.version import get_version


class MainWindow(QMainWindow):
    """主窗口

    布局结构：
    ┌─────────────────────────┬──────────────────────┐
    │                         │                      │
    │     PlayerCard          │    NotePanel          │
    │     (视频+控制栏)       │    (笔记列表)         │
    │                         │                      │
    ├─────────────────────────┤                      │
    │     InputBar            │                      │
    └─────────────────────────┴──────────────────────┘
    """

    VIDEO_FILTER = "视频文件 (*.mp4 *.avi *.flv *.mkv *.mov *.wmv *.mp3 *.wav *.aac);;所有文件 (*)"
    NOTE_FILTER = "笔记文件 (*.txt)"

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

        # 加载轨道颜色配置
        config_dir = Path.home() / ".chestnut_studio"
        config_dir.mkdir(parents=True, exist_ok=True)
        colors_path = config_dir / "track_colors.json"
        set_config_path(colors_path)
        load_track_colors()

        # 创建 UI
        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_statusbar()
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

        merge_action = QAction("导入字幕合并 (ASS+TXT)...", self)
        merge_action.triggered.connect(self._on_merge_ass_txt)
        file_menu.addAction(merge_action)

        file_menu.addSeparator()

        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # ── 快捷键按钮（菜单栏右侧） ──
        menu_bar.addSeparator()
        self._shortcut_action = QAction("快捷键", self)
        self._shortcut_action.triggered.connect(self._show_shortcuts)
        menu_bar.addAction(self._shortcut_action)

        self._term_view_action = QAction("术语", self)
        self._term_view_action.triggered.connect(self._show_terms)
        menu_bar.addAction(self._term_view_action)

    def _setup_central_widget(self):
        """创建中央区域布局"""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 输入栏（放在左侧，与视频右边界对齐） ──
        self.input_bar = InputBar(self)

        # ── 左侧：播放器 + 输入栏 ｜ 右侧：笔记列表 ──
        left_widget = QWidget()
        left_widget.setObjectName("leftPane")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.player_card = PlayerCard(self)
        self.player_card.setMinimumWidth(400)
        left_layout.addWidget(self.player_card, 1)
        left_layout.addWidget(self.input_bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.setHandleWidth(1)
        splitter.addWidget(left_widget)

        self.note_panel = NotePanel(self._note_manager, self)
        self.note_panel.setMinimumWidth(240)
        self.note_panel.setMaximumWidth(400)
        splitter.addWidget(self.note_panel)

        splitter.setSizes([700, 300])
        main_layout.addWidget(splitter, 1)

    def _setup_statusbar(self):
        """配置状态栏：左侧信息、右侧版本号"""
        from PySide6.QtWidgets import QLabel

        self.statusBar().showMessage("拖入视频文件 或 Ctrl+O 打开")

        ver_label = QLabel(f"v{get_version()}")
        ver_label.setObjectName("versionLabel")
        self.statusBar().addPermanentWidget(ver_label)

    def _connect_signals(self):
        """连接信号"""
        # 播放器位置变化 → 更新输入栏时间戳
        self.player_card.position_changed.connect(self.input_bar.set_timestamp)

        # 视频打开 → 更新窗口标题
        self.player_card.video_opened.connect(self._on_video_opened)

        # 输入栏发送笔记 → 添加到管理器 + 刷新列表
        self.input_bar.note_sent.connect(self._on_note_sent)

        # 笔记列表双击 → 跳转视频 + 载入输入框
        self.note_panel.jump_to_position.connect(self.player_card.set_position)
        self.note_panel.edit_requested.connect(self.input_bar.load_for_edit)
        self.note_panel.term_requested.connect(self._on_term_requested)
        self.input_bar.term_added.connect(self._on_term_added)

    def _setup_drop(self):
        """设置拖放支持"""
        self.setAcceptDrops(True)

    # ── 术语查看 ──

    def _show_terms(self):
        """显示术语列表"""
        from chestnut_studio.ui.term_dialog import TermTableDialog

        terms = self._note_manager.get_terms()
        if not terms:
            QMessageBox.information(self, "术语", "暂无术语。")
            return
        dialog = TermTableDialog(self, self._note_manager)
        dialog.exec()

    # ── 快捷键帮助 ──

    def _show_shortcuts(self):
        """显示快捷键列表"""
        from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("快捷键")
        dialog.setMinimumSize(400, 320)
        dialog.setObjectName("shortcutDialog")

        table = QTableWidget(dialog)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["按键", "功能"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.verticalHeader().hide()

        shortcuts = [
            ("F1", "播放 / 暂停"),
            ("F2 / ←", "后退 5 秒"),
            ("F3 / →", "前进 5 秒"),
            ("Ctrl+0~9", "切换轨道"),
            ("Ctrl+O", "打开视频"),
            ("Ctrl+E", "导出笔记"),
            ("Ctrl+I", "导入笔记"),
            ("Ctrl+Q", "退出"),
            ("Enter", "发送笔记（输入框）"),
            ("Delete", "删除选中笔记（列表）"),
        ]

        table.setRowCount(len(shortcuts))
        for i, (key, desc) in enumerate(shortcuts):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(desc))

        table.resizeColumnsToContents()

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(table)
        dialog.exec()

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
        except Exception:  # ffmpeg 调用可能因缺少可执行文件/格式不支持失败
            self.statusBar().showMessage(f"已打开: {filename}", 5000)

    # ── 笔记操作 ──

    def _on_note_sent(self, note_type: str, timestamp_ms: int, text: str):
        """收到新笔记"""
        self._note_manager.add(timestamp_ms=timestamp_ms, text=text, note_type=note_type)
        self.note_panel.refresh()

    def _on_term_requested(self, note_text: str, origin: str):
        """从笔记打开术语录入"""
        from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("术语")
        dialog.setMinimumSize(450, 400)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(6)

        origin_text = Path(self.player_card.get_video_path()).name if self.player_card.get_video_path() else ""
        origin_text = f"{origin_text} {origin}" if origin_text else origin

        layout.addWidget(QLabel("原文（上下文）:"))
        context_edit = QLineEdit(note_text)
        context_edit.selectAll()
        layout.addWidget(context_edit)

        layout.addWidget(QLabel("术语（关键词）:"))
        source_edit = QLineEdit()
        source_edit.setPlaceholderText("从原文复制要查询的词...")
        layout.addWidget(source_edit)

        layout.addWidget(QLabel("译文（中文）:"))
        trans_edit = QLineEdit()
        trans_edit.setPlaceholderText("对应的中文翻译...")
        layout.addWidget(trans_edit)

        layout.addWidget(QLabel("出处:"))
        origin_edit = QLineEdit(origin_text)
        layout.addWidget(origin_edit)

        layout.addWidget(QLabel("参考资料:"))
        ref_edit = QLineEdit()
        ref_edit.setPlaceholderText("词典/网站/工具书名称或链接...")
        layout.addWidget(ref_edit)

        layout.addWidget(QLabel("备注:"))
        note_edit = QTextEdit()
        note_edit.setPlaceholderText("语法说明、用法注意...")
        note_edit.setAcceptRichText(False)
        note_edit.setMinimumHeight(80)
        layout.addWidget(note_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.Accepted:
            source = source_edit.text().strip()
            trans = trans_edit.text().strip()
            o = origin_edit.text().strip()
            ctx = context_edit.text().strip()
            ref = ref_edit.text().strip()
            n = note_edit.toPlainText().strip()
            if ref:
                n = ("参考: " + ref) + ("\n" + n if n else "")
            if ctx:
                n = "原文: " + ctx + ("\n" + n if n else "")
            if source and trans:
                self._on_term_added(source, trans, o, n)

    def _on_term_added(self, source: str, translation: str, origin: str, note: str):
        """添加术语"""
        self._note_manager.add_term(source, translation, origin, note)
        self.statusBar().showMessage(f"术语: {source} → {translation}", 3000)

    def _on_export_notes(self):
        """导出笔记 — 选轨道、选格式"""
        if self._note_manager.count() == 0:
            QMessageBox.information(self, "导出笔记", "没有笔记可导出。")
            return

        # 导出对话框：选轨道
        used_types = self._note_manager.get_used_types()
        if not used_types:
            return

        from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("导出笔记")
        dialog.setMinimumWidth(280)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("选择要导出的轨道:"))

        track_cbs = {}
        for t in NOTE_TYPES:
            cb = QCheckBox(t)
            cb.setChecked(t in used_types)
            cb.setEnabled(t in used_types)
            track_cbs[t] = cb
            layout.addWidget(cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("导出")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        selected_tracks = [t for t, cb in track_cbs.items() if cb.isChecked()]
        if not selected_tracks:
            self.statusBar().showMessage("未选择任何轨道", 3000)
            return

        # 默认文件名 = 视频名（过长截断）
        video_path = self.player_card.get_video_path()
        default_name = "notes.txt"
        if video_path:
            name = Path(video_path).stem
            if len(name) > 40:
                name = name[:37] + "..."
            default_name = name + ".txt"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出笔记",
            default_name,
            "文本文件 (*.txt)",
        )
        if not path:
            return

        # 获取视频信息写入头部
        vname = Path(video_path).name if video_path else ""
        dur = ms_to_time_str(self.player_card.get_duration()) if video_path else ""
        res = fps = bitrate = ""
        if video_path:
            try:
                info = self._ffmpeg.get_video_info(video_path)
                if info.width:
                    res = f"{info.width}x{info.height}"
                if info.fps:
                    fps = f"{info.fps:.0f}fps"
                if info.bitrate:
                    bitrate = f"{info.bitrate}kbps"
            except Exception:  # ffmpeg 调用失败时跳过视频信息
                pass
        count = self._note_manager.export_text(path, selected_tracks, vname, dur, res, fps, bitrate)
        self._note_manager.export_terms(path)
        self.statusBar().showMessage(f"已导出 {count} 条笔记", 3000)

    def _on_import_notes(self):
        """从 txt 文件导入笔记"""
        path, _ = QFileDialog.getOpenFileName(self, "导入笔记", "", self.NOTE_FILTER)
        if path:
            count = self._note_manager.import_text(path)
            term_count = self._note_manager.import_terms(path)
            if count == 0:
                QMessageBox.warning(
                    self,
                    "导入失败",
                    "文件格式不匹配，无法导入任何笔记。\n\n"
                    "请确保每行格式为:\n"
                    "  轨道名  时间  |  内容\n\n"
                    "例如:\n"
                    "  轨道1\t00:15.20\t| 你好",
                )
            else:
                msg = f"已导入 {count} 条笔记"
                if term_count:
                    msg += f"，{term_count} 条术语"
                self.statusBar().showMessage(msg, 3000)
            self.note_panel.refresh()

    def _on_merge_ass_txt(self):
        """打开 ASS+TXT 字幕合并对话框"""
        from chestnut_studio.ui.merge_dialog import MergeDialog

        dialog = MergeDialog(self)
        dialog.exec()

    def closeEvent(self, event):
        """关闭窗口时保存轨道颜色"""
        save_track_colors()
        super().closeEvent(event)

    # ── 快捷键 ──

    def keyPressEvent(self, event):
        """全局快捷键"""
        key = event.key()
        mod = event.modifiers()

        # ── 全局快捷键（输入框有焦点也生效） ──
        # F1 → 播放/暂停
        if key == Qt.Key_F1:
            self.player_card.play_pause()
            event.accept()
            return

        # F2 / ← → 后退 5 秒
        if key in (Qt.Key_F2, Qt.Key_Left):
            self.player_card.skip_back()
            event.accept()
            return

        # F3 / → → 前进 5 秒
        if key in (Qt.Key_F3, Qt.Key_Right):
            self.player_card.skip_forward()
            event.accept()
            return

        # Ctrl+1~9 / Ctrl+0 → 切换轨道
        if mod == Qt.ControlModifier and Qt.Key_0 <= key <= Qt.Key_9:
            track = 10 if key == Qt.Key_0 else key - Qt.Key_1 + 1
            self.input_bar.set_current_track(track)
            event.accept()
            return

        # ── 输入框有焦点时，其他按键交给输入框处理 ──
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
