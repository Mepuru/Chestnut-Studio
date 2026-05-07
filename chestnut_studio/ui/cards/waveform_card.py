"""音频波形卡片模块

功能：
- 主音轨波形显示（pyqtgraph）
- 红色时间线跟随播放
- 视窗滑动跟随播放位置
- 点击跳转到对应时间
- 滚轮缩放（以鼠标位置为中心）
- 打轴功能：I/O 键标记开始/结束点
- 字幕条覆盖显示（从 SubtitleManager 数据同步）
"""

import os
import tempfile

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QDockWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from chestnut_studio.core.audio import compute_envelope_fast, downsample_waveform, load_waveform
from chestnut_studio.core.ffmpeg import FFmpeg
from chestnut_studio.utils.time_utils import ms_to_time_str

# 打轴按钮样式
MARK_BTN_STYLE = """
    QPushButton {
        background: #27272a;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        font-size: 9pt;
        padding: 3px 12px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background: #3f3f46;
    }
    QPushButton:pressed {
        background: #18181b;
    }
"""

# 打轴按钮激活样式（正在标记中）
MARK_ACTIVE_STYLE = """
    QPushButton {
        background: #16a34a;
        border: 1px solid #22c55e;
        color: #ffffff;
        font-size: 9pt;
        padding: 3px 12px;
        border-radius: 3px;
        font-weight: bold;
    }
    QPushButton:hover {
        background: #22c55e;
    }
"""


