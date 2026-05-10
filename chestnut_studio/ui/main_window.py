"""主窗口模块"""

import os
from pathlib import Path

from PySide6.QtCore import QEvent, QSettings, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QMainWindow

from chestnut_studio.core.ffmpeg import FFmpeg
from chestnut_studio.core.subtitle_io import SubtitleIO
from chestnut_studio.resources import get_icon_path
from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.player_card import PlayerCard
from chestnut_studio.ui.cards.timeline_card import TimelineCard
from chestnut_studio.ui.cards.translate_card import TranslateCard
from chestnut_studio.ui.cards.waveform_card import WaveformCard
from chestnut_studio.ui.drag_overlay import SUBTITLE_EXTENSIONS, VIDEO_EXTENSIONS, DragOverlay
from chestnut_studio.ui.menubar import MenuBar
from chestnut_studio.ui.signal_decorator import relay
from chestnut_studio.ui.signal_manager import SignalManager
from chestnut_studio.ui.statusbar import StatusBar
from chestnut_studio.ui.toolbar import ToolBar
from chestnut_studio.utils.time_utils import split_time
from chestnut_studio.utils.version import get_version


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

    # 字幕文件过滤器
    SUBTITLE_FILTER = "SRT 字幕 (*.srt);;ASS 字幕 (*.ass);;所有文件 (*)"
    EXPORT_ASS_FILTER = "ASS 字幕 (*.ass)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chestnut Studio v{get_version()}")
        self.resize(1280, 720)

        # 设置窗口图标
        icon_path = get_icon_path()
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 禁用 Tab 合并，只允许嵌套停靠
        self.setDockNestingEnabled(True)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks)

        # 初始化设置
        self.settings = QSettings("ChestnutStudio", "KaoRouTool")

        # FFmpeg 实例
        self._ffmpeg = FFmpeg()
        self._layout_initialized = False
        self._current_layout = None  # 当前布局配置

        # 调试控制台
        self._debug_console = None

        # 卡片字典 {card_id: BaseCard}
        self._cards: dict[str, BaseCard] = {}

        # 信号管理器
        self._signal_manager = SignalManager(self)

        # 创建 UI 组件
        self._create_cards()
        self._setup_default_layout()
        self._create_toolbar()
        self._create_menubar()
        self._create_statusbar()
        self._create_drag_overlay()
        self._connect_signals()

        # 通知所有卡片就绪
        self._notify_cards_ready()

        # 拖放事件过滤
        self.setAcceptDrops(True)
        self.installEventFilter(self)

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

        # 设置翻译面板的字幕数据引用
        self.translate_card.set_subtitle_data(self.timeline_card.get_subtitle_data())

        # 设置卡片属性
        for card in [self.player_card, self.timeline_card, self.waveform_card, self.translate_card]:
            card.setMinimumSize(200, 150)

        # 填充卡片字典
        self._cards = {
            "player": self.player_card,
            "timeline": self.timeline_card,
            "waveform": self.waveform_card,
            "translate": self.translate_card,
        }

    def _setup_default_layout(self):
        """设置默认布局

        从配置文件加载默认布局并应用。
        """
        from chestnut_studio.ui.layout_config import LayoutConfig
        from chestnut_studio.ui.layout_engine import apply_layout

        # 清除固定尺寸约束
        for card in self._cards.values():
            card.setMinimumSize(200, 150)
            card.setMaximumSize(16777215, 16777215)

        # 加载默认布局配置
        try:
            import importlib.resources
            config_path = importlib.resources.files("chestnut_studio") / "resources" / "layouts" / "default.json"
            self._current_layout = LayoutConfig.from_json(config_path)
        except Exception:
            # 如果加载失败，使用硬编码的默认布局
            self._current_layout = None
            self._setup_fallback_layout()
            return

        # 应用布局
        apply_layout(self, self._current_layout, self._cards)
        self._layout_initialized = True

        # 延迟确保卡片可见
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._show_all_cards)

    def _setup_fallback_layout(self):
        """备用的硬编码布局（当配置文件加载失败时使用）"""
        # 清除固定尺寸约束
        for card in self._cards.values():
            card.setMinimumSize(200, 150)
            card.setMaximumSize(16777215, 16777215)

        # 重置布局时先移除所有卡片
        if self._layout_initialized:
            for card in self._cards.values():
                self.removeDockWidget(card)
        self._layout_initialized = True

        # 左列：player + waveform
        self.addDockWidget(Qt.LeftDockWidgetArea, self.player_card)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.waveform_card)
        self.splitDockWidget(self.player_card, self.waveform_card, Qt.Vertical)

        # 右列：timeline + translation
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
        for card in [self.player_card, self.timeline_card, self.waveform_card, self.translate_card]:
            card.show()
            card.setVisible(True)

    def _apply_layout_size(self):
        """按当前布局配置设置卡片尺寸"""
        if not self._current_layout:
            return

        from chestnut_studio.ui.layout_engine import _apply_sizes
        _apply_sizes(self, self._current_layout, self._cards)

    def resizeEvent(self, event):
        """窗口大小变化时保持卡片比例"""
        super().resizeEvent(event)
        if self._layout_initialized:
            self._apply_layout_size()
        # 保持覆盖层与窗口同尺寸
        if hasattr(self, "_drag_overlay"):
            self._drag_overlay.resize(self.size())

    def eventFilter(self, obj, event):
        """全局事件过滤器，拦截拖放事件显示覆盖层"""
        if obj is self and hasattr(self, "_drag_overlay"):
            etype = event.type()
            if etype == QEvent.DragEnter:
                mime = event.mimeData()
                if mime.hasUrls():
                    paths = [url.toLocalFile() for url in mime.urls()]
                    has_valid = any(
                        os.path.splitext(p)[1].lower() in VIDEO_EXTENSIONS | SUBTITLE_EXTENSIONS
                        for p in paths
                    )
                    if has_valid:
                        self._drag_overlay.update_for_files(paths)
                        self._drag_overlay.show()
                        self._drag_overlay.raise_()
                        event.acceptProposedAction()
                        return True
            elif etype == QEvent.DragLeave:
                self._drag_overlay.hide()
            elif etype == QEvent.Drop:
                mime = event.mimeData()
                if mime.hasUrls():
                    paths = [url.toLocalFile() for url in mime.urls()]
                    self._drag_overlay.handle_drop(paths)
                    event.acceptProposedAction()
                    return True
        return super().eventFilter(obj, event)

    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = ToolBar(self)
        self.addToolBar(self.toolbar)

    def _create_menubar(self):
        """创建菜单栏"""
        from chestnut_studio.ui.auto_menu import build_card_submenu, build_layout_submenu
        from chestnut_studio.ui.layout_config import get_builtin_layouts

        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        # 自动生成卡片子菜单
        card_submenu = build_card_submenu(
            parent=self.menu_bar,
            cards=self._cards,
            on_toggle_card=self._on_toggle_card,
        )
        self.menu_bar.set_card_submenu(card_submenu)

        # 自动生成布局子菜单
        layouts = get_builtin_layouts()
        layout_submenu = build_layout_submenu(
            parent=self.menu_bar,
            layouts=layouts,
            on_apply_layout=self._on_apply_layout,
            on_reset_layout=self._setup_default_layout,
        )
        self.menu_bar.set_layout_submenu(layout_submenu)

        # 连接菜单信号
        self.menu_bar.open_video.connect(self._on_open_video)
        self.menu_bar.open_subtitle.connect(self._on_open_subtitle)
        self.menu_bar.save_subtitle.connect(self._on_save_subtitle)
        self.menu_bar.quit_app.connect(self.close)
        self.menu_bar.toggle_fullscreen.connect(self._toggle_fullscreen)
        self.menu_bar.reset_layout.connect(self._setup_default_layout)
        self.menu_bar.dump_layout.connect(self._dump_layout_info)
        self.menu_bar.toggle_debug_console.connect(self._toggle_debug_console)

    def _on_toggle_card(self, card_id: str, visible: bool):
        """切换卡片显示/隐藏"""
        card = self._cards.get(card_id)
        if card:
            card.setVisible(visible)

    def _on_apply_layout(self, layout_name: str):
        """应用指定布局"""
        from chestnut_studio.ui.layout_config import get_builtin_layouts
        from chestnut_studio.ui.layout_engine import apply_layout

        layouts = get_builtin_layouts()
        config = layouts.get(layout_name)
        if config:
            apply_layout(self, config, self._cards)
            self._current_layout = config

    def _create_statusbar(self):
        """创建状态栏"""
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _create_drag_overlay(self):
        """创建拖放覆盖层"""
        self._drag_overlay = DragOverlay(self)
        self._drag_overlay.video_dropped.connect(self._open_video_file)
        self._drag_overlay.subtitle_dropped.connect(self._import_subtitle_file)

    def _connect_signals(self):
        """连接所有信号（使用 SignalManager）"""
        # 注册卡片和特殊组件
        self._signal_manager.register_cards(self._cards)
        self._signal_manager.register_special("toolbar", self.toolbar)
        self._signal_manager.register_special("statusbar", self.status_bar)

        # 注册状态栏动态订阅
        self._signal_manager.register_dynamic_relay(
            "player.position_changed", self._on_position_changed
        )
        self._signal_manager.register_dynamic_relay(
            "player.duration_changed", self._on_duration_changed
        )

        # 自动连接所有信号
        self._signal_manager.connect_all()

        # 手动连接 toolbar 信号（toolbar 不是 BaseCard）
        self.toolbar.play_clicked.connect(self.player_card.play_pause)
        self.toolbar.rate_changed.connect(self.player_card.set_playback_rate)
        self.toolbar.skip_forward.connect(self._on_skip_forward)
        self.toolbar.skip_backward.connect(self._on_skip_backward)
        self.toolbar.ab_loop_a_clicked.connect(self._on_ab_loop_set_a)
        self.toolbar.ab_loop_b_clicked.connect(self._on_ab_loop_set_b)
        self.toolbar.ab_loop_clear_clicked.connect(self._on_ab_loop_clear)

        # 播放卡片 → 工具栏
        self.player_card.position_changed.connect(self.toolbar.update_position)
        self.player_card.duration_changed.connect(self.toolbar.set_duration)
        self.player_card.playback_state_changed.connect(self.toolbar.set_playing)
        self.player_card.ab_loop_changed.connect(self.toolbar.update_ab_loop_state)

        # 编辑模式相关信号
        self.timeline_card.edit_subtitle_requested.connect(self.waveform_card.enter_edit_mode)
        self.waveform_card.subtitle_edited.connect(self.timeline_card.apply_subtitle_edit)
        self.translate_card.editing_subtitle.connect(self.timeline_card.highlight_subtitle)

    @relay("player.video_opened")
    def _on_video_opened(self, path: str):
        """视频打开后的处理（菜单打开和拖放均触发）"""
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
            self.toolbar.set_fps(info.fps)
            self.timeline_card.set_fps(info.fps)
            self.waveform_card.set_fps(info.fps)

            if self._debug_console and self._debug_console.isVisible():
                print(f"[FFmpeg] 视频信息: {info.width}x{info.height}, {info.fps}fps, {info.bitrate}kbps, {info.duration}ms")
        except Exception as e:
            self.status_bar.clear_video_info()
            if self._debug_console and self._debug_console.isVisible():
                print(f"[FFmpeg] 错误: {str(e)}")

        # 加载波形（异步处理，避免阻塞 UI）
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._load_waveform(path))

    @relay("player.ab_loop_changed")
    def _on_ab_loop_changed(self, a_point: int, b_point: int):
        """AB 循环状态变化 → 更新工具栏和波形卡片"""
        self.toolbar.update_ab_loop_state(a_point, b_point)
        self.waveform_card.set_ab_loop_region(a_point, b_point)

    @relay("waveform.subtitle_created")
    def _on_subtitle_created(self, start_ms: int, end_ms: int, track: int):
        """打轴完成 → 添加字幕到时间轴 + 同步波形覆盖"""
        self.timeline_card.add_subtitle(start_ms, end_ms, col=track)

    @relay("timeline.subtitle_changed")
    def _sync_subtitle_overlay(self):
        """同步字幕数据到波形卡片的覆盖显示"""
        subtitle_data = self.timeline_card.get_subtitle_data()
        self.waveform_card.update_subtitle_overlay_from_data(subtitle_data)

    @relay("timeline.subtitle_selected")
    def _on_subtitle_selected(self, col: int, start_ms: int):
        """字幕被选中 → 更新翻译面板"""
        self.translate_card.show_subtitle(col, start_ms)

    @relay("translate.text_saved")
    def _on_text_saved(self, col: int, start_ms: int, text: str):
        """翻译文本保存 → 更新时间轴卡片"""
        self.timeline_card.set_subtitle_text(col, start_ms, text)

    @relay("translate.jump_to_next")
    def _on_jump_to_next(self, col: int, start_ms: int):
        """跳转到下一条字幕"""
        next_sub = self.timeline_card.get_next_subtitle(col, start_ms)
        if next_sub:
            new_col, new_start = next_sub
            self.player_card.set_position(new_start)
            self.translate_card.show_subtitle(new_col, new_start)
        else:
            self.status_bar.set_status("已是最后一条字幕")

    @relay("translate.jump_to_prev")
    def _on_jump_to_prev(self, col: int, start_ms: int):
        """跳转到上一条字幕"""
        prev_sub = self.timeline_card.get_prev_subtitle(col, start_ms)
        if prev_sub:
            new_col, new_start = prev_sub
            self.player_card.set_position(new_start)
            self.translate_card.show_subtitle(new_col, new_start)
        else:
            self.status_bar.set_status("已是第一条字幕")

    def _notify_cards_ready(self):
        """通知所有卡片就绪"""
        for card in self._cards.values():
            card.on_ready()

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
        modifiers = event.modifiers()

        # 空格：播放/暂停
        if key == Qt.Key_Space:
            self.player_card.play_pause()
            event.accept()
            return

        # I：标记字幕开始点
        if key == Qt.Key_I and modifiers == Qt.NoModifier:
            self.waveform_card.mark_start()
            event.accept()
            return

        # O：标记字幕结束点 / 编辑模式设为终点
        if key == Qt.Key_O and modifiers == Qt.NoModifier:
            self.waveform_card.mark_end()
            event.accept()
            return

        # 1-4：快速切换轨道
        if key in (Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4) and modifiers == Qt.NoModifier:
            track = key - Qt.Key_0  # 1-4
            self.waveform_card.set_current_track(track)
            event.accept()
            return

        # Enter：确认编辑
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self.waveform_card.is_in_edit_mode():
                self.waveform_card.edit_confirm()
                event.accept()
                return

        # Escape：取消编辑
        if key == Qt.Key_Escape:
            if self.waveform_card.is_in_edit_mode():
                self.waveform_card.edit_cancel()
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
        """打开视频文件（由菜单调用）

        Args:
            path: 视频文件路径
        """
        self.player_card.open_video(path)

    def _on_open_subtitle(self):
        """导入字幕文件"""
        # 未加载视频时不允许导入字幕
        if not self.player_card._video_path:
            self.status_bar.set_status("请先加载视频文件")
            return

        path, _ = QFileDialog.getOpenFileName(self, "导入字幕", "", self.SUBTITLE_FILTER)
        if path:
            self._import_subtitle_file(path)

    def _import_subtitle_file(self, path: str):
        """导入字幕文件

        Args:
            path: 字幕文件路径
        """
        # 未加载视频时不允许导入字幕
        if not self.player_card._video_path:
            self.status_bar.set_status("请先加载视频文件")
            return
        try:
            ext = Path(path).suffix.lower()
            if ext == ".srt":
                data = SubtitleIO.import_srt(path)
                if data:
                    # SRT 导入到轨道1
                    subtitle_mgr = self.timeline_card.get_subtitle_manager()
                    for start_ms, (duration, text) in data.items():
                        subtitle_mgr.set(1, start_ms, duration, text)
                    self._sync_subtitle_overlay()
                    self.timeline_card._update_table()
                    self.status_bar.set_status(f"已导入 {len(data)} 条字幕")
                else:
                    self.status_bar.set_status("字幕文件为空或格式错误")

            elif ext == ".ass":
                multi_data = SubtitleIO.import_ass_multi_track(path)
                if multi_data:
                    subtitle_mgr = self.timeline_card.get_subtitle_manager()

                    # 样式到轨道的映射
                    style_to_track: dict[str, int] = {}
                    current_track = 1
                    total_count = 0

                    for style_name, style_data in multi_data.items():
                        if not style_data:
                            continue

                        # 分配轨道号
                        if style_name not in style_to_track:
                            # 确保轨道存在
                            subtitle_mgr.ensure_track(current_track)
                            style_to_track[style_name] = current_track
                            current_track += 1

                        track = style_to_track[style_name]

                        # 导入字幕数据
                        for start_ms, (duration, text) in style_data.items():
                            subtitle_mgr.set(track, start_ms, duration, text)
                            total_count += 1

                    # 刷新界面
                    self._sync_subtitle_overlay()
                    self.timeline_card.refresh_track_combos()

                    # 刷新波形卡片的轨道选择器
                    max_track = subtitle_mgr.get_max_track()
                    self.waveform_card.refresh_track_combo(max_track)

                    # 刷新时间轴表格显示
                    self.timeline_card._update_table()

                    # 构建状态信息
                    track_info = ", ".join([f"{style}→轨道{track}" for style, track in style_to_track.items()])
                    self.status_bar.set_status(f"已导入 {total_count} 条字幕 ({track_info})")

                    # 调试输出
                    if self._debug_console and self._debug_console.isVisible():
                        print(f"[导入] 样式映射: {track_info}")
                else:
                    self.status_bar.set_status("字幕文件为空或格式错误")
            else:
                self.status_bar.set_status(f"不支持的字幕格式: {ext}")

        except Exception as e:
            self.status_bar.set_status(f"导入失败: {str(e)}")
            if self._debug_console and self._debug_console.isVisible():
                print(f"[导入] 错误: {str(e)}")

    def _on_save_subtitle(self):
        """导出字幕文件"""
        path, _ = QFileDialog.getSaveFileName(self, "导出 ASS 字幕", "", self.EXPORT_ASS_FILTER)
        if path:
            self._export_ass_file(path)

    def _export_ass_file(self, path: str):
        """导出 ASS 字幕文件

        Args:
            path: 输出文件路径
        """
        try:
            subtitle_data = self.timeline_card.get_subtitle_data()

            # 过滤空轨道
            tracks = {}
            for col, sub_data in subtitle_data.items():
                if sub_data:
                    tracks[col] = sub_data

            if not tracks:
                self.status_bar.set_status("没有字幕数据可导出")
                return

            # 生成轨道样式名
            track_styles = {}
            for col in tracks:
                track_styles[col] = f"轨道 {col}"

            SubtitleIO.export_ass(path, tracks, track_styles)
            self.status_bar.set_status(f"已导出到: {Path(path).name}")

        except Exception as e:
            self.status_bar.set_status(f"导出失败: {str(e)}")

    def _toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _toggle_debug_console(self):
        """切换调试控制台"""
        from chestnut_studio.ui.dialogs.debug_console import DebugConsole

        if self._debug_console is None:
            self._debug_console = DebugConsole(self)
            self._debug_console.enable_redirect()
            self._debug_console.show()
            print("[调试模式] 已开启，所有输出将显示在此控制台")
        elif self._debug_console.isVisible():
            self._debug_console.disable_redirect()
            self._debug_console.hide()
        else:
            self._debug_console.enable_redirect()
            self._debug_console.show()
            print("[调试模式] 已重新开启")

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
        if self._debug_console and self._debug_console.isVisible():
            print(f"[波形] 开始加载: {video_path}")

        success = self.waveform_card.load_waveform(video_path)
        if success:
            self.status_bar.set_status("波形加载完成")
            if self._debug_console and self._debug_console.isVisible():
                print("[波形] 加载完成")
        else:
            self.status_bar.set_status("波形加载失败")
            if self._debug_console and self._debug_console.isVisible():
                print("[波形] 加载失败")

    # ========== 状态栏更新 ==========

    def _on_position_changed(self, ms: int):
        """播放位置变化 → 更新状态栏时间"""

        total = self.player_card.get_duration()
        self.status_bar.set_time(split_time(ms), split_time(total) if total else "")

    def _on_duration_changed(self, ms: int):
        """视频时长变化 → 更新状态栏"""

        self.status_bar.set_time("00:00", split_time(ms))
        self.status_bar.set_status(f"视频时长: {split_time(ms)}")
