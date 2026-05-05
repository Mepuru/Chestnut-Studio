"""打轴编辑卡片模块"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QHeaderView,
    QMenu,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.subtitle import SubtitleManager
from chestnut_studio.utils.time_utils import ms_to_time_str

# 字幕条颜色配置
SUBTITLE_COLORS = {
    "normal": QColor(53, 84, 93),  # 正常持续时间
    "long": QColor(250, 128, 114),  # 持续时间 > 4.5s
    "abnormal": QColor(178, 34, 34),  # 持续时间异常
}

# 轨道数量
NUM_COLUMNS = 4

# 可视区域行数（固定）
VISIBLE_ROWS = 200

# 快捷键映射
KEY_MAP = {
    Qt.Key_Q: "shift_start_left",
    Qt.Key_1: "shift_start_left",
    Qt.Key_W: "shift_start_right",
    Qt.Key_2: "shift_start_right",
    Qt.Key_E: "shift_end_left",
    Qt.Key_3: "shift_end_left",
    Qt.Key_R: "shift_end_right",
    Qt.Key_4: "shift_end_right",
    Qt.Key_5: "split_at_cursor",
    Qt.Key_Delete: "delete_selected",
}


class TimelineCard(QDockWidget):
    """打轴编辑卡片

    功能：
    - 虚拟滚动：只渲染可视区域，支持任意长度视频
    - 4列字幕轨道
    - 点击跳转到视频对应位置并暂停
    - 完整的快捷键支持
    - 右键上下文菜单
    - 双击编辑字幕文本
    - 叠轴检测
    - 撤销/重做
    """

    # 信号
    subtitle_selected = Signal(int, str)  # 字幕被选中 (col, text)
    subtitle_changed = Signal()  # 字幕数据变化
    position_jump_requested = Signal(int)  # 请求跳转并暂停

    # 默认停靠区域
    default_area = Qt.RightDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("时间轴", parent)
        self._subtitle_mgr = SubtitleManager()
        self._global_interval = 33.33  # 间隔 (ms)
        self._style_names = ["1", "2", "3", "4"]
        self._clipboard = []
        self._follow_player = True
        self._player_position = 0
        self._scroll_offset = 0  # 滚动偏移（起始行号）
        self._total_logical_rows = 0  # 逻辑总行数（根据视频时长计算）
        self._selected_logical_row = 0  # 选中的逻辑行号
        self._selected_col = 0  # 选中的列号
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

        # 创建表格 - 固定行数
        self._table = QTableWidget(VISIBLE_ROWS, NUM_COLUMNS, self)
        self._table.setStyleSheet("""
            QTableWidget {
                background: #0f0f14;
                color: #e4e4e7;
                gridline-color: #27272a;
                font-size: 9pt;
                selection-background-color: rgba(37, 99, 235, 0.3);
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
            QHeaderView::section:vertical {
                min-width: 70px;
                max-width: 70px;
            }
            QHeaderView::section:horizontal {
                min-height: 25px;
            }
        """)

        # 设置表格属性
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self._table.verticalHeader().setDefaultSectionSize(15)
        self._table.verticalHeader().setMinimumSectionSize(15)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)

        # 隐藏原生滚动条（我们自己控制）
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 设置列头
        for i in range(NUM_COLUMNS):
            self._table.setHorizontalHeaderItem(i, QTableWidgetItem(self._style_names[i]))

        # 创建自定义滚动条
        from PySide6.QtWidgets import QScrollBar
        self._scrollbar = QScrollBar(Qt.Vertical, self)
        self._scrollbar.setRange(0, 0)
        self._scrollbar.valueChanged.connect(self._on_scrollbar_changed)

        # 连接信号
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        # 滚轮事件
        self._table.wheelEvent = self._wheel_event

        # 表格和滚动条布局
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)

        # 使用水平布局包含表格和滚动条
        from PySide6.QtWidgets import QHBoxLayout
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        h_layout.addWidget(self._table)
        h_layout.addWidget(self._scrollbar)

        layout.addLayout(h_layout)
        self.setWidget(content)

        # 初始刷新
        self._refresh_display()

    def _wheel_event(self, event):
        """处理滚轮事件"""
        delta = event.angleDelta().y()
        if delta > 0:
            # 向上滚动
            self._scroll_up(3)
        elif delta < 0:
            # 向下滚动
            self._scroll_down(3)
        event.accept()

    def _scroll_up(self, rows: int):
        """向上滚动"""
        self._scroll_offset = max(0, self._scroll_offset - rows)
        self._scrollbar.setValue(self._scroll_offset)
        self._refresh_display()

    def _scroll_down(self, rows: int):
        """向下滚动"""
        max_offset = max(0, self._total_logical_rows - VISIBLE_ROWS)
        self._scroll_offset = min(max_offset, self._scroll_offset + rows)
        self._scrollbar.setValue(self._scroll_offset)
        self._refresh_display()

    def _on_scrollbar_changed(self, value):
        """滚动条变化"""
        self._scroll_offset = value
        self._refresh_display()

    def _update_scrollbar(self):
        """更新滚动条范围"""
        max_offset = max(0, self._total_logical_rows - VISIBLE_ROWS)
        self._scrollbar.setRange(0, max_offset)
        self._scrollbar.setPageStep(VISIBLE_ROWS)

    # ========== 公有方法 ==========

    def set_player_position(self, ms: int):
        """设置播放器位置，可选跟随滚动"""
        self._player_position = ms
        if self._follow_player:
            target_row = int(ms / self._global_interval)
            # 确保播放位置在可视区域中间
            self._scroll_offset = max(0, target_row - VISIBLE_ROWS // 2)
            max_offset = max(0, self._total_logical_rows - VISIBLE_ROWS)
            self._scroll_offset = min(self._scroll_offset, max_offset)
            self._scrollbar.setValue(self._scroll_offset)
        self._refresh_display()

    def set_interval(self, interval_ms: float):
        """设置间隔"""
        self._global_interval = interval_ms
        self._refresh_display()

    def get_interval(self) -> float:
        """获取当前间隔"""
        return self._global_interval

    def set_duration(self, duration_ms: int):
        """设置视频时长，更新逻辑行数"""
        self._total_logical_rows = int(duration_ms / self._global_interval) + 1
        self._update_scrollbar()
        self._refresh_display()

    def get_subtitle_data(self) -> dict:
        """获取字幕数据"""
        return self._subtitle_mgr.data

    def get_subtitle_manager(self) -> SubtitleManager:
        """获取字幕管理器实例"""
        return self._subtitle_mgr

    def set_follow_player(self, follow: bool):
        """设置是否跟随播放位置"""
        self._follow_player = follow

    def is_following_player(self) -> bool:
        """是否跟随播放位置"""
        return self._follow_player

    def jump_to_position(self, ms: int):
        """跳转到指定时间位置"""
        target_row = int(ms / self._global_interval)
        self._scroll_offset = max(0, target_row - VISIBLE_ROWS // 2)
        max_offset = max(0, self._total_logical_rows - VISIBLE_ROWS)
        self._scroll_offset = min(self._scroll_offset, max_offset)
        self._scrollbar.setValue(self._scroll_offset)
        self._refresh_display()

    # ========== 快捷键操作 ==========

    def keyPressEvent(self, event):
        """处理快捷键"""
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl 组合键
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Z:
                self._undo()
                event.accept()
                return
            elif key == Qt.Key_Y:
                self._redo()
                event.accept()
                return
            elif key == Qt.Key_C:
                self._copy()
                event.accept()
                return
            elif key == Qt.Key_V:
                self._paste()
                event.accept()
                return
            elif key == Qt.Key_X:
                self._cut()
                event.accept()
                return

        # 单键操作
        if key in KEY_MAP:
            action = KEY_MAP[key]
            self._execute_action(action)
            event.accept()
            return

        # 方向键
        if key == Qt.Key_Up:
            self._move_selection(-1, 0)
            event.accept()
            return
        elif key == Qt.Key_Down:
            self._move_selection(1, 0)
            event.accept()
            return
        elif key == Qt.Key_Left:
            self._move_selection(0, -1)
            event.accept()
            return
        elif key == Qt.Key_Right:
            self._move_selection(0, 1)
            event.accept()
            return

        # 空格键 - 传递给父窗口
        if key == Qt.Key_Space:
            event.ignore()
            return

        super().keyPressEvent(event)

    def _execute_action(self, action: str):
        """执行快捷键操作"""
        if action == "shift_start_left":
            self._shift_start(-1)
        elif action == "shift_start_right":
            self._shift_start(1)
        elif action == "shift_end_left":
            self._shift_end(-1)
        elif action == "shift_end_right":
            self._shift_end(1)
        elif action == "split_at_cursor":
            self._split_at_cursor()
        elif action == "delete_selected":
            self._delete_selected()

    # ========== 表格操作 ==========

    def _refresh_display(self):
        """刷新表格显示"""
        # 清空所有单元格
        for row in range(VISIBLE_ROWS):
            for col in range(NUM_COLUMNS):
                item = self._table.item(row, col)
                if item:
                    item.setText("")
                    item.setBackground(QBrush(QColor("#0f0f14")))
                    item.setData(Qt.UserRole, None)
                    item.setData(Qt.UserRole + 1, None)

        # 更新行头时间戳
        for row in range(VISIBLE_ROWS):
            logical_row = self._scroll_offset + row
            time_ms = int(logical_row * self._global_interval)
            header_item = QTableWidgetItem(ms_to_time_str(time_ms))
            header_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._table.setVerticalHeaderItem(row, header_item)

        # 计算可见时间范围
        view_start_ms = int(self._scroll_offset * self._global_interval)
        view_end_ms = int((self._scroll_offset + VISIBLE_ROWS) * self._global_interval)

        # 填充字幕条
        for col, sub_data in self._subtitle_mgr.data.items():
            for start in sorted(sub_data):
                delta, text = sub_data[start]
                end = start + delta
                if end < view_start_ms:
                    continue
                if start > view_end_ms:
                    break
                self._render_subtitle(col, start, delta, text)

        # 恢复选中状态
        vis_row = self._selected_logical_row - self._scroll_offset
        if 0 <= vis_row < VISIBLE_ROWS:
            self._table.setCurrentCell(vis_row, self._selected_col)

    def _render_subtitle(self, col: int, start: int, duration: int, text: str):
        """渲染单个字幕条到表格"""
        # 计算逻辑行范围
        logical_row_start = int(start / self._global_interval)
        logical_row_end = int((start + duration) / self._global_interval)

        # 转换为可视行范围
        vis_row_start = logical_row_start - self._scroll_offset
        vis_row_end = logical_row_end - self._scroll_offset

        # 限制在可视范围内
        vis_row_start = max(0, min(VISIBLE_ROWS - 1, vis_row_start))
        vis_row_end = max(0, min(VISIBLE_ROWS - 1, vis_row_end))

        if vis_row_start > VISIBLE_ROWS - 1 or vis_row_end < 0:
            return

        # 确定颜色
        duration_sec = duration / 1000.0
        if duration_sec > 4.5:
            color = SUBTITLE_COLORS["long"]
        elif duration_sec < 0.1:
            color = SUBTITLE_COLORS["abnormal"]
        else:
            color = SUBTITLE_COLORS["normal"]

        # 合并单元格并设置内容
        if vis_row_start < vis_row_end:
            self._table.setSpan(vis_row_start, col, vis_row_end - vis_row_start + 1, 1)

        item = QTableWidgetItem(text)
        item.setBackground(QBrush(color))
        item.setForeground(QBrush(QColor("#e4e4e7")))
        item.setData(Qt.UserRole, start)  # 存储起始时间
        item.setData(Qt.UserRole + 1, logical_row_start)  # 存储逻辑行号
        self._table.setItem(vis_row_start, col, item)

    def _move_selection(self, row_delta: int, col_delta: int):
        """移动选中位置"""
        current_row = self._table.currentRow()
        current_col = self._table.currentColumn()

        new_row = max(0, min(VISIBLE_ROWS - 1, current_row + row_delta))
        new_col = max(0, min(NUM_COLUMNS - 1, current_col + col_delta))

        # 如果移动超出可视范围，滚动
        if new_row == 0 and row_delta < 0:
            self._scroll_up(1)
        elif new_row == VISIBLE_ROWS - 1 and row_delta > 0:
            self._scroll_down(1)

        # 更新逻辑行号
        self._selected_logical_row = self._scroll_offset + new_row
        self._selected_col = new_col
        self._table.setCurrentCell(new_row, new_col)

    # ========== 字幕条操作 ==========

    def _get_selected_col(self) -> int:
        """获取当前选中的列"""
        current_col = self._table.currentColumn()
        return max(0, min(NUM_COLUMNS - 1, current_col))

    def _get_selected_logical_row(self) -> int:
        """获取当前选中的逻辑行号"""
        vis_row = self._table.currentRow()
        return self._scroll_offset + vis_row

    def _shift_start(self, direction: int):
        """调整轴左端"""
        logical_row = self._get_selected_logical_row()
        current_col = self._get_selected_col()
        time_ms = int(logical_row * self._global_interval)

        for start, (delta, text) in list(self._subtitle_mgr.data[current_col].items()):
            end = start + delta
            if start <= time_ms < end:
                new_start = start + int(direction * self._global_interval)
                if new_start < end and new_start >= 0:
                    overlap_result = self._subtitle_mgr.check_overlap(
                        current_col, new_start, end, self._global_interval
                    )
                    if overlap_result == 0:
                        QMessageBox.warning(self, "叠轴检测", "操作会导致重叠，已阻止")
                        return

                    self._subtitle_mgr.push_undo()
                    self._subtitle_mgr.delete(current_col, start)
                    new_delta = end - new_start
                    self._subtitle_mgr.set(current_col, new_start, new_delta, text)

                    self._refresh_display()
                    self.subtitle_changed.emit()
                break

    def _shift_end(self, direction: int):
        """调整轴右端"""
        logical_row = self._get_selected_logical_row()
        current_col = self._get_selected_col()
        time_ms = int(logical_row * self._global_interval)

        for start, (delta, text) in list(self._subtitle_mgr.data[current_col].items()):
            end = start + delta
            if start <= time_ms < end:
                new_end = end + int(direction * self._global_interval)
                if new_end > start:
                    overlap_result = self._subtitle_mgr.check_overlap(
                        current_col, start, new_end, self._global_interval
                    )
                    if overlap_result == 0:
                        QMessageBox.warning(self, "叠轴检测", "操作会导致重叠，已阻止")
                        return

                    self._subtitle_mgr.push_undo()
                    new_delta = new_end - start
                    self._subtitle_mgr.set(current_col, start, new_delta, text)

                    self._refresh_display()
                    self.subtitle_changed.emit()
                break

    def _split_at_cursor(self):
        """在光标位置切割字幕条"""
        logical_row = self._get_selected_logical_row()
        current_col = self._get_selected_col()
        split_time = int(logical_row * self._global_interval)

        self._subtitle_mgr.push_undo()
        if self._subtitle_mgr.split(current_col, split_time):
            self._refresh_display()
            self.subtitle_changed.emit()

    def _delete_selected(self):
        """删除选中的字幕条"""
        selected = self._table.selectedItems()
        if not selected:
            return

        self._subtitle_mgr.push_undo()
        for item in selected:
            col = item.column()
            start_time = item.data(Qt.UserRole)
            if start_time is not None:
                self._subtitle_mgr.delete(col, start_time)

        self._refresh_display()
        self.subtitle_changed.emit()

    def _merge_selected(self):
        """合并选中的多行为一条字幕"""
        selected = self._table.selectedItems()
        if not selected:
            return

        rows = set()
        cols = set()
        for item in selected:
            rows.add(item.row())
            cols.add(item.column())

        if len(rows) < 2:
            return

        self._subtitle_mgr.push_undo()

        for col in cols:
            logical_rows = [self._scroll_offset + r for r in rows]
            row_start = min(logical_rows)
            row_end = max(logical_rows)
            time_start = int(row_start * self._global_interval)
            time_end = int((row_end + 1) * self._global_interval)

            text = ""
            for row in range(row_start, row_end + 1):
                vis_row = row - self._scroll_offset
                if 0 <= vis_row < VISIBLE_ROWS:
                    item = self._table.item(vis_row, col)
                    if item and item.text():
                        text = item.text()
                        break

            self._subtitle_mgr.merge(col, time_start, time_end, text)

        self._refresh_display()
        self.subtitle_changed.emit()

    # ========== 剪贴板操作 ==========

    def _copy(self):
        """复制选中的字幕条"""
        selected = self._table.selectedItems()
        if not selected:
            return

        self._clipboard = []
        for item in selected:
            col = item.column()
            start_time = item.data(Qt.UserRole)
            if start_time is not None:
                sub_data = self._subtitle_mgr.get(col, start_time)
                if sub_data:
                    self._clipboard.append({
                        "col": col,
                        "start": start_time,
                        "duration": sub_data[0],
                        "text": sub_data[1],
                    })

    def _cut(self):
        """剪切选中的字幕条"""
        self._copy()
        self._delete_selected()

    def _paste(self):
        """粘贴字幕条"""
        if not self._clipboard:
            return

        logical_row = self._get_selected_logical_row()
        current_col = self._get_selected_col()
        paste_time = int(logical_row * self._global_interval)

        self._subtitle_mgr.push_undo()

        for item in self._clipboard:
            self._subtitle_mgr.set(
                current_col,
                paste_time,
                item["duration"],
                item["text"],
            )
            paste_time += item["duration"]

        self._refresh_display()
        self.subtitle_changed.emit()

    # ========== 撤销/重做 ==========

    def _undo(self):
        """撤销"""
        if self._subtitle_mgr.undo():
            self._refresh_display()
            self.subtitle_changed.emit()

    def _redo(self):
        """重做"""
        if self._subtitle_mgr.redo():
            self._refresh_display()
            self.subtitle_changed.emit()

    # ========== 信号处理 ==========

    def _on_cell_clicked(self, row: int, col: int):
        """单击单元格 - 记录选中位置并跳转"""
        self._selected_logical_row = self._scroll_offset + row
        self._selected_col = col
        time_ms = int(self._selected_logical_row * self._global_interval)
        self.position_jump_requested.emit(time_ms)

    def _on_cell_double_clicked(self, row: int, col: int):
        """双击单元格 - 记录选中位置并发射字幕选中信号"""
        self._selected_logical_row = self._scroll_offset + row
        self._selected_col = col
        time_ms = int(self._selected_logical_row * self._global_interval)

        sub_data = self._subtitle_mgr.get(col, time_ms)
        if sub_data is None:
            for start, (delta, text) in self._subtitle_mgr.data[col].items():
                end = start + delta
                if start <= time_ms < end:
                    sub_data = [delta, text]
                    break

        if sub_data:
            self.subtitle_selected.emit(col, sub_data[1])

    def _show_context_menu(self, pos):
        """显示右键上下文菜单"""
        menu = QMenu(self)

        logical_row = self._get_selected_logical_row()
        current_col = self._get_selected_col()
        time_ms = int(logical_row * self._global_interval)

        has_subtitle = False
        for start, (delta, text) in self._subtitle_mgr.data[current_col].items():
            end = start + delta
            if start <= time_ms < end:
                has_subtitle = True
                break

        if has_subtitle:
            split_action = QAction("切割", self)
            split_action.triggered.connect(self._split_at_cursor)
            menu.addAction(split_action)

            delete_action = QAction("删除", self)
            delete_action.triggered.connect(self._delete_selected)
            menu.addAction(delete_action)

        menu.addSeparator()

        selected = self._table.selectedItems()
        if selected and len(selected) > 1:
            merge_action = QAction("合并选中", self)
            merge_action.triggered.connect(self._merge_selected)
            menu.addAction(merge_action)

        menu.addSeparator()

        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self._copy)
        menu.addAction(copy_action)

        cut_action = QAction("剪切", self)
        cut_action.triggered.connect(self._cut)
        menu.addAction(cut_action)

        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self._paste)
        menu.addAction(paste_action)

        menu.addSeparator()

        undo_action = QAction("撤销", self)
        undo_action.triggered.connect(self._undo)
        menu.addAction(undo_action)

        redo_action = QAction("重做", self)
        redo_action.triggered.connect(self._redo)
        menu.addAction(redo_action)

        menu.exec_(self._table.viewport().mapToGlobal(pos))

    # ========== 工具栏集成方法 ==========

    def create_subtitle_at_cursor(self):
        """在光标位置创建新字幕条"""
        logical_row = self._get_selected_logical_row()
        current_col = self._get_selected_col()
        start_time = int(logical_row * self._global_interval)
        duration = int(self._global_interval * 10)

        overlap_result = self._subtitle_mgr.check_overlap(
            current_col, start_time, start_time + duration, self._global_interval
        )
        if overlap_result == 0:
            QMessageBox.warning(self, "叠轴检测", "位置已存在字幕条，无法创建")
            return

        self._subtitle_mgr.push_undo()
        self._subtitle_mgr.set(current_col, start_time, duration, "")
        self._refresh_display()
        self.subtitle_changed.emit()

    def set_subtitle_text(self, col: int, start: int, text: str):
        """设置字幕文本"""
        sub_data = self._subtitle_mgr.get(col, start)
        if sub_data:
            self._subtitle_mgr.push_undo()
            self._subtitle_mgr.set(col, start, sub_data[0], text)
            self._refresh_display()
            self.subtitle_changed.emit()