class WaveformPlotWidget(pg.PlotWidget):
    """波形绘图组件，支持滚轮缩放和点击跳转"""

    position_clicked = Signal(int)  # 点击位置 (ms)
    zoom_changed = Signal(float)  # 缩放倍数变化

    # 默认视窗宽度（毫秒）
    DEFAULT_VIEW_WINDOW_MS = 30000  # 30 秒
    # 最小视窗宽度（毫秒）- 约 1 秒
    MIN_VIEW_WINDOW_MS = 1000
    # 最大视窗宽度（毫秒）- 视频总时长
    MAX_VIEW_WINDOW_MS = 600000  # 10 分钟

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration_ms = 0
        self._view_window_ms = self.DEFAULT_VIEW_WINDOW_MS
        self._zoom_factor = 1.0

        # 拖动相关状态
        self._dragging = False
        self._drag_start_pos = None
        self._drag_start_view = None

        self._setup_plot()

    def _setup_plot(self):
        """配置绘图区域"""
        # 背景色
        self.setBackground("#0f0f14")

        # 禁用自动范围，手动控制
        self.enableAutoRange(x=False, y=False)

        # 隐藏 Auto Range 按钮（左下角的 "A" 按钮）
        self.plotItem.hideButtons()

        # 显示底部时间轴
        self.showAxis("bottom")
        axis = self.getAxis("bottom")
        axis.setPen(pg.mkPen(color="#52525b", width=1))
        axis.setTextPen(pg.mkPen(color="#a1a1aa"))
        axis.setTickFont(QFont("Consolas", 8))

        # 隐藏左侧轴
        self.hideAxis("left")

        # 设置边距
        self.plotItem.setContentsMargins(0, 0, 0, 20)

        # 禁用右键菜单
        self.setMenuEnabled(False)

        # 禁用拖拽平移（手动控制视窗）
        self.setMouseEnabled(x=False, y=False)

        # 设置时间轴格式
        self._setup_time_axis()

    def _setup_time_axis(self):
        """设置时间轴格式"""
        axis = self.getAxis("bottom")

        def time_tick_strings(values, scale, spacing):
            """将毫秒值转换为 mm:ss 格式"""
            strings = []
            for v in values:
                if v < 0:
                    strings.append("")
                else:
                    # 转换为 mm:ss 格式
                    total_seconds = int(v / 1000)
                    minutes = total_seconds // 60
                    seconds = total_seconds % 60
                    strings.append(f"{minutes}:{seconds:02d}")
            return strings

        axis.tickStrings = time_tick_strings

    def set_duration(self, duration_ms: int):
        """设置视频总时长"""
        self._duration_ms = duration_ms
        # 限制最大视窗
        self.MAX_VIEW_WINDOW_MS = max(duration_ms, 60000)

    def set_view_window(self, window_ms: int):
        """设置视窗宽度"""
        self._view_window_ms = max(self.MIN_VIEW_WINDOW_MS, min(window_ms, self.MAX_VIEW_WINDOW_MS))
        self._zoom_factor = self.DEFAULT_VIEW_WINDOW_MS / self._view_window_ms
        self.zoom_changed.emit(self._zoom_factor)

    def get_view_window(self) -> int:
        """获取当前视窗宽度"""
        return self._view_window_ms

    def get_zoom_factor(self) -> float:
        """获取当前缩放倍数"""
        return self._zoom_factor

    def wheelEvent(self, event: QWheelEvent):
        """滚轮缩放"""
        if self._duration_ms <= 0:
            return

        # 获取滚轮方向
        delta = event.angleDelta().y()
        if delta == 0:
            return

        # 缩放因子
        zoom_step = 1.2
        if delta > 0:
            # 向上滚动 - 放大（缩小视窗）
            new_window = int(self._view_window_ms / zoom_step)
        else:
            # 向上滚动 - 缩小（放大视窗）
            new_window = int(self._view_window_ms * zoom_step)

        # 限制范围
        new_window = max(self.MIN_VIEW_WINDOW_MS, min(new_window, self.MAX_VIEW_WINDOW_MS))

        if new_window != self._view_window_ms:
            # 获取鼠标位置对应的时间点（缩放中心）
            mouse_pos = event.position()
            view_pos = self.plotItem.vb.mapSceneToView(mouse_pos)
            center_time = view_pos.x()

            # 计算鼠标在视窗中的相对位置
            current_range = self.plotItem.vb.viewRange()[0]
            rel_pos = (
                (center_time - current_range[0]) / (current_range[1] - current_range[0])
                if current_range[1] != current_range[0]
                else 0.5
            )

            # 更新视窗
            self._view_window_ms = new_window
            self._zoom_factor = self.DEFAULT_VIEW_WINDOW_MS / self._view_window_ms

            # 计算新的视窗范围（保持鼠标位置不变）
            new_start = center_time - rel_pos * new_window
            new_end = new_start + new_window

            # 边界检查
            if new_start < 0:
                new_start = 0
                new_end = new_window
            if new_end > self._duration_ms:
                new_end = self._duration_ms
                new_start = max(0, new_end - new_window)

            self.setXRange(new_start, new_end, padding=0)
            self.zoom_changed.emit(self._zoom_factor)

        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton and self._duration_ms > 0:
            # 检查是否按住 Shift 键
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+左键：开始拖动模式
                self._dragging = True
                self._drag_start_pos = event.pos()
                self._drag_start_view = self.plotItem.vb.viewRange()[0]
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
            else:
                # 普通左键：点击跳转
                pos = event.pos()
                view_pos = self.plotItem.vb.mapSceneToView(pos)
                time_ms = int(view_pos.x())
                time_ms = max(0, min(time_ms, self._duration_ms))
                self.position_clicked.emit(time_ms)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件（拖动视窗）"""
        if self._dragging and self._duration_ms > 0:
            # 计算鼠标移动的像素距离
            delta_pos = event.pos() - self._drag_start_pos

            # 将像素距离转换为时间距离
            # 获取当前视窗的像素范围
            view_range = self._drag_start_view
            view_width_ms = view_range[1] - view_range[0]

            # 获取控件宽度
            widget_width = self.width()
            if widget_width <= 0:
                return

            # 计算时间偏移（像素 -> 毫秒）
            ms_per_pixel = view_width_ms / widget_width
            time_offset = delta_pos.x() * ms_per_pixel

            # 计算新的视窗范围
            new_start = self._drag_start_view[0] - time_offset
            new_end = new_start + view_width_ms

            # 边界检查
            if new_start < 0:
                new_start = 0
                new_end = view_width_ms
            if new_end > self._duration_ms:
                new_end = self._duration_ms
                new_start = max(0, new_end - view_width_ms)

            self.setXRange(new_start, new_end, padding=0)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """按键事件（用于检测 Shift 键释放）"""
        # 不需要特殊处理，Shift 状态在鼠标事件中检测
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """按键释放事件"""
        # 如果 Shift 键释放，取消拖动模式
        if event.key() == Qt.Key_Shift and self._dragging:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)
        super().keyReleaseEvent(event)


class WaveformCard(QDockWidget):
    """音频波形卡片

    功能：
    - 主音轨波形显示（pyqtgraph）
    - 红色时间线跟随播放
    - 视窗滑动跟随播放位置
    - 点击跳转到对应时间
    - 滚轮缩放（以鼠标位置为中心）
    - 时间刻度显示
    - 放大倍数显示
    - 打轴功能：I/O 键标记开始/结束点
    - 编辑模式：可视化调整字幕起止点
    - 字幕条覆盖显示（从 SubtitleManager 数据同步）

    信号：
    - position_clicked(ms): 点击波形时发射，用于跳转播放位置
    - subtitle_created(start_ms, end_ms): 打轴完成时发射
    - subtitle_edited(col, old_start, new_start, new_end): 编辑完成时发射
    """

    # 信号
    position_clicked = Signal(int)  # 点击位置 (ms)
    subtitle_created = Signal(int, int)  # 打轴完成 (start_ms, end_ms)
    subtitle_edited = Signal(int, int, int, int)  # 编辑完成 (col, old_start, new_start, new_end)

    # 默认停靠区域
    default_area = Qt.BottomDockWidgetArea

    # 默认视窗宽度（显示的毫秒数）
    DEFAULT_VIEW_WINDOW_MS = 30000  # 30 秒

    def __init__(self, parent=None):
        super().__init__("波形图", parent)
        self._ffmpeg = FFmpeg()
        self._duration_ms = 0
        self._current_position_ms = 0
        self._waveform_data = None  # (times, amplitudes)
        self._temp_wav_path = None
        self._view_window_ms = self.DEFAULT_VIEW_WINDOW_MS

        # 字幕条数据 {start_ms: end_ms}
        self._subtitle_regions: dict[int, int] = {}

        # 打轴状态
        self._mark_start_ms: int = -1  # 标记的开始点，-1 表示未设置

        # 编辑模式状态
        self._edit_mode: bool = False
        self._edit_col: int = -1  # 编辑的字幕轨道
        self._edit_old_start: int = -1  # 编辑前的起始点
        self._edit_start_ms: int = -1  # 编辑中的开始点
        self._edit_end_ms: int = -1  # 编辑中的结束点
        self._edit_which: str = ""  # 正在编辑哪个端点: "start" 或 "end"

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

        # 顶部信息栏
        info_bar = QWidget()
        info_bar.setFixedHeight(24)
        info_bar.setStyleSheet("background: #18181b; border: none;")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(8, 0, 8, 0)

        # 缩放倍数标签
        self._zoom_label = QLabel("1.0x")
        self._zoom_label.setStyleSheet("color: #a1a1aa; font-size: 9pt; font-family: Consolas;")
        self._zoom_label.setFixedWidth(60)

        # 视窗范围标签
        self._range_label = QLabel("0:00 - 0:30")
        self._range_label.setStyleSheet("color: #a1a1aa; font-size: 9pt; font-family: Consolas;")

        # 提示标签
        self._scroll_hint = QLabel("滚轮缩放 | Shift+拖动平移")
        self._scroll_hint.setStyleSheet("color: #52525b; font-size: 8pt;")

        info_layout.addWidget(self._zoom_label)
        info_layout.addWidget(self._range_label)
        info_layout.addStretch()
        info_layout.addWidget(self._scroll_hint)

        layout.addWidget(info_bar)

        # 波形绘图组件
        self._plot_widget = WaveformPlotWidget(parent=self)
        self._plot_widget.position_clicked.connect(self.position_clicked.emit)
        self._plot_widget.zoom_changed.connect(self._on_zoom_changed)
        layout.addWidget(self._plot_widget)

        # 包络线（上半部分填充）
        self._envelope_curve = self._plot_widget.plot(
            pen=pg.mkPen(color=QColor(59, 130, 246, 100), width=1),
            fillLevel=0,
            brush=pg.mkBrush(color=QColor(59, 130, 246, 40)),
        )

        # 波形曲线（细线，叠加在包络上）
        self._waveform_curve = self._plot_widget.plot(pen=pg.mkPen(color="#60a5fa", width=1))

        # 红色时间线
        self._red_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#ef4444", width=1.5),
            movable=False,
        )
        self._plot_widget.addItem(self._red_line)

        # AB 循环区域图层（半透明橙色）
        self._ab_loop_item: pg.PlotCurveItem | None = None
        self._ab_loop_a_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#f59e0b", width=2, style=Qt.DashLine),
            movable=False,
        )
        self._ab_loop_a_line.setVisible(False)
        self._ab_loop_b_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#f59e0b", width=2, style=Qt.DashLine),
            movable=False,
        )
        self._ab_loop_b_line.setVisible(False)
        self._plot_widget.addItem(self._ab_loop_a_line)
        self._plot_widget.addItem(self._ab_loop_b_line)

        # 字幕条图层
        self._subtitle_items: list[pg.PlotCurveItem] = []

        # 打轴标记线（绿色虚线 = 开始点）
        self._mark_start_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#22c55e", width=2, style=Qt.DashLine),
            movable=False,
        )
        self._mark_start_line.setVisible(False)
        self._mark_start_line.setZValue(15)
        self._plot_widget.addItem(self._mark_start_line)

        # 编辑模式标记线
        # 编辑开始线（绿色虚线）
        self._edit_start_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#22c55e", width=2.5, style=Qt.DashLine),
            movable=False,
        )
        self._edit_start_line.setVisible(False)
        self._edit_start_line.setZValue(15)
        self._plot_widget.addItem(self._edit_start_line)

        # 编辑结束线（橙色虚线）
        self._edit_end_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#f59e0b", width=2.5, style=Qt.DashLine),
            movable=False,
        )
        self._edit_end_line.setVisible(False)
        self._edit_end_line.setZValue(15)
        self._plot_widget.addItem(self._edit_end_line)

        # 编辑模式填充区域
        self._edit_fill_item: pg.PlotCurveItem | None = None

        # 底部打轴/编辑按钮栏
        self._mark_bar = QWidget()
        self._mark_bar.setFixedHeight(32)
        self._mark_bar.setStyleSheet("background: #18181b; border: none;")
        mark_layout = QHBoxLayout(self._mark_bar)
        mark_layout.setContentsMargins(8, 0, 8, 0)
        mark_layout.setSpacing(8)

        # 状态标签
        self._mark_status_label = QLabel("就绪")
        self._mark_status_label.setStyleSheet("color: #a1a1aa; font-size: 9pt; font-family: Consolas;")

        # 标记开始按钮
        self._mark_start_btn = QPushButton("标记开始 [I]")
        self._mark_start_btn.setStyleSheet(MARK_BTN_STYLE)
        self._mark_start_btn.setToolTip("标记字幕开始点 (I)")
        self._mark_start_btn.clicked.connect(self._on_mark_start)

        # 标记结束按钮
        self._mark_end_btn = QPushButton("标记结束 [O]")
        self._mark_end_btn.setStyleSheet(MARK_BTN_STYLE)
        self._mark_end_btn.setToolTip("标记字幕结束点 (O)")
        self._mark_end_btn.clicked.connect(self._on_mark_end)

        # 取消标记按钮
        self._mark_cancel_btn = QPushButton("取消")
        self._mark_cancel_btn.setStyleSheet(MARK_BTN_STYLE)
        self._mark_cancel_btn.setToolTip("取消当前打轴标记")
        self._mark_cancel_btn.clicked.connect(self._on_mark_cancel)
        self._mark_cancel_btn.setEnabled(False)

        # 编辑模式按钮（初始隐藏）
        # 设为起点按钮
        self._edit_set_start_btn = QPushButton("设为起点 [I]")
        self._edit_set_start_btn.setStyleSheet("""
            QPushButton {
                background: #16a34a;
                border: 1px solid #22c55e;
                color: #ffffff;
                font-size: 9pt;
                padding: 3px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #22c55e;
            }
        """)
        self._edit_set_start_btn.setToolTip("将当前位置设为起点 (I)")
        self._edit_set_start_btn.clicked.connect(self._on_edit_set_start)
        self._edit_set_start_btn.setVisible(False)

        # 设为终点按钮
        self._edit_set_end_btn = QPushButton("设为终点 [O]")
        self._edit_set_end_btn.setStyleSheet("""
            QPushButton {
                background: #d97706;
                border: 1px solid #f59e0b;
                color: #ffffff;
                font-size: 9pt;
                padding: 3px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #f59e0b;
            }
        """)
        self._edit_set_end_btn.setToolTip("将当前位置设为终点 (O)")
        self._edit_set_end_btn.clicked.connect(self._on_edit_set_end)
        self._edit_set_end_btn.setVisible(False)

        # 确认编辑按钮
        self._edit_confirm_btn = QPushButton("确认")
        self._edit_confirm_btn.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                border: 1px solid #3b82f6;
                color: #ffffff;
                font-size: 9pt;
                padding: 3px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #3b82f6;
            }
        """)
        self._edit_confirm_btn.setToolTip("确认编辑")
        self._edit_confirm_btn.clicked.connect(self._on_edit_confirm)
        self._edit_confirm_btn.setVisible(False)

        # 取消编辑按钮
        self._edit_cancel_btn = QPushButton("取消编辑")
        self._edit_cancel_btn.setStyleSheet(MARK_BTN_STYLE)
        self._edit_cancel_btn.setToolTip("取消编辑，恢复原始值")
        self._edit_cancel_btn.clicked.connect(self._on_edit_cancel)
        self._edit_cancel_btn.setVisible(False)

        mark_layout.addWidget(self._mark_status_label)
        mark_layout.addStretch()

        # 打轴模式按钮
        mark_layout.addWidget(self._mark_start_btn)
        mark_layout.addWidget(self._mark_end_btn)
        mark_layout.addWidget(self._mark_cancel_btn)

        # 编辑模式按钮
        mark_layout.addWidget(self._edit_set_start_btn)
        mark_layout.addWidget(self._edit_set_end_btn)
        mark_layout.addWidget(self._edit_confirm_btn)
        mark_layout.addWidget(self._edit_cancel_btn)

        layout.addWidget(self._mark_bar)

        # 空状态提示
        self._hint_label = QLabel("打开视频后显示音轨波形", content)
        self._hint_label.setAlignment(Qt.AlignCenter)
        self._hint_label.setStyleSheet("""
            QLabel {
                color: #52525b;
                font-size: 10pt;
                background: transparent;
                border: none;
            }
        """)
        self._hint_label.show()

        self.setWidget(content)

    def _on_zoom_changed(self, zoom_factor: float):
        """缩放倍数变化时更新显示"""
        self._zoom_label.setText(f"{zoom_factor:.1f}x")

        # 更新视窗范围标签
        self._update_range_label()

    def _update_range_label(self):
        """更新视窗范围标签"""
        view_range = self._plot_widget.plotItem.vb.viewRange()[0]
        start_ms = int(view_range[0])
        end_ms = int(view_range[1])
        start_str = ms_to_time_str(max(0, start_ms))
        end_str = ms_to_time_str(min(self._duration_ms, end_ms))
        self._range_label.setText(f"{start_str} - {end_str}")

    def resizeEvent(self, event):
        """保持提示标签居中"""
        super().resizeEvent(event)
        if self._hint_label.isVisible():
            parent_size = self.widget().size()
            self._hint_label.setGeometry(0, 0, parent_size.width(), parent_size.height())

    # ========== 公有方法 ==========

    def load_waveform(self, video_path: str) -> bool:
        """加载视频的音频波形

        Args:
            video_path: 视频文件路径

        Returns:
            是否成功加载
        """
        if not os.path.exists(video_path):
            return False

        # 清理旧的临时文件
        self._cleanup_temp_file()

        # 创建临时 WAV 文件
        try:
            fd, self._temp_wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
        except Exception:
            return False

        # 使用 FFmpeg 提取音轨
        success = self._ffmpeg.extract_audio(video_path, self._temp_wav_path, sample_rate=1000)
        if not success:
            self._cleanup_temp_file()
            return False

        # 加载波形数据
        try:
            times, amplitudes = load_waveform(self._temp_wav_path)
            # 直接存储原始数据，显示时再下采样
            self._waveform_data = (times, amplitudes)
            self._update_waveform_plot()
            self._hint_label.hide()
            return True
        except Exception:
            self._cleanup_temp_file()
            return False

    def set_duration(self, duration_ms: int):
        """设置视频总时长"""
        self._duration_ms = duration_ms
        self._plot_widget.set_duration(duration_ms)

        # 更新视窗范围
        if duration_ms > 0:
            view_end = min(self._view_window_ms, duration_ms)
            self._plot_widget.setXRange(0, view_end, padding=0)
            self._update_range_label()

    def update_position(self, position_ms: int):
        """更新播放位置，移动红线和视窗"""
        self._current_position_ms = position_ms

        # 移动红线
        self._red_line.setPos(position_ms)

        # 获取当前视窗范围
        view_range = self._plot_widget.plotItem.vb.viewRange()[0]
        view_start = view_range[0]
        view_end = view_range[1]
        view_width = view_end - view_start

        # 只在播放位置超出视窗范围时才滑动
        if position_ms < view_start or position_ms > view_end:
            # 视窗滑动：保持播放位置在视窗中心
            new_start = max(0, position_ms - view_width / 2)
            new_end = min(self._duration_ms, new_start + view_width)

            # 如果到达末尾，调整起点
            if new_end - new_start < view_width:
                new_start = max(0, new_end - view_width)

            self._plot_widget.setXRange(new_start, new_end, padding=0)
            self._update_range_label()

    def set_subtitle_regions(self, regions: dict[int, int]):
        """设置字幕条覆盖区域

        Args:
            regions: {start_ms: end_ms, ...}
        """
        self._subtitle_regions = regions
        self._update_subtitle_overlay()

    def update_subtitle_overlay_from_data(self, subtitle_data: dict):
        """从 SubtitleManager 数据同步字幕条覆盖

        Args:
            subtitle_data: SubtitleManager.data (dict[int, dict[int, list]])
        """
        regions = {}
        for col, sub_dict in subtitle_data.items():
            for start_ms, (duration_ms, _text) in sub_dict.items():
                end_ms = start_ms + duration_ms
                # 如果该区域已存在，取更大范围
                if start_ms not in regions or end_ms > regions[start_ms]:
                    regions[start_ms] = end_ms
        self._subtitle_regions = regions
        self._update_subtitle_overlay()

    def clear_subtitle_regions(self):
        """清除字幕条覆盖"""
        self._subtitle_regions = {}
        self._update_subtitle_overlay()

    def set_ab_loop_region(self, a_point: int, b_point: int):
        """设置 AB 循环区域显示

        Args:
            a_point: A 点位置（ms），-1 表示未设置
            b_point: B 点位置（ms），-1 表示未设置
        """
        # 移除旧的填充区域
        if self._ab_loop_item is not None:
            self._plot_widget.removeItem(self._ab_loop_item)
            self._ab_loop_item = None

        # 更新 A 点线
        if a_point >= 0:
            self._ab_loop_a_line.setPos(a_point)
            self._ab_loop_a_line.setVisible(True)
        else:
            self._ab_loop_a_line.setVisible(False)

        # 更新 B 点线
        if b_point >= 0:
            self._ab_loop_b_line.setPos(b_point)
            self._ab_loop_b_line.setVisible(True)
        else:
            self._ab_loop_b_line.setVisible(False)

        # 如果两个点都设置了，绘制填充区域
        if a_point >= 0 and b_point >= 0 and a_point < b_point:
            self._draw_ab_loop_region(a_point, b_point)

    def _draw_ab_loop_region(self, a_point: int, b_point: int):
        """绘制 AB 循环填充区域"""
        # 获取 Y 轴范围
        view_range = self._plot_widget.plotItem.vb.viewRange()
        y_min, y_max = view_range[1]

        # 创建半透明橙色填充区域
        x = [a_point, b_point, b_point, a_point, a_point]
        y = [y_min, y_min, y_max, y_max, y_min]

        self._ab_loop_item = pg.PlotCurveItem(
            x=x,
            y=y,
            fillLevel=0,
            brush=pg.mkBrush(color=QColor(245, 158, 11, 30)),  # 半透明橙色
            pen=pg.mkPen(color=QColor(245, 158, 11, 0), width=0),  # 无边框
        )
        self._plot_widget.addItem(self._ab_loop_item)

        # 确保 AB 线在填充区域之上
        self._ab_loop_a_line.setZValue(10)
        self._ab_loop_b_line.setZValue(10)
        self._red_line.setZValue(20)

    # ========== 打轴功能 ==========

    def mark_start(self):
        """标记字幕开始点（使用当前播放位置）"""
        # 如果在编辑模式，调用编辑模式的方法
        if self._edit_mode:
            self.edit_set_start()
            return

        if self._duration_ms <= 0:
            return
        self._mark_start_ms = self._current_position_ms
        self._mark_start_line.setPos(self._mark_start_ms)
        self._mark_start_line.setVisible(True)

        # 更新 UI 状态
        self._mark_start_btn.setStyleSheet(MARK_ACTIVE_STYLE)
        self._mark_start_btn.setText(f"开始: {ms_to_time_str(self._mark_start_ms)}")
        self._mark_cancel_btn.setEnabled(True)
        self._mark_status_label.setText(f"标记开始: {ms_to_time_str(self._mark_start_ms)}，按 O 标记结束")

    def mark_end(self):
        """标记字幕结束点（使用当前播放位置），完成打轴"""
        # 如果在编辑模式，调用编辑模式的方法
        if self._edit_mode:
            self.edit_set_end()
            return

        if self._duration_ms <= 0:
            return
        if self._mark_start_ms < 0:
            self._mark_status_label.setText("请先按 I 标记开始点")
            return

        end_ms = self._current_position_ms
        start_ms = self._mark_start_ms

        # 确保 start < end
        if end_ms <= start_ms:
            self._mark_status_label.setText("结束点必须在开始点之后")
            return

        # 发射打轴完成信号
        self.subtitle_created.emit(start_ms, end_ms)

        # 清除标记状态
        self._clear_mark_state()
        self._mark_status_label.setText(f"已打轴: {ms_to_time_str(start_ms)} - {ms_to_time_str(end_ms)}")

    def cancel_marking(self):
        """取消当前打轴标记"""
        self._clear_mark_state()
        self._mark_status_label.setText("已取消标记")

    def _clear_mark_state(self):
        """清除打轴标记状态"""
        self._mark_start_ms = -1
        self._mark_start_line.setVisible(False)
        self._mark_start_btn.setStyleSheet(MARK_BTN_STYLE)
        self._mark_start_btn.setText("标记开始 [I]")
        self._mark_cancel_btn.setEnabled(False)

    def _on_mark_start(self):
        """标记开始按钮点击"""
        self.mark_start()

    def _on_mark_end(self):
        """标记结束按钮点击"""
        self.mark_end()

    def _on_mark_cancel(self):
        """取消标记按钮点击"""
        self.cancel_marking()

    def get_mark_start(self) -> int:
        """获取当前标记的开始点，-1 表示未设置"""
        return self._mark_start_ms

    # ========== 编辑模式 ==========

    def enter_edit_mode(self, col: int, start_ms: int, end_ms: int):
        """进入编辑模式，可视化调整字幕起止点

        Args:
            col: 字幕轨道号
            start_ms: 当前开始时间 (ms)
            end_ms: 当前结束时间 (ms)
        """
        if self._duration_ms <= 0:
            return

        # 如果正在打轴，先取消
        if self._mark_start_ms >= 0:
            self._clear_mark_state()

        self._edit_mode = True
        self._edit_col = col
        self._edit_old_start = start_ms
        self._edit_start_ms = start_ms
        self._edit_end_ms = end_ms
        self._edit_which = "start"  # 默认先编辑起点

        # 更新可视化
        self._update_edit_lines()

        # 切换按钮显示
        self._set_mark_buttons_visible(False)
        self._set_edit_buttons_visible(True)

        # 更新状态提示
        self._mark_status_label.setText(
            f"编辑模式: {ms_to_time_str(start_ms)} - {ms_to_time_str(end_ms)}  |  按 I 设起点，按 O 设终点，Enter 确认"
        )

        # 视窗跳转到编辑区域
        self._scroll_to_edit_area()

    def exit_edit_mode(self):
        """退出编辑模式"""
        self._edit_mode = False
        self._edit_col = -1
        self._edit_old_start = -1
        self._edit_start_ms = -1
        self._edit_end_ms = -1
        self._edit_which = ""

        # 隐藏编辑可视化
        self._edit_start_line.setVisible(False)
        self._edit_end_line.setVisible(False)
        self._clear_edit_fill()

        # 切换按钮显示
        self._set_edit_buttons_visible(False)
        self._set_mark_buttons_visible(True)

        self._mark_status_label.setText("就绪")

    def edit_set_start(self):
        """编辑模式：将当前位置设为起点"""
        if not self._edit_mode:
            return

        new_start = self._current_position_ms
        # 确保起点在终点之前
        if new_start >= self._edit_end_ms:
            self._mark_status_label.setText("起点必须在终点之前")
            return

        self._edit_start_ms = new_start
        self._update_edit_lines()
        self._mark_status_label.setText(
            f"起点已更新: {ms_to_time_str(self._edit_start_ms)} - {ms_to_time_str(self._edit_end_ms)}  |  "
            f"按 O 设终点，Enter 确认"
        )

    def edit_set_end(self):
        """编辑模式：将当前位置设为终点"""
        if not self._edit_mode:
            return

        new_end = self._current_position_ms
        # 确保终点在起点之后
        if new_end <= self._edit_start_ms:
            self._mark_status_label.setText("终点必须在起点之后")
            return

        self._edit_end_ms = new_end
        self._update_edit_lines()
        self._mark_status_label.setText(
            f"终点已更新: {ms_to_time_str(self._edit_start_ms)} - {ms_to_time_str(self._edit_end_ms)}  |  "
            f"按 I 设起点，Enter 确认"
        )

    def edit_confirm(self):
        """确认编辑，发射信号"""
        if not self._edit_mode:
            return

        # 发射编辑完成信号
        self.subtitle_edited.emit(
            self._edit_col,
            self._edit_old_start,
            self._edit_start_ms,
            self._edit_end_ms,
        )

        self._mark_status_label.setText(
            f"已更新: {ms_to_time_str(self._edit_start_ms)} - {ms_to_time_str(self._edit_end_ms)}"
        )
        self.exit_edit_mode()

    def edit_cancel(self):
        """取消编辑"""
        self._mark_status_label.setText("已取消编辑")
        self.exit_edit_mode()

    def is_in_edit_mode(self) -> bool:
        """是否在编辑模式"""
        return self._edit_mode

    def _update_edit_lines(self):
        """更新编辑模式的可视化线条"""
        self._edit_start_line.setPos(self._edit_start_ms)
        self._edit_start_line.setVisible(True)

        self._edit_end_line.setPos(self._edit_end_ms)
        self._edit_end_line.setVisible(True)

        # 更新填充区域
        self._draw_edit_fill()

    def _draw_edit_fill(self):
        """绘制编辑模式的填充区域"""
        self._clear_edit_fill()

        if self._edit_start_ms < 0 or self._edit_end_ms < 0:
            return

        # 获取 Y 轴范围
        y_range = self._plot_widget.plotItem.vb.viewRange()[1]
        y_min, y_max = y_range

        # 创建半透明紫色填充区域（区分于打轴的蓝色和 AB 循环的橙色）
        x = [self._edit_start_ms, self._edit_end_ms, self._edit_end_ms, self._edit_start_ms, self._edit_start_ms]
        y = [y_min, y_min, y_max, y_max, y_min]

        self._edit_fill_item = pg.PlotCurveItem(
            x=x,
            y=y,
            fillLevel=0,
            brush=pg.mkBrush(color=QColor(139, 92, 246, 30)),  # 半透明紫色
            pen=pg.mkPen(color=QColor(139, 92, 246, 60), width=1),
        )
        self._plot_widget.addItem(self._edit_fill_item)

        # 确保线条在填充之上
        self._edit_start_line.setZValue(15)
        self._edit_end_line.setZValue(15)
        self._red_line.setZValue(20)

    def _clear_edit_fill(self):
        """清除编辑模式的填充区域"""
        if self._edit_fill_item is not None:
            self._plot_widget.removeItem(self._edit_fill_item)
            self._edit_fill_item = None

    def _scroll_to_edit_area(self):
        """视窗跳转到编辑区域"""
        # 让编辑区域居中显示，左右各留 20% 的空间
        center = (self._edit_start_ms + self._edit_end_ms) / 2
        half_window = self._view_window_ms / 2

        new_start = max(0, center - half_window)
        new_end = min(self._duration_ms, center + half_window)

        # 调整边界
        if new_end - new_start < self._view_window_ms:
            if new_start == 0:
                new_end = min(self._duration_ms, self._view_window_ms)
            else:
                new_start = max(0, new_end - self._view_window_ms)

        self._plot_widget.setXRange(new_start, new_end, padding=0)
        self._update_range_label()

    def _set_mark_buttons_visible(self, visible: bool):
        """设置打轴模式按钮可见性"""
        self._mark_start_btn.setVisible(visible)
        self._mark_end_btn.setVisible(visible)
        self._mark_cancel_btn.setVisible(visible and self._mark_start_ms >= 0)

    def _set_edit_buttons_visible(self, visible: bool):
        """设置编辑模式按钮可见性"""
        self._edit_set_start_btn.setVisible(visible)
        self._edit_set_end_btn.setVisible(visible)
        self._edit_confirm_btn.setVisible(visible)
        self._edit_cancel_btn.setVisible(visible)

    def _on_edit_set_start(self):
        """设为起点按钮点击"""
        self.edit_set_start()

    def _on_edit_set_end(self):
        """设为终点按钮点击"""
        self.edit_set_end()

    def _on_edit_confirm(self):
        """确认编辑按钮点击"""
        self.edit_confirm()

    def _on_edit_cancel(self):
        """取消编辑按钮点击"""
        self.edit_cancel()

    # ========== 内部方法 ==========

    def _update_waveform_plot(self):
        """更新波形曲线显示"""
        if self._waveform_data is None:
            return

        times, amplitudes = self._waveform_data

        # 下采样波形（保留峰值，减少数据点到 5000）
        ds_times, ds_amps = downsample_waveform(times, amplitudes, target_points=5000)

        # 计算包络线（快速版本，窗口 50 个采样点）
        upper, lower = compute_envelope_fast(amplitudes, window=50, target_points=5000)

        # 包络线只显示上半部分（绝对值形式），用 fillLevel=0 填充
        self._envelope_curve.setData(ds_times, upper)

        # 波形曲线使用下采样后的数据
        self._waveform_curve.setData(ds_times, ds_amps)

        # 设置 Y 轴范围（让波形更居中）
        max_envelope = max(upper) if upper else 0
        if max_envelope > 0:
            # 上下各留 15% 的空间，让波形居中显示
            margin = max_envelope * 0.15
            self._plot_widget.setYRange(-max_envelope - margin, max_envelope + margin, padding=0)

    def _update_subtitle_overlay(self):
        """更新字幕条覆盖显示"""
        # 清除旧的字幕条
        for item in self._subtitle_items:
            self._plot_widget.removeItem(item)
        self._subtitle_items.clear()

        # 绘制新的字幕条
        for start_ms, end_ms in self._subtitle_regions.items():
            self._draw_subtitle_region(start_ms, end_ms)

    def _draw_subtitle_region(self, start_ms: int, end_ms: int):
        """绘制单个字幕条区域"""
        # 获取 Y 轴范围
        y_range = self._plot_widget.plotItem.vb.viewRange()[1]
        y_min, y_max = y_range

        # 判断是否是正在编辑的字幕条
        is_editing = self._edit_mode and start_ms == self._edit_old_start

        # 根据状态选择颜色
        duration = end_ms - start_ms
        if is_editing:
            # 正在编辑：紫色高亮
            fill_color = QColor(139, 92, 246, 60)
            border_color = QColor(139, 92, 246, 120)
        elif duration < 100 or duration > 8000:
            # 异常：红色
            fill_color = QColor(178, 34, 34, 50)
            border_color = QColor(178, 34, 34, 100)
        elif duration > 4500:
            # 过长：橙色
            fill_color = QColor(250, 128, 114, 40)
            border_color = QColor(250, 128, 114, 80)
        else:
            # 正常：蓝色
            fill_color = QColor(59, 130, 246, 40)
            border_color = QColor(59, 130, 246, 80)

        # 创建半透明色块
        x = [start_ms, end_ms, end_ms, start_ms, start_ms]
        y = [y_min, y_min, y_max, y_max, y_min]

        item = pg.PlotCurveItem(
            x=x,
            y=y,
            fillLevel=0,
            brush=pg.mkBrush(color=fill_color),
            pen=pg.mkPen(color=border_color, width=2 if is_editing else 1),
        )
        self._plot_widget.addItem(item)
        self._subtitle_items.append(item)

    def _cleanup_temp_file(self):
        """清理临时 WAV 文件"""
        if self._temp_wav_path and os.path.exists(self._temp_wav_path):
            try:
                os.unlink(self._temp_wav_path)
            except Exception:
                pass
            self._temp_wav_path = None

    def closeEvent(self, event):
        """关闭时清理资源"""
        self._cleanup_temp_file()
        super().closeEvent(event)
