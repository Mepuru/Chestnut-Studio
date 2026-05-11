"""打轴编辑卡片模块

功能：
- 显示已打轴的字幕列表（编号 + 轨道 + 起止时间 + 时长 + 操作按钮）
- 提供查看、编辑、锁定、删除功能
- 支持批量删除
- 支持撤销/重做
- 与音频波形区联动
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.subtitle import SubtitleEntry, SubtitleManager
from chestnut_studio.core.track_config import (
    TRACK_COLORS_HEX,
    get_effective_track_count,
    get_track_color,
)
from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.registry import register_card
from chestnut_studio.utils.log_manager import LogManager
from chestnut_studio.utils.time_utils import ms_to_time_str

# 操作按钮样式
OP_BTN_STYLE = """
    QPushButton {
        background: transparent;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        font-size: 8pt;
        padding: 1px 4px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background: #3f3f46;
    }
    QPushButton:pressed {
        background: #27272a;
    }
"""

# 锁定按钮激活样式
LOCK_ACTIVE_STYLE = """
    QPushButton {
        background: #f59e0b;
        border: 1px solid #fbbf24;
        color: #000000;
        font-size: 8pt;
        padding: 1px 4px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background: #fbbf24;
    }
"""

# 底部工具栏按钮样式
TOOL_BTN_STYLE = """
    QPushButton {
        background: #27272a;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        font-size: 9pt;
        padding: 2px 8px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background: #3f3f46;
    }
    QPushButton:pressed {
        background: #18181b;
    }
    QPushButton:disabled {
        color: #52525b;
        background: #1e1e22;
    }
