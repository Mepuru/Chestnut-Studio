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
        self.setWindowTitle("Chestnut Studio - 打轴工具")
        self.resize(1280, 720)

        # 禁用 Tab 合并，只允许嵌套停靠
        self.setDockNestingEnabled(True)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks)

        # 初始化设置
        self.settings = QSettings("ChestnutStudio", "KaoRouTool")

        # FFmpeg 实例
        self._ffmpeg = FFmpeg()

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
        """设置默认布局"""
        # 添加卡片到主窗口
        self.addDockWidget(Qt.LeftDockWidgetArea, self.player_card)
        self.addDockWidget(Qt.RightDockWidgetArea, self.timeline_card)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.waveform_card)
        self.addDockWidget(Qt.RightDockWidgetArea, self.translate_card)

        # 设置左右分割布局
        # 上层：视频播放(左) + 打轴编辑(右)
        self.splitDockWidget(self.player_card, self.timeline_card, Qt.Horizontal)

        # 下层：音频波形(左) + 翻译面板(右)
        self.splitDockWidget(self.waveform_card, self.translate_card, Qt.Horizontal)

        # 上下分割：上层和下层
        self.splitDockWidget(self.player_card, self.waveform_card, Qt.Vertical)

        # 设置初始大小比例
        # 上层高度约 500px，下层高度约 200px
        self.resizeDocks([self.player_card, self.waveform_card], [500, 200], Qt.Vertical)

        # 左右比例：左 55%，右 45%
        self.resizeDocks([self.player_card, self.timeline_card], [704, 576], Qt.Horizontal)
        self.resizeDocks([self.waveform_card, self.translate_card], [704, 576], Qt.Horizontal)

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

    def _create_statusbar(self):
        """创建状态栏"""
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _connect_signals(self):
        """连接各组件间的信号"""
        # --- 工具栏 → 播放卡片 ---
        self.toolbar.play_clicked.connect(self.player_card.play_pause)
        self.toolbar.rate_changed.connect(self.player_card.set_playback_rate)

        # 跳转信号：toolbar 发出 ms 偏移量，player_card 换算成绝对位置
        self.toolbar.skip_forward.connect(self._on_skip_forward)
        self.toolbar.skip_backward.connect(self._on_skip_backward)
        self.toolbar.frame_forward.connect(self._on_frame_forward)
        self.toolbar.frame_backward.connect(self._on_frame_backward)

        # --- 播放卡片 → 工具栏 ---
        self.player_card.position_changed.connect(self.toolbar.update_position)
        self.player_card.duration_changed.connect(self.toolbar.set_duration)
        self.player_card.playback_state_changed.connect(self.toolbar.set_playing)

        # --- 播放卡片 → 状态栏 ---
        self.player_card.duration_changed.connect(self._on_duration_changed)
        self.player_card.position_changed.connect(self._on_position_changed)

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

    def closeEvent(self, event):
        """关闭事件，保存布局"""
        self._save_layout()
        super().closeEvent(event)

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

    def _on_frame_forward(self):
        """前进 1 帧"""
        frame_ms = int(1000 / self.toolbar._fps)
        pos = self.player_card.get_position() + frame_ms
        self.player_card.set_position(min(pos, self.player_card.get_duration()))

    def _on_frame_backward(self):
        """后退 1 帧"""
        frame_ms = int(1000 / self.toolbar._fps)
        pos = self.player_card.get_position() - frame_ms
        self.player_card.set_position(max(pos, 0))

    # ========== 状态栏更新 ==========

    def _on_position_changed(self, ms: int):
        """播放位置变化 → 更新状态栏时间"""
        from chestnut_studio.utils.time_utils import ms_to_time_str

        self.status_bar.set_time(ms_to_time_str(ms))

    def _on_duration_changed(self, ms: int):
        """视频时长变化 → 更新状态栏"""
        self.status_bar.set_status(f"视频时长: {split_time(ms)}")
