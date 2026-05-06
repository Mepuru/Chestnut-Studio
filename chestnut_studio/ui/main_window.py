"""主窗口模块"""

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QFileDialog, QMainWindow

from chestnut_studio.core.ffmpeg import FFmpeg
from chestnut_studio.ui.cards.player_card import PlayerCard
from chestnut_studio.ui.cards.timeline_card import TimelineCard
from chestnut_studio.ui.cards.translate_card import TranslateCard
from chestnut_studio.ui.cards.waveform_card import WaveformCard
from chestnut_studio.ui.menubar import MenuBar
from chestnut_studio.ui.statusbar import StatusBar
from chestnut_studio.ui.toolbar import ToolBar
from chestnut_studio.utils.time_utils import split_time


class MainWindow(QMainWindow):
    """主窗口，管理所有 DockWidget 卡片

    功能：
    - 管理四个可拖拽的 DockWidget 卡片
    - 集成菜单栏、工具栏、状态栏
    - 支持布局保存与恢复
    - 连接各卡片间信号

    默认布局：
    ┌───────────────────────┬───────────────────────┐
    │                       │                       │
    │    视频播放卡片         │    打轴编辑卡片        │
    │    (左 55%)           │    (右 45%)           │
    │                       │                       │
    ├───────────────────────┼───────────────────────┤
    │                       │                       │
    │    音频波形卡片         │    翻译面板卡片        │
    │    高度 200px          │    高度 200px          │
    │                       │                       │
    └───────────────────────┴───────────────────────┘
    """

    # 视频文件过滤器
    VIDEO_FILTER = "视频文件 (*.mp4 *.avi *.flv *.mkv *.mov *.wmv *.mp3 *.wav *.aac);;所有文件 (*)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chestnut Studio")
        self.resize(1280, 720)

        # 禁用 Tab 合并，只允许嵌套停靠
        self.setDockNestingEnabled(True)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks)

        # 初始化设置
        self.settings = QSettings("ChestnutStudio", "KaoRouTool")

        # 布局比例常量
        self._layout_left_ratio = 0.39
        self._layout_top_ratio = 0.56

        # FFmpeg 实例
        self._ffmpeg = FFmpeg()
        self._layout_initialized = False

        # 创建 UI 组件
        self._create_cards()
        self._setup_default_layout()
        self._create_toolbar()
        self._create_menubar()
        self._create_statusbar()
        self._connect_signals()

        # 开发阶段：不恢复布局，每次都使用默认布局
        # TODO: 发布时取消注释以下代码
        # self._restore_layout()

    def _create_cards(self):
        """创建四个 DockWidget 卡片"""
        from PySide6.QtWidgets import QDockWidget

        # 视频播放卡片
        self.player_card = PlayerCard(self)
        self.player_card.setObjectName("player_card")
        self.player_card.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        # 打轴编辑卡片
        self.timeline_card = TimelineCard(self)
        self.timeline_card.setObjectName("timeline_card")
        self.timeline_card.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        # 音频波形卡片
        self.waveform_card = WaveformCard(self)
        self.waveform_card.setObjectName("waveform_card")
        self.waveform_card.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        # 翻译面板卡片
        self.translate_card = TranslateCard(self)
        self.translate_card.setObjectName("translate_card")
        self.translate_card.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        # 设置卡片属性
        for card in [self.player_card, self.timeline_card, self.waveform_card, self.translate_card]:
            card.setMinimumSize(200, 150)

    def _setup_default_layout(self):
        """设置默认布局

        布局示意（左39% 右61%，上56% 下44%）：
        ┌──────────────────┬───────────────────────────────┐
        │                  │                               │
        │  Player          │  Timeline (打轴)              │
        │                  │                               │
        ├──────────────────┼───────────────────────────────┤
        │  Waveform        │  Translation (翻译)           │
        │                  │                               │
        └──────────────────┴───────────────────────────────┘
        """
        # 清除固定尺寸约束
        for card in [self.player_card, self.timeline_card,
                     self.waveform_card, self.translate_card]:
            card.setMinimumSize(200, 150)
            card.setMaximumSize(16777215, 16777215)

        # 重置布局时先移除所有卡片
        if self._layout_initialized:
            self.removeDockWidget(self.player_card)
            self.removeDockWidget(self.timeline_card)
            self.removeDockWidget(self.waveform_card)
            self.removeDockWidget(self.translate_card)
        self._layout_initialized = True

        # 左列：player + waveform（显式添加到 Left 区域，再垂直分割）
        self.addDockWidget(Qt.LeftDockWidgetArea, self.player_card)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.waveform_card)
        self.splitDockWidget(self.player_card, self.waveform_card, Qt.Vertical)

        # 右列：timeline + translation（显式添加到 Right 区域，再垂直分割）
        self.addDockWidget(Qt.RightDockWidgetArea, self.timeline_card)
        self.addDockWidget(Qt.RightDockWidgetArea, self.translate_card)
        self.splitDockWidget(self.timeline_card, self.translate_card, Qt.Vertical)

        # 动态计算尺寸
        self._apply_layout_size()

        # 延迟确保卡片可见
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._show_all_cards)

    def _show_all_cards(self):
        """确保所有卡片可见"""
        for card in [self.player_card, self.timeline_card,
                     self.waveform_card, self.translate_card]:
            card.show()
            card.setVisible(True)

    def _apply_layout_size(self):
        """按固定比例设置卡片尺寸"""
        win_w = self.width()
        win_h = self.height() - 45
        left_w = int(win_w * self._layout_left_ratio)
        right_w = win_w - left_w - 4
        top_h = int(win_h * self._layout_top_ratio)
        bottom_h = win_h - top_h - 4

        self.resizeDocks(
            [self.player_card, self.timeline_card,
             self.waveform_card, self.translate_card],
            [left_w, right_w, left_w, right_w],
            Qt.Horizontal,
        )
        self.resizeDocks(
            [self.player_card, self.waveform_card,
             self.timeline_card, self.translate_card],
            [top_h, bottom_h, top_h, bottom_h],
            Qt.Vertical,
        )

    def resizeEvent(self, event):
        """窗口大小变化时保持卡片比例"""
        super().resizeEvent(event)
        if self._layout_initialized:
            self._apply_layout_size()

    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = ToolBar(self)
        self.addToolBar(self.toolbar)

    def _create_menubar(self):
        """创建菜单栏"""
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        # 连接菜单信号
        self.menu_bar.open_video.connect(self._on_open_video)
        self.menu_bar.open_subtitle.connect(self._on_open_subtitle)
        self.menu_bar.save_subtitle.connect(self._on_save_subtitle)
        self.menu_bar.quit_app.connect(self.close)
        self.menu_bar.toggle_fullscreen.connect(self._toggle_fullscreen)
        self.menu_bar.reset_layout.connect(self._setup_default_layout)
        self.menu_bar.dump_layout.connect(self._dump_layout_info)

    def _create_statusbar(self):
        """创建状态栏"""
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _connect_signals(self):
        """连接各组件间的信号"""
        # --- 工具栏 → 播放卡片 ---
        self.toolbar.play_clicked.connect(self.player_card.play_pause)
        self.toolbar.rate_changed.connect(self.player_card.set_playback_rate)

        # 跳转信号
        self.toolbar.skip_forward.connect(self._on_skip_forward)
        self.toolbar.skip_backward.connect(self._on_skip_backward)

        # AB 循环信号
        self.toolbar.ab_loop_a_clicked.connect(self._on_ab_loop_set_a)
        self.toolbar.ab_loop_b_clicked.connect(self._on_ab_loop_set_b)
        self.toolbar.ab_loop_clear_clicked.connect(self._on_ab_loop_clear)

        # --- 播放卡片 → 工具栏 ---
        self.player_card.position_changed.connect(self.toolbar.update_position)
        self.player_card.duration_changed.connect(self.toolbar.set_duration)
        self.player_card.playback_state_changed.connect(self.toolbar.set_playing)

        # --- 播放卡片 → 状态栏 ---
        self.player_card.duration_changed.connect(self._on_duration_changed)
        self.player_card.position_changed.connect(self._on_position_changed)

        # --- 播放卡片 → 波形卡片 ---
        self.player_card.position_changed.connect(self.waveform_card.update_position)
        self.player_card.duration_changed.connect(self.waveform_card.set_duration)

        # --- 播放卡片 AB 循环 → 工具栏和波形卡片 ---
        self.player_card.ab_loop_changed.connect(self.toolbar.update_ab_loop_state)
        self.player_card.ab_loop_changed.connect(self.waveform_card.set_ab_loop_region)

        # --- 波形卡片 → 播放卡片（点击跳转） ---
        self.waveform_card.position_clicked.connect(self.player_card.set_position)



    # ========== 布局管理 ==========

    def _restore_layout(self):
        """恢复上次保存的布局"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

    def _save_layout(self):
        """保存当前布局"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def _dump_layout_info(self):
        """打印当前布局信息到控制台（调试用）"""
        print("\n" + "=" * 60)
        print("布局调试信息")
        print("=" * 60)

        # 窗口尺寸
        geo = self.geometry()
        print(f"窗口尺寸: {geo.width()} x {geo.height()}")
        print(f"窗口位置: ({geo.x()}, {geo.y()})")
        print()

        # 各卡片信息
        cards = [
            ("player_card", self.player_card),
            ("timeline_card", self.timeline_card),
            ("waveform_card", self.waveform_card),
            ("translate_card", self.translate_card),
        ]

        for name, card in cards:
            area = self.dockWidgetArea(card)
            area_name = {
                Qt.LeftDockWidgetArea: "Left",
                Qt.RightDockWidgetArea: "Right",
                Qt.TopDockWidgetArea: "Top",
                Qt.BottomDockWidgetArea: "Bottom",
                Qt.NoDockWidgetArea: "None (浮动)",
            }.get(area, str(area))

            size = card.size()
            pos = card.pos()
            visible = card.isVisible()
            floating = card.isFloating()

            print(f"[{name}]")
            print(f"  区域: {area_name}")
            print(f"  尺寸: {size.width()} x {size.height()}")
            print(f"  位置: ({pos.x()}, {pos.y()})")
            print(f"  可见: {visible}  浮动: {floating}")
            print()

        # 保存的 state（Base64）
        state = self.saveState()
        print(f"QSettings state (Base64): {state.toBase64().data().decode()}")
        print("=" * 60 + "\n")

    def closeEvent(self, event):
        """关闭事件，保存布局"""
        self._save_layout()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """全局快捷键处理"""
        key = event.key()

        # 空格：播放/暂停
        if key == Qt.Key_Space:
            self.player_card.play_pause()
            event.accept()
            return

        # [：设置 A 点
        if key == Qt.Key_BracketLeft:
            self._on_ab_loop_set_a()
            event.accept()
            return

        # ]：设置 B 点
        if key == Qt.Key_BracketRight:
            self._on_ab_loop_set_b()
            event.accept()
            return

        # \：清除 AB 循环
        if key == Qt.Key_Backslash:
            self._on_ab_loop_clear()
            event.accept()
            return

        super().keyPressEvent(event)

    # ========== 菜单事件处理 ==========

    def _on_open_video(self):
        """打开视频文件对话框"""
        path, _ = QFileDialog.getOpenFileName(self, "打开视频文件", "", self.VIDEO_FILTER)
        if path:
            self._open_video_file(path)

    def _open_video_file(self, path: str):
        """打开视频文件并更新状态栏

        Args:
            path: 视频文件路径
        """
        if self.player_card.open_video(path):
            # 更新状态栏
            self.status_bar.set_status(f"已打开: {Path(path).name}")

            # 使用 FFmpeg 解析视频信息
            try:
                info = self._ffmpeg.get_video_info(path)
                self.status_bar.set_video_info(
                    resolution=f"{info.width}×{info.height}" if info.width else "",
                    fps=f"{info.fps:.0f}fps" if info.fps else "",
                    bitrate=f"{info.bitrate}kbps" if info.bitrate else "",
                )
                # 传递帧率给工具栏（用于逐帧和帧号显示）
                self.toolbar.set_fps(info.fps)
            except Exception:
                # FFmpeg 不可用时不报错，只是不显示视频信息
                self.status_bar.clear_video_info()

            # 加载波形（异步处理，避免阻塞 UI）
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._load_waveform(path))

    def _on_open_subtitle(self):
        """导入字幕文件"""
        # TODO: Phase 4 实现
        pass

    def _on_save_subtitle(self):
        """导出字幕文件"""
        # TODO: Phase 4 实现
        pass

    def _toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ========== 跳转/逐帧 ==========

    def _on_skip_forward(self, ms: int):
        """前进指定毫秒"""
        pos = self.player_card.get_position() + ms
        self.player_card.set_position(min(pos, self.player_card.get_duration()))

    def _on_skip_backward(self, ms: int):
        """后退指定毫秒"""
        pos = self.player_card.get_position() - ms
        self.player_card.set_position(max(pos, 0))

    # ========== AB 循环 ==========

    def _on_ab_loop_set_a(self):
        """设置 A 点"""
        self.player_card.set_ab_loop_a()
        a, b = self.player_card.get_ab_loop_points()
        if a >= 0:
            self.status_bar.set_status(f"AB 循环：A 点已设置 ({split_time(a)})")

    def _on_ab_loop_set_b(self):
        """设置 B 点"""
        self.player_card.set_ab_loop_b()
        a, b = self.player_card.get_ab_loop_points()
        if b >= 0:
            if a >= 0:
                self.status_bar.set_status(f"AB 循环：{split_time(a)} - {split_time(b)}")
            else:
                self.status_bar.set_status(f"AB 循环：B 点已设置 ({split_time(b)})")

    def _on_ab_loop_clear(self):
        """清除 AB 循环"""
        self.player_card.clear_ab_loop()
        self.status_bar.set_status("AB 循环已清除")

    # ========== 波形加载 ==========

    def _load_waveform(self, video_path: str):
        """加载视频的音频波形

        Args:
            video_path: 视频文件路径
        """
        success = self.waveform_card.load_waveform(video_path)
        if success:
            self.status_bar.set_status("波形加载完成")
        else:
            self.status_bar.set_status("波形加载失败")

    # ========== 状态栏更新 ==========

    def _on_position_changed(self, ms: int):
        """播放位置变化 → 更新状态栏时间"""

        total = self.player_card.get_duration()
        self.status_bar.set_time(split_time(ms), split_time(total) if total else "")

    def _on_duration_changed(self, ms: int):
        """视频时长变化 → 更新状态栏"""

        self.status_bar.set_time("00:00", split_time(ms))
        self.status_bar.set_status(f"视频时长: {split_time(ms)}")