"""


@register_card
class TimelineCard(BaseCard):
    """打轴编辑卡片

    功能：
    - 显示已打轴的字幕列表（编号 + 轨道 + 起止时间 + 时长 + 操作按钮）
    - 查看：跳转到字幕起始点
    - 编辑：在波形图上可视化调整区间
    - 锁定：切换锁定状态
    - 删除：删除单条或多条字幕
    - 撤销/重做

    信号：
    - jump_to_position(ms): 跳转到指定位置
    - subtitle_changed(): 字幕数据变化（用于同步波形覆盖）
    - subtitle_selected(col, start_ms): 字幕被选中（用于翻译面板）
    - edit_subtitle_requested(col, start_ms, end_ms): 请求编辑字幕（发射到波形图）
    """

    # ── BaseCard 必需属性 ──
    card_id = "timeline"
    card_title = "时间轴"
    default_area = Qt.RightDockWidgetArea
    default_ratio = 0.56

    # ── 信号 ──
    jump_to_position = Signal(int)  # 跳转到指定位置 (ms)
    subtitle_changed = Signal()  # 字幕数据变化
    subtitle_selected = Signal(int, int)  # 字幕被选中 (col, start_ms)
    edit_subtitle_requested = Signal(int, int, int)  # 请求编辑 (col, start_ms, end_ms)

    def on_init(self) -> None:
        """自定义初始化"""
        self._subtitle_mgr = SubtitleManager()
        self._duration_ms = 0
        self._fps = 30.0  # 默认帧率

        # 锁定状态集合 {(col, start_ms), ...}
        self._locked_states: set[tuple[int, int]] = set()

        # 轨道筛选 (-1 = 全部，1-4 = 指定轨道)
        self._filter_track: int = -1

        # 缓存轨道颜色（避免每次表格重建时重复创建 QColor）
        self._track_colors_fg = [QColor(c) for c in TRACK_COLORS_HEX]
        self._track_colors_bg = []
        for c in TRACK_COLORS_HEX:
            qc = QColor(c)
            qc.setAlpha(30)
            self._track_colors_bg.append(qc)

        # 撤销/重做后端
        # 栈保存每个操作完成后状态快照，point 指向当前状态
        self._backend: list[tuple[dict, set]] = []
        self._backend_point: int = -1

        # 初始化撤销栈，保存初始状态
        self._push_undo()

    def listens_to(self) -> dict[str, str]:
        """声明本卡片关心的外部信号"""
        return {
            "player.duration_changed": "set_duration",
        }

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

        # --- 字幕列表表格 ---
        self._table = QTableWidget(0, 9, self)
        self._table.setStyleSheet("""
            QTableWidget {
                background: #0f0f14;
                color: #e4e4e7;
                gridline-color: #27272a;
                font-size: 9pt;
                selection-background-color: rgba(37, 99, 235, 0.3);
                border: none;
            }
            QTableWidget::item {
                padding: 2px;
                border: none;
            }
            QTableWidget::item:selected {
                background: rgba(37, 99, 235, 0.3);
            }
            QHeaderView::section {
                background: #18181b;
                color: #a1a1aa;
                border: none;
                border-right: 1px solid #27272a;
                border-bottom: 1px solid #27272a;
                padding: 4px;
                font-size: 8pt;
            }
        """)

        # 设置表格属性
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.NoSelection)  # 默认禁用选择，仅翻译区域高亮时启用

        # 设置列头 - 使用 Stretch 模式自动调整列宽
        self._table.setHorizontalHeaderLabels(["#", "轨道", "开始时间", "结束时间", "开始帧", "结束帧", "时长", "文本", "操作"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self._table.setColumnWidth(0, 40)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self._table.setColumnWidth(1, 65)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        header.setSectionResizeMode(8, QHeaderView.Fixed)
        self._table.setColumnWidth(8, 170)

        # 隐藏垂直表头
        self._table.verticalHeader().setVisible(False)

        # 双击跳转
        self._table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self._table)

        # --- 底部工具栏 ---
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(32)
        bottom_bar.setStyleSheet("background: #18181b; border: none;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(8, 0, 8, 0)
        bottom_layout.setSpacing(6)

        # 字幕总数
        self._count_label = QLabel("共 0 条")
        self._count_label.setStyleSheet("color: #a1a1aa; font-size: 9pt;")

        # 撤销/重做按钮
        self._undo_btn = QPushButton("撤销")
        self._undo_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._undo_btn.setToolTip("撤销 (Ctrl+Z)")
        self._undo_btn.clicked.connect(self._undo)
        self._undo_btn.setEnabled(False)

        self._redo_btn = QPushButton("重做")
        self._redo_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._redo_btn.setToolTip("重做 (Ctrl+Y)")
        self._redo_btn.clicked.connect(self._redo)
        self._redo_btn.setEnabled(False)

        self._delete_all_btn = QPushButton("清空")
        self._delete_all_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._delete_all_btn.setToolTip("清空当前轨道所有字幕")
        self._delete_all_btn.clicked.connect(self._delete_all_current_track)

        # 全部锁定/解锁按钮
        self._lock_all_btn = QPushButton("全部锁定")
        self._lock_all_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._lock_all_btn.clicked.connect(self._lock_all)

        self._unlock_all_btn = QPushButton("全部解锁")
        self._unlock_all_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._unlock_all_btn.clicked.connect(self._unlock_all)

        # 预览按钮
        self._preview_btn = QPushButton("预览")
        self._preview_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._preview_btn.setToolTip("预览所有轨道叠加效果")
        self._preview_btn.clicked.connect(self._preview_tracks)

        # 复制轴功能
        copy_label = QLabel("复制:")
        copy_label.setStyleSheet("color: #a1a1aa; font-size: 9pt;")

        self._copy_source_combo = QComboBox()
        self._copy_source_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        for i, color in enumerate(TRACK_COLORS_HEX):
            self._copy_source_combo.addItem(f"轨道 {i + 1}")
            self._copy_source_combo.setItemData(i, QColor(color), Qt.ForegroundRole)
        self._copy_source_combo.setCurrentIndex(0)

        copy_arrow = QLabel("→")
        copy_arrow.setStyleSheet("color: #a1a1aa; font-size: 9pt;")

        self._copy_target_combo = QComboBox()
        self._copy_target_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        for i, color in enumerate(TRACK_COLORS_HEX):
            self._copy_target_combo.addItem(f"轨道 {i + 1}")
            self._copy_target_combo.setItemData(i, QColor(color), Qt.ForegroundRole)
        self._copy_target_combo.setCurrentIndex(1)

        self._copy_track_btn = QPushButton("复制轴")
        self._copy_track_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._copy_track_btn.setToolTip("将源轨道的字幕复制到目标轨道")
        self._copy_track_btn.clicked.connect(self._copy_track)

        # 轨道筛选器
        filter_label = QLabel("显示:")
        filter_label.setStyleSheet("color: #a1a1aa; font-size: 9pt;")

        self._track_filter = QComboBox()
        self._track_filter.setFixedWidth(80)
        self._track_filter.addItem("全部")
        for i, color in enumerate(TRACK_COLORS_HEX):
            self._track_filter.addItem(f"轨道 {i + 1}")
            self._track_filter.setItemData(i + 1, QColor(color), Qt.ForegroundRole)
        self._track_filter.setCurrentIndex(0)
        self._track_filter.currentIndexChanged.connect(self._on_track_filter_changed)

        bottom_layout.addWidget(self._count_label)
        bottom_layout.addSpacing(8)
        bottom_layout.addWidget(filter_label)
        bottom_layout.addWidget(self._track_filter)
        bottom_layout.addStretch()
        bottom_layout.addWidget(copy_label)
        bottom_layout.addWidget(self._copy_source_combo)
        bottom_layout.addWidget(copy_arrow)
        bottom_layout.addWidget(self._copy_target_combo)
        bottom_layout.addWidget(self._copy_track_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self._undo_btn)
        bottom_layout.addWidget(self._redo_btn)
        bottom_layout.addWidget(self._delete_all_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self._lock_all_btn)
        bottom_layout.addWidget(self._unlock_all_btn)
        bottom_layout.addWidget(self._preview_btn)

        layout.addWidget(bottom_bar)

        self.setWidget(content)

    # ========== 表格更新 ==========

    def _update_table(self):
        """更新字幕列表表格"""
        # 记住当前选中行和滚动位置
        selected_row = -1
        selected_items = self._table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
        scroll_pos = self._table.verticalScrollBar().value()

        self._table.setRowCount(0)

        # 收集字幕条（根据筛选条件）
        all_subtitles: list[tuple[int, int, int, str]] = []  # (start, duration, col, text)
        for col, sub_data in self._subtitle_mgr.data.items():
            # 轨道筛选
            if self._filter_track >= 0 and col != self._filter_track:
                continue
            for start, (duration, text) in sub_data.items():
                all_subtitles.append((start, duration, col, text))

        # 按开始时间排序
        all_subtitles.sort(key=lambda x: x[0])

        # 填充表格
        for idx, (start, duration, col, text) in enumerate(all_subtitles):
            row = self._table.rowCount()
            self._table.insertRow(row)

            is_locked = (col, start) in self._locked_states

            # 列（编号）
            num_item = QTableWidgetItem(str(idx + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setData(Qt.UserRole, (col, start))
            self._table.setItem(row, 0, num_item)

            # 轨道列
            track_item = QTableWidgetItem(f"轨道 {col}")
            track_item.setTextAlignment(Qt.AlignCenter)
            track_item.setData(Qt.UserRole + 1, col)
            col_idx = max(0, min(col - 1, len(self._track_colors_fg) - 1))
            track_item.setForeground(self._track_colors_fg[col_idx])
            self._table.setItem(row, 1, track_item)

            # 开始时间
            start_item = QTableWidgetItem(ms_to_time_str(start))
            start_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, start_item)

            # 结束时间
            end_item = QTableWidgetItem(ms_to_time_str(start + duration))
            end_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, end_item)

            # 开始帧
            start_frame = int(start * self._fps / 1000)
            start_frame_item = QTableWidgetItem(str(start_frame))
            start_frame_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 4, start_frame_item)

            # 结束帧
            end_frame = int((start + duration) * self._fps / 1000)
            end_frame_item = QTableWidgetItem(str(end_frame))
            end_frame_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 5, end_frame_item)

            # 时长
            duration_item = QTableWidgetItem(f"{duration / 1000:.2f}s")
            duration_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 6, duration_item)

            # 文本
            text_display = text.replace("\n", " ") if text else ""
            text_item = QTableWidgetItem(text_display)
            text_item.setToolTip(text if text else "")
            self._table.setItem(row, 7, text_item)

            # 操作按钮
            op_widget = self._create_operation_buttons(col, start, is_locked)
            self._table.setCellWidget(row, 8, op_widget)

            # 设置行颜色
            if is_locked:
                bg_color = QColor(255, 255, 255, 15)  # 锁定时微亮
            elif duration < 100 or duration > 8000:
                bg_color = QColor(178, 34, 34, 40)  # 异常：红色
            else:
                col_idx = max(0, min(col - 1, len(self._track_colors_bg) - 1))
                bg_color = self._track_colors_bg[col_idx]

            for c in range(9):
                item = self._table.item(row, c)
                if item:
                    item.setBackground(bg_color)

        # 恢复选中
        if selected_row >= 0 and selected_row < self._table.rowCount():
            self._table.selectRow(selected_row)

        # 恢复滚动位置
        self._table.verticalScrollBar().setValue(scroll_pos)

        # 更新计数和按钮状态
        self._count_label.setText(f"共 {len(all_subtitles)} 条")
        self._update_undo_redo_buttons()

    def _create_operation_buttons(self, col: int, start: int, is_locked: bool) -> QWidget:
        """创建操作按钮组（查看 / 编辑 / 锁定 / 删除）"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # 查看按钮
        view_btn = QPushButton("查看")
        view_btn.setStyleSheet(OP_BTN_STYLE)
        view_btn.setToolTip("跳转到字幕起始点")
        view_btn.setFixedSize(32, 22)
        view_btn.clicked.connect(lambda checked, s=start: self._on_view_clicked(s))
        layout.addWidget(view_btn)

        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet(OP_BTN_STYLE)
        edit_btn.setToolTip("编辑字幕区间")
        edit_btn.setFixedSize(32, 22)
        edit_btn.clicked.connect(lambda checked, c=col, s=start: self._on_edit_clicked(c, s))
        layout.addWidget(edit_btn)

        # 锁定按钮
        lock_btn = QPushButton("锁定" if not is_locked else "解锁")
        lock_btn.setStyleSheet(LOCK_ACTIVE_STYLE if is_locked else OP_BTN_STYLE)
        lock_btn.setToolTip("切换锁定状态")
        lock_btn.setFixedSize(32, 22)
        lock_btn.clicked.connect(lambda checked, c=col, s=start: self._on_lock_clicked(c, s))
        layout.addWidget(lock_btn)

        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #3f3f46;
                color: #ef4444;
                font-size: 8pt;
                padding: 1px 4px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #ef4444;
                color: #ffffff;
            }
        """)
        delete_btn.setToolTip("删除此字幕")
        delete_btn.setFixedSize(32, 22)
        delete_btn.clicked.connect(lambda checked, c=col, s=start: self._on_delete_single(c, s))
        layout.addWidget(delete_btn)

        layout.addStretch()
        return widget

    # ========== 操作回调 ==========

    def _on_view_clicked(self, start_ms: int):
        """查看按钮：跳转到字幕起始点"""
        self.jump_to_position.emit(start_ms)

    def _on_edit_clicked(self, col: int, start_ms: int):
        """编辑按钮：发射信号到波形图进行可视化编辑"""
        if (col, start_ms) in self._locked_states:
            return  # 锁定状态不可编辑

        subtitle = self._subtitle_mgr.get(col, start_ms)
        if subtitle is None:
            return

        duration = subtitle.duration_ms
        end_ms = start_ms + duration

        # 发射编辑请求信号，让波形图进入编辑模式
        self.edit_subtitle_requested.emit(col, start_ms, end_ms)

    def _on_lock_clicked(self, col: int, start_ms: int):
        """锁定按钮：切换锁定状态"""
        key = (col, start_ms)
        if key in self._locked_states:
            self._locked_states.discard(key)
        else:
            self._locked_states.add(key)
        # 锁定操作也需要保存到撤销栈
        self._push_undo()
        self._update_table()

    def _on_delete_single(self, col: int, start_ms: int):
        """删除单条字幕"""
        if (col, start_ms) in self._locked_states:
            return  # 锁定状态不可删除

        subtitle = self._subtitle_mgr.get(col, start_ms)
        if subtitle is None:
            return

        self._push_undo()
        self._subtitle_mgr.delete(col, start_ms)
        self._locked_states.discard((col, start_ms))
        self._update_table()
        self.subtitle_changed.emit()

    def _on_double_click(self, index):
        """双击行：跳转到字幕起始点"""
        row = index.row()
        num_item = self._table.item(row, 0)
        if num_item:
            data = num_item.data(Qt.UserRole)
            if data:
                col, start = data
                self.jump_to_position.emit(start)
                self.subtitle_selected.emit(col, start)

    def _on_track_filter_changed(self, index: int):
        """轨道筛选变化"""
        self._filter_track = -1 if index == 0 else index  # 0=全部(-1), 1-4=指定轨道
        self._update_table()

    # ========== 删除功能 ==========

    def _delete_selected(self):
        """删除选中的字幕"""
        selected_rows = set()
        for item in self._table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            return

        # 收集要删除的字幕
        to_delete = []
        for row in selected_rows:
            num_item = self._table.item(row, 0)
            if num_item:
                data = num_item.data(Qt.UserRole)
                if data:
                    col, start = data
                    if (col, start) not in self._locked_states:
                        to_delete.append((col, start))

        if not to_delete:
            return

        # 确认删除
        if len(to_delete) > 1:
            reply = QMessageBox.question(
                self, "批量删除", f"确定要删除选中的 {len(to_delete)} 条字幕吗？", QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # 执行删除
        self._push_undo()
        for col, start in to_delete:
            self._subtitle_mgr.delete(col, start)
            self._locked_states.discard((col, start))

        self._update_table()
        self.subtitle_changed.emit()

    def _delete_all_current_track(self):
        """清空当前轨道所有字幕（需要外部传入当前轨道号）"""
        # 这个方法需要与 WaveformCard 的当前轨道联动
        # 暂时清空所有轨道
        reply = QMessageBox.question(
            self, "清空字幕", "确定要清空所有字幕吗？此操作不可撤销。", QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self._push_undo()
        self._subtitle_mgr.clear_all()
        self._locked_states.clear()
        self._update_table()
        self.subtitle_changed.emit()

    def delete_by_track(self, track: int):
        """删除指定轨道的所有字幕"""
        if track < 0:
            return

        sub_data = self._subtitle_mgr.data.get(track, {})
        if not sub_data:
            return

        reply = QMessageBox.question(
            self, "清空轨道", f"确定要清空轨道 {track} 的所有字幕吗？", QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self._push_undo()
        self._subtitle_mgr.clear(track)
        # 清除该轨道的锁定状态
        to_remove = [(c, s) for c, s in self._locked_states if c == track]
        for key in to_remove:
            self._locked_states.discard(key)

        self._update_table()
        self.subtitle_changed.emit()

    def _preview_tracks(self):
        """预览所有轨道叠加效果"""
        # 发射预览信号或打开预览对话框
        logger = LogManager.instance().get_logger("Timeline")
        logger.info("===== 轨道预览 =====")
        max_track = self._subtitle_mgr.get_max_track()
        for col in range(1, max_track + 1):
            sub_data = self._subtitle_mgr.data.get(col, {})
            if sub_data:
                logger.info(f"轨道 {col}: {len(sub_data)} 条")
                for start, (duration, text) in sorted(sub_data.items()):
                    logger.info(f"  {ms_to_time_str(start)} - {ms_to_time_str(start + duration)}: {text or '(无文本)'}")
        logger.info("===================")

    def _copy_track(self):
        """复制轨道字幕到另一个轨道"""
        source_col = self._copy_source_combo.currentIndex() + 1  # combo index 0 = track 1
        target_col = self._copy_target_combo.currentIndex() + 1

        if source_col == target_col:
            QMessageBox.warning(self, "复制失败", "源轨道和目标轨道不能相同")
            return

        # 检查源轨道是否有数据
        source_data = self._subtitle_mgr.data.get(source_col, {})
        if not source_data:
            QMessageBox.warning(self, "复制失败", f"轨道 {source_col} 没有字幕数据")
            return

        # 检查目标轨道是否有数据
        target_data = self._subtitle_mgr.data.get(target_col, {})
        if target_data:
            reply = QMessageBox.question(
                self,
                "确认复制",
                f"轨道 {target_col} 已有字幕数据，复制将覆盖现有数据。确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # 执行复制
        self._push_undo()
        success = self._subtitle_mgr.copy_track(source_col, target_col)

        if success:
            self._update_table()
            self.subtitle_changed.emit()
            QMessageBox.information(
                self,
                "复制成功",
                f"已将轨道 {source_col} 的 {len(source_data)} 条字幕复制到轨道 {target_col}",
            )
        else:
            QMessageBox.warning(self, "复制失败", "复制过程中发生错误")

    # ========== 撤销/重做 ==========

    def _push_undo(self):
        """保存当前状态到撤销栈（在操作完成后调用）"""
        # SubtitleEntry 是不可变的 NamedTuple，浅拷贝内层 dict 即可
        data_snapshot = {col: dict(entries) for col, entries in self._subtitle_mgr.data.items()}
        state = (
            data_snapshot,
            self._locked_states.copy(),  # set of tuple，浅拷贝足够
        )
        # 截断当前位置之后的栈（丢弃重做历史）
        self._backend = self._backend[: self._backend_point + 1]
        self._backend.append(state)
        self._backend_point = len(self._backend) - 1
        # 限制栈大小
        if len(self._backend) > 100:
            self._backend.pop(0)
            self._backend_point -= 1
        self._update_undo_redo_buttons()

    def _undo(self):
        """撤销"""
        if self._backend_point > 0:
            self._backend_point -= 1
            data, locked = self._backend[self._backend_point]
            # 恢复快照需要深拷贝，防止后续操作修改快照内容
            self._subtitle_mgr._data = {col: dict(entries) for col, entries in data.items()}
            self._locked_states = set(locked)
            self._update_table()
            self.subtitle_changed.emit()

    def _redo(self):
        """重做"""
        if self._backend_point < len(self._backend) - 1:
            self._backend_point += 1
            data, locked = self._backend[self._backend_point]
            # 恢复快照需要深拷贝，防止后续操作修改快照内容
            self._subtitle_mgr._data = {col: dict(entries) for col, entries in data.items()}
            self._locked_states = set(locked)
            self._update_table()
            self.subtitle_changed.emit()

    def _update_undo_redo_buttons(self):
        """更新撤销/重做按钮状态"""
        self._undo_btn.setEnabled(self._backend_point > 0)
        self._redo_btn.setEnabled(self._backend_point < len(self._backend) - 1)

    # ========== 全部锁定/解锁 ==========

    def _lock_all(self):
        """锁定所有字幕"""
        for col, sub_data in self._subtitle_mgr.data.items():
            for start in sub_data:
                self._locked_states.add((col, start))
        self._push_undo()
        self._update_table()

    def _unlock_all(self):
        """解锁所有字幕"""
        self._locked_states.clear()
        self._push_undo()
        self._update_table()

    # ========== 快捷键 ==========

    def keyPressEvent(self, event):
        """处理快捷键"""
        key = event.key()
        modifiers = event.modifiers()

        if modifiers == Qt.ControlModifier and key == Qt.Key_Z:
            self._undo()
            event.accept()
            return
        elif modifiers == Qt.ControlModifier and key == Qt.Key_Y:
            self._redo()
            event.accept()
            return
        elif key == Qt.Key_Delete:
            self._delete_selected()
            event.accept()
            return

        super().keyPressEvent(event)

    # ========== 公有方法 ==========

    def set_duration(self, duration_ms: int):
        """设置视频时长"""
        self._duration_ms = duration_ms

    def set_fps(self, fps: float):
        """设置帧率"""
        self._fps = fps if fps > 0 else 30.0

    def get_subtitle_data(self) -> dict:
        """获取字幕数据"""
        return self._subtitle_mgr.data

    def get_subtitle_manager(self) -> SubtitleManager:
        """获取字幕管理器实例"""
        return self._subtitle_mgr

    def is_locked(self, col: int, start_ms: int) -> bool:
        """检查字幕是否被锁定"""
        return (col, start_ms) in self._locked_states

    def add_subtitle(self, start_ms: int, end_ms: int, col: int = 0):
        """添加新字幕条（由打轴信号调用）

        Args:
            start_ms: 开始时间 (ms)
            end_ms: 结束时间 (ms)
            col: 轨道号，默认 0
        """
        duration = end_ms - start_ms
        self._subtitle_mgr.set(col, start_ms, duration, "")
        # 操作完成后保存状态
        self._push_undo()
        self._update_table()
        self.subtitle_changed.emit()

    def set_subtitle_text(self, col: int, start_ms: int, text: str):
        """设置字幕文本"""
        if start_ms in self._subtitle_mgr.data[col]:
            if (col, start_ms) in self._locked_states:
                return  # 锁定状态不可编辑
            duration = self._subtitle_mgr.data[col][start_ms].duration_ms
            self._subtitle_mgr.data[col][start_ms] = SubtitleEntry(duration, text)
            # 操作完成后保存状态
            self._push_undo()
            self._update_table()
            self.subtitle_changed.emit()

    def apply_subtitle_edit(self, col: int, old_start: int, new_start: int, new_end: int):
        """应用字幕编辑结果（由波形图编辑模式调用）

        Args:
            col: 轨道号
            old_start: 编辑前的起始点
            new_start: 新的起始点
            new_end: 新的结束点
        """
        # 检查原字幕是否存在
        subtitle = self._subtitle_mgr.get(col, old_start)
        if subtitle is None:
            return

        duration, text = subtitle

        # 检查是否锁定
        if (col, old_start) in self._locked_states:
            return

        # 删除旧条目
        self._subtitle_mgr.delete(col, old_start)

        # 同步更新锁定状态
        if (col, old_start) in self._locked_states:
            self._locked_states.discard((col, old_start))
            self._locked_states.add((col, new_start))

        # 创建新条目
        new_duration = new_end - new_start
        self._subtitle_mgr.set(col, new_start, new_duration, text)

        # 操作完成后保存状态
        self._push_undo()
        self._update_table()
        self.subtitle_changed.emit()

    def get_next_subtitle(self, col: int, current_start_ms: int) -> tuple[int, int] | None:
        """获取下一条字幕

        Args:
            col: 轨道号
            current_start_ms: 当前字幕开始时间

        Returns:
            (col, start_ms) 或 None
        """
        sub_data = self._subtitle_mgr.data.get(col, {})
        if not sub_data:
            return None

        sorted_starts = sorted(sub_data.keys())
        try:
            idx = sorted_starts.index(current_start_ms)
            if idx + 1 < len(sorted_starts):
                return (col, sorted_starts[idx + 1])
        except ValueError:
            pass

        return None

    def get_prev_subtitle(self, col: int, current_start_ms: int) -> tuple[int, int] | None:
        """获取上一条字幕

        Args:
            col: 轨道号
            current_start_ms: 当前字幕开始时间

        Returns:
            (col, start_ms) 或 None
        """
        sub_data = self._subtitle_mgr.data.get(col, {})
        if not sub_data:
            return None

        sorted_starts = sorted(sub_data.keys())
        try:
            idx = sorted_starts.index(current_start_ms)
            if idx - 1 >= 0:
                return (col, sorted_starts[idx - 1])
        except ValueError:
            pass

        return None

    def get_track_subtitle_count(self, col: int) -> int:
        """获取指定轨道的字幕数量"""
        return len(self._subtitle_mgr.data.get(col, {}))

    def refresh_track_combos(self):
        """刷新所有轨道相关的下拉框（当轨道数量变化时调用）"""
        # 获取当前最大轨道号
        max_track = get_effective_track_count(self._subtitle_mgr.get_max_track())

        # 更新轨道筛选器
        current_filter = self._track_filter.currentIndex()
        self._track_filter.blockSignals(True)
        self._track_filter.clear()
        self._track_filter.addItem("全部")
        for i in range(max_track):
            color = get_track_color(i + 1)
            self._track_filter.addItem(f"轨道 {i + 1}")
            self._track_filter.setItemData(i + 1, QColor(color), Qt.ForegroundRole)
        # 恢复选择
        if current_filter <= max_track:
            self._track_filter.setCurrentIndex(current_filter)
        else:
            self._track_filter.setCurrentIndex(0)
        self._track_filter.blockSignals(False)

        # 更新复制源轨道下拉框
        current_source = self._copy_source_combo.currentIndex()
        self._copy_source_combo.blockSignals(True)
        self._copy_source_combo.clear()
        for i in range(max_track):
            color = get_track_color(i + 1)
            self._copy_source_combo.addItem(f"轨道 {i + 1}")
            self._copy_source_combo.setItemData(i, QColor(color), Qt.ForegroundRole)
        if current_source < max_track:
            self._copy_source_combo.setCurrentIndex(current_source)
        else:
            self._copy_source_combo.setCurrentIndex(0)
        self._copy_source_combo.blockSignals(False)

        # 更新复制目标轨道下拉框
        current_target = self._copy_target_combo.currentIndex()
        self._copy_target_combo.blockSignals(True)
        self._copy_target_combo.clear()
        for i in range(max_track):
            color = get_track_color(i + 1)
            self._copy_target_combo.addItem(f"轨道 {i + 1}")
            self._copy_target_combo.setItemData(i, QColor(color), Qt.ForegroundRole)
        if current_target < max_track:
            self._copy_target_combo.setCurrentIndex(current_target)
        elif max_track > 1:
            self._copy_target_combo.setCurrentIndex(1)
        else:
            self._copy_target_combo.setCurrentIndex(0)
        self._copy_target_combo.blockSignals(False)

    def highlight_subtitle(self, col: int, start_ms: int):
        """高亮指定的字幕行

        Args:
            col: 轨道号
            start_ms: 字幕开始时间
        """
        from PySide6.QtWidgets import QAbstractItemView

        # 遍历表格，找到对应的行
        for row in range(self._table.rowCount()):
            num_item = self._table.item(row, 0)
            if num_item:
                data = num_item.data(Qt.UserRole)
                if data and data == (col, start_ms):
                    # 临时启用选择模式
                    self._table.setSelectionMode(QAbstractItemView.SingleSelection)
                    # 选中该行并滚动到可见位置
                    self._table.selectRow(row)
                    self._table.scrollToItem(
                        self._table.item(row, 0),
                        QAbstractItemView.PositionAtCenter,
                    )
                    return

        # 如果没有找到对应行，清除选择并恢复禁用模式
        self._table.clearSelection()
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
