"""打轴编辑卡片模块"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QHeaderView,
    QInputDialog,
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

# 轴颜色列表
AXIS_COLORS = [
    QColor(59, 130, 246),   # 蓝色
    QColor(16, 185, 129),   # 绿色
    QColor(245, 158, 11),   # 橙色
    QColor(239, 68, 68),    # 红色
    QColor(139, 92, 246),   # 紫色
    QColor(236, 72, 153),   # 粉色
    QColor(20, 184, 166),   # 青色
    QColor(249, 115, 22),   # 深橙色
]

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
    - Shift+左键拖动批量选择并创建轴
    - Shift+右键拖动批量取消轴
    - 右键菜单管理轴
    - 完整的快捷键支持
    - 叠轴检测
    - 撤销/重做
    """

    # 信号
    subtitle_selected = Signal(int, str)  # 字幕被选中 (col, text)
    subtitle_changed = Signal()  # 字幕数据变化
    position_jump_requested = Signal(int)  # 请求跳转并暂停
    position_shift_requested = Signal(int)  # 请求移动位置（滚动边界时）

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
        self._scroll_offset = 0
        self._total_logical_rows = 0
        self._selected_logical_row = 0
        self._selected_col = 0
        self._user_clicked = False
        self._pending_refresh = False

        # 轴相关数据结构
        self._axes = {}  # {axis_id: {"name": str, "color": QColor, "cells": set}}
        self._cell_to_axis = {}  # {(logical_row, col): axis_id}
        self._next_axis_id = 1
        self._next_axis_counter = {}  # {col: counter} 用于生成轴编号

        # 拖动选择状态
        self._shift_left_dragging = False
        self._shift_right_dragging = False
        self._drag_start_cell = None
        self._drag_selected_cells = set()

        self._setup_ui()

        # 防抖定时器
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(16)
        self._refresh_timer.timeout.connect(self._do_pending_refresh)

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

        # 创建表格
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
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setDragEnabled(False)
        self._table.setDragDropMode(QAbstractItemView.NoDragDrop)
        self._table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self._table.verticalHeader().setDefaultSectionSize(15)
        self._table.verticalHeader().setMinimumSectionSize(15)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.setMouseTracking(True)

        # 设置列头
        for i in range(NUM_COLUMNS):
            self._table.setHorizontalHeaderItem(i, QTableWidgetItem(self._style_names[i]))

        # 连接信号
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        # 重写鼠标事件
        self._table.mousePressEvent = self._table_mouse_press
        self._table.mouseMoveEvent = self._table_mouse_move
        self._table.mouseReleaseEvent = self._table_mouse_release

        # 滚轮事件
        self._table.wheelEvent = self._wheel_event

        # 创建自定义滚动条
        from PySide6.QtWidgets import QScrollBar
        self._scrollbar = QScrollBar(Qt.Vertical, self)
        self._scrollbar.setRange(0, 0)
        self._scrollbar.valueChanged.connect(self._on_scrollbar_changed)

        # 布局
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

    def _get_cell_at_pos(self, pos):
        """获取鼠标位置对应的单元格 (logical_row, col)"""
        index = self._table.indexAt(pos)
        if index.isValid():
            vis_row = index.row()
            col = index.column()
            logical_row = self._scroll_offset + vis_row
            return (logical_row, col)
        return None

    def _table_mouse_press(self, event):
        """鼠标按下事件"""
        cell = self._get_cell_at_pos(event.pos())
        if cell is None:
            event.accept()
            return

        logical_row, col = cell
        modifiers = event.modifiers()

        if event.button() == Qt.LeftButton:
            if modifiers & Qt.ShiftModifier:
                # Shift+左键：开始拖动选择
                self._shift_left_dragging = True
                self._drag_start_cell = cell
                self._drag_selected_cells = {cell}
                self._highlight_drag_selection()
            else:
                # 普通左键：跳转并暂停
                self._selected_logical_row = logical_row
                self._selected_col = col
                self._user_clicked = True
                time_ms = int(logical_row * self._global_interval)
                self.position_jump_requested.emit(time_ms)
                self._refresh_display()

        elif event.button() == Qt.RightButton:
            if modifiers & Qt.ShiftModifier:
                # Shift+右键：开始拖动取消轴
                self._shift_right_dragging = True
                self._drag_start_cell = cell
                self._remove_cell_from_axis(cell)
                self._drag_selected_cells = {cell}
            else:
                # 普通右键：弹出菜单（在 _show_context_menu 中处理）
                self._selected_logical_row = logical_row
                self._selected_col = col
                self._refresh_display()

        event.accept()

    def _table_mouse_move(self, event):
        """鼠标移动事件"""
        cell = self._get_cell_at_pos(event.pos())
        if cell is None:
            event.accept()
            return

        if self._shift_left_dragging:
            # Shift+左键拖动：扩展选择
            if cell not in self._drag_selected_cells:
                self._drag_selected_cells.add(cell)
                self._highlight_drag_selection()

        elif self._shift_right_dragging:
            # Shift+右键拖动：取消轴
            if cell not in self._drag_selected_cells:
                self._drag_selected_cells.add(cell)
                self._remove_cell_from_axis(cell)

        event.accept()

    def _table_mouse_release(self, event):
        """鼠标释放事件"""
        if self._shift_left_dragging and event.button() == Qt.LeftButton:
            # Shift+左键释放：创建轴
            self._shift_left_dragging = False
            if len(self._drag_selected_cells) > 1:
                self._create_axis_from_selection()
            self._drag_selected_cells = set()
            self._refresh_display()

        elif self._shift_right_dragging and event.button() == Qt.RightButton:
            # Shift+右键释放：完成取消
            self._shift_right_dragging = False
            self._drag_selected_cells = set()
            self._refresh_display()

        event.accept()

    def _highlight_drag_selection(self):
        """高亮拖动选择的单元格"""
        # 先清除所有高亮
        for row in range(VISIBLE_ROWS):
            for col in range(NUM_COLUMNS):
                item = self._table.item(row, col)
                if item:
                    item.setSelected(False)

        # 高亮选中的单元格
        for logical_row, col in self._drag_selected_cells:
            vis_row = logical_row - self._scroll_offset
            if 0 <= vis_row < VISIBLE_ROWS:
                item = self._table.item(vis_row, col)
                if item:
                    item.setSelected(True)

    def _create_axis_from_selection(self):
        """从选择的单元格创建轴"""
        if not self._drag_selected_cells:
            return

        # 按列分组
        cells_by_col = {}
        for logical_row, col in self._drag_selected_cells:
            if col not in cells_by_col:
                cells_by_col[col] = []
            cells_by_col[col].append(logical_row)

        # 为每列创建一个轴
        for col, rows in cells_by_col.items():
            if len(rows) < 2:
                continue

            # 生成轴编号
            if col not in self._next_axis_counter:
                self._next_axis_counter[col] = 0
            self._next_axis_counter[col] += 1
            axis_num = self._next_axis_counter[col]

            # 创建轴
            axis_id = self._next_axis_id
            self._next_axis_id += 1

            axis_name = f"轴{col + 1}-{axis_num}"
            axis_color = AXIS_COLORS[(axis_id - 1) % len(AXIS_COLORS)]

            self._axes[axis_id] = {
                "name": axis_name,
                "color": axis_color,
                "cells": set(),
                "col": col,
            }

            # 添加单元格到轴
            for row in rows:
                cell_key = (row, col)
                # 如果单元格已属于其他轴，先移除
                if cell_key in self._cell_to_axis:
                    old_axis_id = self._cell_to_axis[cell_key]
                    self._axes[old_axis_id]["cells"].discard(cell_key)
                self._cell_to_axis[cell_key] = axis_id
                self._axes[axis_id]["cells"].add(cell_key)

        self.subtitle_changed.emit()

    def _remove_cell_from_axis(self, cell):
        """从轴中移除单元格"""
        if cell in self._cell_to_axis:
            axis_id = self._cell_to_axis[cell]
            del self._cell_to_axis[cell]
            self._axes[axis_id]["cells"].discard(cell)

            # 如果轴为空，删除轴
            if not self._axes[axis_id]["cells"]:
                del self._axes[axis_id]

            self.subtitle_changed.emit()

    def _get_axis_at_cell(self, cell):
        """获取单元格所在的轴"""
        if cell in self._cell_to_axis:
            axis_id = self._cell_to_axis[cell]
            return self._axes.get(axis_id)
        return None

    def _show_context_menu(self, pos):
        """显示右键上下文菜单"""
        # 只在非Shift状态下显示
        from PySide6.QtGui import QGuiApplication
        if QGuiApplication.keyboardModifiers() & Qt.ShiftModifier:
            return

        cell = self._get_cell_at_pos(pos)
        if cell is None:
            return

        menu = QMenu(self)

        # 检查是否有轴
        axis = self._get_axis_at_cell(cell)
        if axis:
            # 轴操作菜单
            rename_action = QAction(f"重命名轴: {axis['name']}", self)
            rename_action.triggered.connect(lambda: self._rename_axis(cell))
            menu.addAction(rename_action)

            delete_action = QAction(f"删除轴: {axis['name']}", self)
            delete_action.triggered.connect(lambda: self._delete_axis(cell))
            menu.addAction(delete_action)

            menu.addSeparator()

        # 其他操作
        current_col = cell[1]
        time_ms = int(cell[0] * self._global_interval)

        # 检查是否有字幕条
        has_subtitle = False
        for start, (delta, text) in self._subtitle_mgr.data[current_col].items():
            end = start + delta
            if start <= time_ms < end:
                has_subtitle = True
                break

        if has_subtitle:
            split_action = QAction("切割字幕", self)
            split_action.triggered.connect(self._split_at_cursor)
            menu.addAction(split_action)

            delete_sub_action = QAction("删除字幕", self)
            delete_sub_action.triggered.connect(self._delete_selected)
            menu.addAction(delete_sub_action)

        menu.addSeparator()

        undo_action = QAction("撤销", self)
        undo_action.triggered.connect(self._undo)
        menu.addAction(undo_action)

        redo_action = QAction("重做", self)
        redo_action.triggered.connect(self._redo)
        menu.addAction(redo_action)

        menu.exec_(self._table.viewport().mapToGlobal(pos))

    def _rename_axis(self, cell):
        """重命名轴"""
        axis = self._get_axis_at_cell(cell)
        if axis is None:
            return

        new_name, ok = QInputDialog.getText(
            self, "重命名轴", "轴名称:", text=axis["name"]
        )
        if ok and new_name:
            axis["name"] = new_name
            self._refresh_display()

    def _delete_axis(self, cell):
        """删除轴"""
        axis = self._get_axis_at_cell(cell)
        if axis is None:
            return

        reply = QMessageBox.question(
            self, "删除轴",
            f"确定要删除轴 '{axis['name']}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            axis_id = self._cell_to_axis.get(cell)
            if axis_id and axis_id in self._axes:
                # 移除所有单元格的映射
                for c in self._axes[axis_id]["cells"]:
                    if c in self._cell_to_axis:
                        del self._cell_to_axis[c]
                del self._axes[axis_id]
                self._refresh_display()
                self.subtitle_changed.emit()

    # ========== 滚动相关 ==========

    def _wheel_event(self, event):
        """处理滚轮事件 - 参考 DD_KaoRou2 边界处理"""
        delta = event.angleDelta().y()
        scroll_speed = 3  # 每次滚动行数

        if delta > 0:
            # 向上滚动
            if self._scroll_offset <= 0:
                # 已到顶部，移动视频位置
                shift_ms = int(scroll_speed * self._global_interval)
                self.position_shift_requested.emit(-shift_ms)
            else:
                self._scroll_up(scroll_speed)
        elif delta < 0:
            # 向下滚动
            max_offset = max(0, self._total_logical_rows - VISIBLE_ROWS)
            if self._scroll_offset >= max_offset:
                # 已到底部，移动视频位置
                shift_ms = int(scroll_speed * self._global_interval)
                self.position_shift_requested.emit(shift_ms)
            else:
                self._scroll_down(scroll_speed)
        event.accept()

    def _scroll_up(self, rows: int):
        """向上滚动"""
        self._scroll_offset = max(0, self._scroll_offset - rows)
        self._scrollbar.blockSignals(True)
        self._scrollbar.setValue(self._scroll_offset)
        self._scrollbar.blockSignals(False)
        self._request_refresh()

    def _scroll_down(self, rows: int):
        """向下滚动"""
        max_offset = max(0, self._total_logical_rows - VISIBLE_ROWS)
        self._scroll_offset = min(max_offset, self._scroll_offset + rows)
        self._scrollbar.blockSignals(True)
        self._scrollbar.setValue(self._scroll_offset)
        self._scrollbar.blockSignals(False)
        self._request_refresh()

    def _request_refresh(self):
        """请求刷新（防抖）"""
        self._pending_refresh = True
        self._refresh_timer.start()

    def _do_pending_refresh(self):
        """执行待刷新"""
        if self._pending_refresh:
            self._pending_refresh = False
            self._refresh_display()

    def _on_scrollbar_changed(self, value):
        """滚动条变化"""
        self._scroll_offset = value
        self._request_refresh()

    def _update_scrollbar(self):
        """更新滚动条范围"""
        min_rows = VISIBLE_ROWS + 100
        total_rows = max(min_rows, self._total_logical_rows)
        max_offset = max(0, total_rows - VISIBLE_ROWS)
        self._scrollbar.setRange(0, max_offset)
        self._scrollbar.setPageStep(VISIBLE_ROWS)

    # ========== 公有方法 ==========

    def set_player_position(self, ms: int):
        """设置播放器位置"""
        self._player_position = ms
        if self._user_clicked:
            self._user_clicked = False
            self._refresh_display()
            return
        if self._follow_player:
            target_row = int(ms / self._global_interval)
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
        """设置视频时长"""
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

    def jump_to_position_at_top(self, ms: int):
        """跳转到指定时间位置，显示在可视行1并选中"""
        target_row = int(ms / self._global_interval)
        self._scroll_offset = max(0, target_row)
        max_offset = max(0, self._total_logical_rows - VISIBLE_ROWS)
        self._scroll_offset = min(self._scroll_offset, max_offset)
        self._scrollbar.setValue(self._scroll_offset)
        self._selected_logical_row = self._scroll_offset
        self._selected_col = 0
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

        # 空格键
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
        self._table.blockSignals(True)

        # 清空所有单元格
        for row in range(VISIBLE_ROWS):
            for col in range(NUM_COLUMNS):
                item = self._table.item(row, col)
                if item:
                    item.setText("")
                    item.setBackground(QBrush(QColor("#0f0f14")))
                    item.setData(Qt.UserRole, None)
                    item.setFont(QFont())

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

        # 渲染轴
        self._render_axes()

        # 恢复选中状态
        vis_row = self._selected_logical_row - self._scroll_offset
        if 0 <= vis_row < VISIBLE_ROWS:
            self._table.setCurrentCell(vis_row, self._selected_col)
        else:
            self._table.clearSelection()
            self._table.setCurrentCell(-1, -1)

        self._table.blockSignals(False)

    def _render_subtitle(self, col: int, start: int, duration: int, text: str):
        """渲染单个字幕条到表格"""
        logical_row_start = int(start / self._global_interval)
        logical_row_end = int((start + duration) / self._global_interval)

        vis_row_start = logical_row_start - self._scroll_offset
        vis_row_end = logical_row_end - self._scroll_offset

        vis_row_start = max(0, min(VISIBLE_ROWS - 1, vis_row_start))
        vis_row_end = max(0, min(VISIBLE_ROWS - 1, vis_row_end))

        if vis_row_start > VISIBLE_ROWS - 1 or vis_row_end < 0:
            return

        duration_sec = duration / 1000.0
        if duration_sec > 4.5:
            color = SUBTITLE_COLORS["long"]
        elif duration_sec < 0.1:
            color = SUBTITLE_COLORS["abnormal"]
        else:
            color = SUBTITLE_COLORS["normal"]

        if vis_row_start < vis_row_end:
            self._table.setSpan(vis_row_start, col, vis_row_end - vis_row_start + 1, 1)

        item = QTableWidgetItem(text)
        item.setBackground(QBrush(color))
        item.setForeground(QBrush(QColor("#e4e4e7")))
        item.setData(Qt.UserRole, start)
        self._table.setItem(vis_row_start, col, item)

    def _render_axes(self):
        """渲染轴"""
        for axis_id, axis_data in self._axes.items():
            color = axis_data["color"]
            name = axis_data["name"]
            cells = axis_data["cells"]

            if not cells:
                continue

            # 找到轴的起始位置
            min_row = min(c[0] for c in cells)

            for logical_row, c in cells:
                vis_row = logical_row - self._scroll_offset
                if 0 <= vis_row < VISIBLE_ROWS:
                    item = self._table.item(vis_row, c)
                    if item is None:
                        item = QTableWidgetItem("")
                        self._table.setItem(vis_row, c, item)

                    # 设置轴颜色背景（半透明）
                    axis_bg = QColor(color)
                    axis_bg.setAlpha(80)
                    item.setBackground(QBrush(axis_bg))

                    # 如果是轴的第一行，显示轴名称
                    if logical_row == min_row:
                        item.setText(name)
                        item.setForeground(QBrush(QColor("#ffffff")))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

    def _move_selection(self, row_delta: int, col_delta: int):
        """移动选中位置"""
        current_row = self._selected_logical_row
        current_col = self._selected_col

        new_row = max(0, current_row + row_delta)
        new_col = max(0, min(NUM_COLUMNS - 1, current_col + col_delta))

        # 如果移动超出可视范围，滚动
        vis_row = new_row - self._scroll_offset
        if vis_row < 0:
            self._scroll_up(abs(vis_row))
        elif vis_row >= VISIBLE_ROWS:
            self._scroll_down(vis_row - VISIBLE_ROWS + 1)

        self._selected_logical_row = new_row
        self._selected_col = new_col
        self._refresh_display()

    # ========== 字幕条操作 ==========

    def _shift_start(self, direction: int):
        """调整轴左端"""
        logical_row = self._selected_logical_row
        current_col = self._selected_col
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
        logical_row = self._selected_logical_row
        current_col = self._selected_col
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
        logical_row = self._selected_logical_row
        current_col = self._selected_col
        split_time = int(logical_row * self._global_interval)

        self._subtitle_mgr.push_undo()
        if self._subtitle_mgr.split(current_col, split_time):
            self._refresh_display()
            self.subtitle_changed.emit()

    def _delete_selected(self):
        """删除选中的字幕条"""
        logical_row = self._selected_logical_row
        current_col = self._selected_col
        time_ms = int(logical_row * self._global_interval)

        self._subtitle_mgr.push_undo()
        for start in list(self._subtitle_mgr.data[current_col].keys()):
            delta = self._subtitle_mgr.data[current_col][start][0]
            end = start + delta
            if start <= time_ms < end:
                self._subtitle_mgr.delete(current_col, start)
                break

        self._refresh_display()
        self.subtitle_changed.emit()

    # ========== 剪贴板操作 ==========

    def _copy(self):
        """复制"""
        pass

    def _cut(self):
        """剪切"""
        pass

    def _paste(self):
        """粘贴"""
        pass

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

    # ========== 工具栏集成方法 ==========

    def create_subtitle_at_cursor(self):
        """在光标位置创建新字幕条"""
        logical_row = self._selected_logical_row
        current_col = self._selected_col
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
