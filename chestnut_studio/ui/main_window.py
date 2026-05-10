"""主窗口模块"""

import os
from collections.abc import Callable
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

        # 布局比例常量
        self._layout_left_ratio = 0.39
        self._layout_top_ratio = 0.56

        # FFmpeg 实例
        self._ffmpeg = FFmpeg()
        self._layout_initialized = False

        # 调试控制台
        self._debug_console = None

        # 卡片字典 {card_id: BaseCard}
        self._cards: dict[str, BaseCard] = {}

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
        for card in [self.player_card, self.timeline_card, self.waveform_card, self.translate_card]:
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
        for card in [self.player_card, self.timeline_card, self.waveform_card, self.translate_card]:
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
            [self.player_card, self.timeline_card, self.waveform_card, self.translate_card],
            [left_w, right_w, left_w, right_w],
            Qt.Horizontal,
        )
        self.resizeDocks(
            [self.player_card, self.waveform_card, self.timeline_card, self.translate_card],
            [top_h, bottom_h, top_h, bottom_h],
            Qt.Vertical,
        )

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
        self.menu_bar.toggle_debug_console.connect(self._toggle_debug_console)

    def _create_statusbar(self):
        """创建状态栏"""
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _create_drag_overlay(self):
        """创建拖放覆盖层"""
        self._drag_overlay = DragOverlay(self)
        self._drag_overlay.video_dropped.connect(self._open_video_file)
        self._drag_overlay.subtitle_dropped.connect(self._import_subtitle_file)

    def _get_special_component(self, component_id: str):
        """获取非卡片组件（如 toolbar、statusbar）"""
        special = {
            "toolbar": self.toolbar,
            "statusbar": self.status_bar,
        }
        return special.get(component_id)

    def _get_relay_handlers(self) -> dict[str, Callable]:
        """声明需要 MainWindow 中转处理的信号。

        格式: "<source_card_id>.<signal_name>": handler_method
        """
        return {
            "player.position_changed": self._on_position_changed,
            "player.duration_changed": self._on_duration_changed,
            "player.video_opened": self._on_video_opened,
            "player.ab_loop_changed": self._on_ab_loop_changed,
            "waveform.subtitle_created": self._on_subtitle_created,
            "timeline.subtitle_changed": self._sync_subtitle_overlay,
            "timeline.subtitle_selected": self._on_subtitle_selected,
            "translate.text_saved": self._on_text_saved,
            "translate.jump_to_next": self._on_jump_to_next,
            "translate.jump_to_prev": self._on_jump_to_prev,
        }

    def _connect_declarative_signals(self):
        """自动连接所有卡片声明的信号"""
        # 获取中转处理声明
        relay_handlers = self._get_relay_handlers()

        # 1. 主动连接所有中转处理信号
        for source_key, handler in relay_handlers.items():
            parts = source_key.split(".", 1)
            if len(parts) != 2:
                continue
            src_id, signal_name = parts

            # 获取源卡片
            source = self._cards.get(src_id)
            if source is None:
                source = self._get_special_component(src_id)
            if source is None:
                print(f"[Signal] 未知源: {src_id}")
                continue

            # 获取信号
            signal = getattr(source, signal_name, None)
            if signal is None:
                print(f"[Signal] {src_id} 没有信号 {signal_name}")
                continue

            # 连接到中转处理函数
            signal.connect(handler)

        # 2. 连接卡片间声明式信号
        for card_id, card in self._cards.items():
            subscriptions = card.listens_to()
            for source_key, handler in subscriptions.items():
                # 跳过已由中转处理连接的信号
                if source_key in relay_handlers:
                    continue

                # 解析 "player.position_changed"
                parts = source_key.split(".", 1)
                if len(parts) != 2:
                    continue
                src_id, signal_name = parts

                # 获取源卡片
                source = self._cards.get(src_id)
                if source is None:
                    source = self._get_special_component(src_id)
                if source is None:
                    print(f"[Signal] 未知源: {src_id}")
                    continue

                # 获取信号
                signal = getattr(source, signal_name, None)
                if signal is None:
                    print(f"[Signal] {src_id} 没有信号 {signal_name}")
                    continue

                # 获取处理函数
                if callable(handler):
                    slot = handler
                else:
                    slot = getattr(card, handler, None)
                if slot is None:
                    print(f"[Signal] {card_id} 没有方法 {handler}")
                    continue

                # 连接
                signal.connect(slot)

    def _connect_signals(self):
        """连接各组件间的信号"""
        # 自动连接声明式信号
        self._connect_declarative_signals()

        # --- 工具栏 → 播放卡片（toolbar 不是 BaseCard，手动连接） ---
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

        # --- 播放卡片 AB 循环 → 工具栏 ---
        self.player_card.ab_loop_changed.connect(self.toolbar.update_ab_loop_state)

        # --- 播放卡片 → 视频打开后处理 ---
        self.player_card.video_opened.connect(self._on_video_opened)

        # --- 时间轴卡片 → 波形卡片（请求编辑字幕） ---
        self.timeline_card.edit_subtitle_requested.connect(self.waveform_card.enter_edit_mode)

        # --- 波形卡片 → 时间轴卡片（编辑完成） ---
        self.waveform_card.subtitle_edited.connect(self.timeline_card.apply_subtitle_edit)

        # --- 翻译面板 → 时间轴卡片（高亮当前编辑行） ---
        self.translate_card.editing_subtitle.connect(self.timeline_card.highlight_subtitle)

    def _on_subtitle_selected(self, col: int, start_ms: int):
        """字幕被选中 → 更新翻译面板"""
        self.translate_card.show_subtitle(col, start_ms)

    def _on_text_saved(self, col: int, start_ms: int, text: str):
        """翻译文本保存 → 更新时间轴卡片"""
        self.timeline_card.set_subtitle_text(col, start_ms, text)

    def _on_jump_to_next(self, col: int, start_ms: int):
        """跳转到下一条字幕"""
        next_sub = self.timeline_card.get_next_subtitle(col, start_ms)
        if next_sub:
            new_col, new_start = next_sub
            self.player_card.set_position(new_start)
            self.translate_card.show_subtitle(new_col, new_start)
        else:
            self.status_bar.set_status("已是最后一条字幕")

    def _on_jump_to_prev(self, col: int, start_ms: int):
        """跳转到上一条字幕"""
        prev_sub = self.timeline_card.get_prev_subtitle(col, start_ms)
        if prev_sub:
            new_col, new_start = prev_sub
            self.player_card.set_position(new_start)
            self.translate_card.show_subtitle(new_col, new_start)
        else:
            self.status_bar.set_status("已是第一条字幕")

    def _on_ab_loop_changed(self, a_point: int, b_point: int):
        """AB 循环状态变化 → 更新工具栏和波形卡片"""
        self.toolbar.update_ab_loop_state(a_point, b_point)
        self.waveform_card.set_ab_loop_region(a_point, b_point)

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

    def _on_video_opened(self, path: str):
        """视频打开后的处理（菜单打开和拖放均触发）

        Args:
            path: 视频文件路径
        """
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
            # 传递帧率给时间轴（用于帧号显示）
            self.timeline_card.set_fps(info.fps)
            # 传递帧率给波形图（用于帧号显示）
            self.waveform_card.set_fps(info.fps)

            # 调试输出
            if self._debug_console and self._debug_console.isVisible():
                print(f"[FFmpeg] 视频信息: {info.width}x{info.height}, {info.fps}fps, {info.bitrate}kbps, {info.duration}ms")
        except Exception as e:
            # FFmpeg 不可用时不报错，只是不显示视频信息
            self.status_bar.clear_video_info()
            if self._debug_console and self._debug_console.isVisible():
                print(f"[FFmpeg] 错误: {str(e)}")

        # 加载波形（异步处理，避免阻塞 UI）
        from PySide6.QtCore import QTimer

        QTimer.singleShot(100, lambda: self._load_waveform(path))

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

    # ========== 打轴功能 ==========

    def _on_subtitle_created(self, start_ms: int, end_ms: int, track: int):
        """打轴完成 → 添加字幕到时间轴 + 同步波形覆盖"""
        self.timeline_card.add_subtitle(start_ms, end_ms, col=track)

    def _sync_subtitle_overlay(self):
        """同步字幕数据到波形卡片的覆盖显示"""
        subtitle_data = self.timeline_card.get_subtitle_data()
        self.waveform_card.update_subtitle_overlay_from_data(subtitle_data)

    # ========== 状态栏更新 ==========

    def _on_position_changed(self, ms: int):
        """播放位置变化 → 更新状态栏时间"""

        total = self.player_card.get_duration()
        self.status_bar.set_time(split_time(ms), split_time(total) if total else "")

    def _on_duration_changed(self, ms: int):
        """视频时长变化 → 更新状态栏"""

        self.status_bar.set_time("00:00", split_time(ms))
        self.status_bar.set_status(f"视频时长: {split_time(ms)}")
