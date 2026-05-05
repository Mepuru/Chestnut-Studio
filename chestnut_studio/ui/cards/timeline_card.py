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

# 快捷键映射
KEY_MAP = {
    Qt.Key_Q: "shift_start_left",  # 轴左端左移
    Qt.Key_1: "shift_start_left",
    Qt.Key_W: "shift_start_right",  # 轴左端右移
    Qt.Key_2: "shift_start_right",
    Qt.Key_E: "shift_end_left",  # 轴右端左移
    Qt.Key_3: "shift_end_left",
    Qt.Key_R: "shift_end_right",  # 轴右端右移
    Qt.Key_4: "shift_end_right",
    Qt.Key_5: "split_at_cursor",  # 切割
    Qt.Key_Delete: "delete_selected",  # 删除
}


class TimelineCard(QDockWidget):
    """打轴编辑卡片

    功能：
    - 可滚动的动态表格，4列字幕轨道
    - 点击跳转到视频对应位置并暂停
    - 完整的快捷键支持
    - 右键上下文菜单
    - 双击编辑字幕文本
    - 叠轴检测
    - 撤销/重做
    - 跟随播放位置模式
    """

    # 信号
    subtitle_selected = Signal(int, str)  # 字幕被选中 (col, text)
    subtitle_changed = Signal()  # 字幕数据变化（用于刷新波形覆盖）
    position_jump_requested = Signal(int)  # 请求跳转到指定位置并暂停

    # 默认停靠区域
    default_area = Qt.RightDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("时间轴", parent)
        self._subtitle_mgr = SubtitleManager()
        self._global_interval = 33.33  # 间隔 (ms)
        self._style_names = ["1", "2", "3", "4"]
        self._clipboard = []  # 剪贴板
        self._follow_player = True  # 跟随播放位置模式
        self._player_position = 0  # 播放器当前位置
        self._total_rows = 10000  # 默认总行数（约5分钟 @33ms间隔）
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

        # 创建表格
        self._table = QTableWidget(self._total_rows, NUM_COLUMNS, self)
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

        # 设置列头
        for i in range(NUM_COLUMNS):
            self._table.setHorizontalHeaderItem(i, QTableWidgetItem(self._style_names[i]))

        # 初始化行头时间戳
        self._update_row_headers()

        # 连接信号
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        # 滚动条变化时刷新可见区域
        self._table.verticalScrollBar().valueChanged.connect(self._on_scroll)

        layout.addWidget(self._table)
        self.setWidget(content)

        # 初始刷新
        self._refresh_visible_rows()

    def _update_row_headers(self):
        """更新所有行头时间戳"""
        for row in range(self._total_rows):
            time_ms = int(row * self._global_interval)
            header_item = QTableWidgetItem(ms_to_time_str(time_ms))
            header_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._table.setVerticalHeaderItem(row, header_item)

    # ========== 公有方法 ==========

    def set_player_position(self, ms: int):
        """设置播放器位置，可选跟随滚动"""
        self._player_position = ms
        if self._follow_player:
            row = int(ms / self._global_interval)
            self._table.scrollToItem(self._table.item(row, 0))
        self._refresh_visible_rows()

    def set_interval(self, interval_ms: float):
        """设置间隔"""
        self._global_interval = interval_ms
        # 重新计算总行数（默认支持到10分钟）
        self._total_rows = int(600000 / interval_ms)
        self._table.setRowCount(self._total_rows)
        self._update_row_headers()
        self._refresh_visible_rows()

    def get_interval(self) -> float:
        """获取当前间隔"""
        return self._global_interval

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
        row = int(ms / self._global_interval)
        row = max(0, min(self._total_rows - 1, row))
        self._table.scrollToItem(self._table.item(row, 0))
        self._table.setCurrentCell(row, 0)
        self._refresh_visible_rows()

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

        # 空格键播放/暂停 - 传递给父窗口
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

    def _on_scroll(self, value):
        """滚动时刷新可见区域"""
        self._refresh_visible_rows()

    def _refresh_visible_rows(self):
        """刷新可见行的字幕显示"""
        # 清空所有单元格
        for row in range(self._total_rows):
            for col in range(NUM_COLUMNS):
                item = self._table.item(row, col)
                if item:
                    item.setText("")
                    item.setBackground(QBrush(QColor("#0f0f14")))
                    item.setData(Qt.UserRole, None)

        # 获取可见范围
        visible_top = self._table.rowAt(0)
        visible_bottom = self._table.rowAt(self._table.viewport().height())
        if visible_top < 0:
            visible_top = 0
        if visible_bottom < 0:
            visible_bottom = self._total_rows - 1

        # 计算可见时间范围
        view_start_ms = int(visible_top * self._global_interval)
        view_end_ms = int((visible_bottom + 1) * self._global_interval)

        # 填充可见范围内的字幕条
        for col, sub_data in self._subtitle_mgr.data.items():
            for start in sorted(sub_data):
                delta, text = sub_data[start]
                end = start + delta
                # 检查是否在可见范围内
                if end < view_start_ms:
                    continue
                if start > view_end_ms:
                    break
                self._render_subtitle(col, start, delta, text)

    def _render_subtitle(self, col: int, start: int, duration: int, text: str):
        """渲染单个字幕条到表格"""
        # 计算行范围
        row_start = int(start / self._global_interval)
        row_end = int((start + duration) / self._global_interval)

        # 限制在表格范围内
        row_start = max(0, min(self._total_rows - 1, row_start))
        row_end = max(0, min(self._total_rows - 1, row_end))

        # 确定颜色
        duration_sec = duration / 1000.0
        if duration_sec > 4.5:
            color = SUBTITLE_COLORS["long"]
        elif duration_sec < 0.1:
            color = SUBTITLE_COLORS["abnormal"]
        else:
            color = SUBTITLE_COLORS["normal"]

        # 合并单元格并设置内容
        if row_start < row_end:
            self._table.setSpan(row_start, col, row_end - row_start + 1, 1)

        item = QTableWidgetItem(text)
        item.setBackground(QBrush(color))
        item.setForeground(QBrush(QColor("#e4e4e7")))
        item.setData(Qt.UserRole, start)  # 存储起始时间
        self._table.setItem(row_start, col, item)

    def _move_selection(self, row_delta: int, col_delta: int):
        """移动选中位置"""
        current_row = self._table.currentRow()
        current_col = self._table.currentColumn()

        new_row = max(0, min(self._total_rows - 1, current_row + row_delta))
        new_col = max(0, min(NUM_COLUMNS - 1, current_col + col_delta))

        self._table.setCurrentCell(new_row, new_col)

    # ========== 字幕条操作 ==========

    def _get_selected_col(self) -> int:
        """获取当前选中的列"""
        current_col = self._table.currentColumn()
        return max(0, min(NUM_COLUMNS - 1, current_col))

    def _shift_start(self, direction: int):
        """调整轴左端

        Args:
            direction: -1 左移, 1 右移
        """
        current_row = self._table.currentRow()
        current_col = self._get_selected_col()
        time_ms = int(current_row * self._global_interval)

        # 查找包含此时间点的字幕条
        for start, (delta, text) in list(self._subtitle_mgr.data[current_col].items()):
            end = start + delta
            if start <= time_ms < end:
                # 计算新起点
                new_start = start + int(direction * self._global_interval)
                if new_start < end and new_start >= 0:
                    # 检查叠轴
                    overlap_result = self._subtitle_mgr.check_overlap(
                        current_col, new_start, end, self._global_interval
                    )
                    if overlap_result == 0:
                        QMessageBox.warning(self, "叠轴检测", "操作会导致重叠，已阻止")
                        return

                    # 执行调整
                    self._subtitle_mgr.push_undo()
                    self._subtitle_mgr.delete(current_col, start)
                    new_delta = end - new_start
                    self._subtitle_mgr.set(current_col, new_start, new_delta, text)

                    self._refresh_visible_rows()
                    self.subtitle_changed.emit()
                break

    def _shift_end(self, direction: int):
        """调整轴右端

        Args:
            direction: -1 左移, 1 右移
        """
        current_row = self._table.currentRow()
        current_col = self._get_selected_col()
        time_ms = int(current_row * self._global_interval)

        # 查找包含此时间点的字幕条
        for start, (delta, text) in list(self._subtitle_mgr.data[current_col].items()):
            end = start + delta
            if start <= time_ms < end:
                # 计算新终点
                new_end = end + int(direction * self._global_interval)
                if new_end > start:
                    # 检查叠轴
                    overlap_result = self._subtitle_mgr.check_overlap(
                        current_col, start, new_end, self._global_interval
                    )
                    if overlap_result == 0:
                        QMessageBox.warning(self, "叠轴检测", "操作会导致重叠，已阻止")
                        return

                    # 执行调整
                    self._subtitle_mgr.push_undo()
                    new_delta = new_end - start
                    self._subtitle_mgr.set(current_col, start, new_delta, text)

                    self._refresh_visible_rows()
                    self.subtitle_changed.emit()
                break

    def _split_at_cursor(self):
        """在光标位置切割字幕条"""
        current_row = self._table.currentRow()
        current_col = self._get_selected_col()
        split_time = int(current_row * self._global_interval)

        self._subtitle_mgr.push_undo()
        if self._subtitle_mgr.split(current_col, split_time):
            self._refresh_visible_rows()
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

        self._refresh_visible_rows()
        self.subtitle_changed.emit()

    def _merge_selected(self):
        """合并选中的多行为一条字幕"""
        selected = self._table.selectedItems()
        if not selected:
            return

        # 获取选中范围
        rows = set()
        cols = set()
        for item in selected:
            rows.add(item.row())
            cols.add(item.column())

        if len(rows) < 2:
            return

        self._subtitle_mgr.push_undo()

        for col in cols:
            # 计算时间范围
            row_start = min(rows)
            row_end = max(rows)
            time_start = int(row_start * self._global_interval)
            time_end = int((row_end + 1) * self._global_interval)

            # 查找第一个非空文本
            text = ""
            for row in range(row_start, row_end + 1):
                item = self._table.item(row, col)
                if item and item.text():
                    text = item.text()
                    break

            # 合并
            self._subtitle_mgr.merge(col, time_start, time_end, text)

        self._refresh_visible_rows()
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
                    self._clipboard.append(
                        {
                            "col": col,
                            "start": start_time,
                            "duration": sub_data[0],
                            "text": sub_data[1],
                        }
                    )

    def _cut(self):
        """剪切选中的字幕条"""
        self._copy()
        self._delete_selected()

    def _paste(self):
        """粘贴字幕条"""
        if not self._clipboard:
            return

        current_row = self._table.currentRow()
        current_col = self._get_selected_col()
        paste_time = int(current_row * self._global_interval)

        self._subtitle_mgr.push_undo()

        for item in self._clipboard:
            # 粘贴到当前选中列
            self._subtitle_mgr.set(
                current_col,
                paste_time,
                item["duration"],
                item["text"],
            )
            paste_time += item["duration"]

        self._refresh_visible_rows()
        self.subtitle_changed.emit()

    # ========== 撤销/重做 ==========

    def _undo(self):
        """撤销"""
        if self._subtitle_mgr.undo():
            self._refresh_visible_rows()
            self.subtitle_changed.emit()

    def _redo(self):
        """重做"""
        if self._subtitle_mgr.redo():
            self._refresh_visible_rows()
            self.subtitle_changed.emit()

    # ========== 信号处理 ==========

    def _on_cell_clicked(self, row: int, col: int):
        """单击单元格 - 跳转到对应时间并暂停播放"""
        time_ms = int(row * self._global_interval)
        self.position_jump_requested.emit(time_ms)

    def _on_cell_double_clicked(self, row: int, col: int):
        """双击单元格 - 发射字幕选中信号"""
        time_ms = int(row * self._global_interval)

        # 查找此时间点的字幕条
        sub_data = self._subtitle_mgr.get(col, time_ms)
        if sub_data is None:
            # 查找包含此时间点的字幕条
            for start, (delta, text) in self._subtitle_mgr.data[col].items():
                end = start + delta
                if start <= time_ms < end:
                    sub_data = [delta, text]
                    time_ms = start
                    break

        if sub_data:
            self.subtitle_selected.emit(col, sub_data[1])

    def _show_context_menu(self, pos):
        """显示右键上下文菜单"""
        menu = QMenu(self)

        # 获取当前单元格信息
        current_row = self._table.currentRow()
        current_col = self._get_selected_col()
        time_ms = int(current_row * self._global_interval)

        # 检查是否有字幕条
        has_subtitle = False
        for start, (delta, text) in self._subtitle_mgr.data[current_col].items():
            end = start + delta
            if start <= time_ms < end:
                has_subtitle = True
                break

        # 菜单项
        if has_subtitle:
            split_action = QAction("切割", self)
            split_action.triggered.connect(self._split_at_cursor)
            menu.addAction(split_action)

            delete_action = QAction("删除", self)
            delete_action.triggered.connect(self._delete_selected)
            menu.addAction(delete_action)

        menu.addSeparator()

        # 合并操作
        selected = self._table.selectedItems()
        if selected and len(selected) > 1:
            merge_action = QAction("合并选中", self)
            merge_action.triggered.connect(self._merge_selected)
            menu.addAction(merge_action)

        menu.addSeparator()

        # 剪贴板操作
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

        # 撤销/重做
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
        current_row = self._table.currentRow()
        current_col = self._get_selected_col()
        start_time = int(current_row * self._global_interval)
        duration = int(self._global_interval * 10)  # 默认 10 个间隔长度

        # 检查叠轴
        overlap_result = self._subtitle_mgr.check_overlap(
            current_col, start_time, start_time + duration, self._global_interval
        )
        if overlap_result == 0:
            QMessageBox.warning(self, "叠轴检测", "位置已存在字幕条，无法创建")
            return

        self._subtitle_mgr.push_undo()
        self._subtitle_mgr.set(current_col, start_time, duration, "")
        self._refresh_visible_rows()
        self.subtitle_changed.emit()

    def set_subtitle_text(self, col: int, start: int, text: str):
        """设置字幕文本"""
        sub_data = self._subtitle_mgr.get(col, start)
        if sub_data:
            self._subtitle_mgr.push_undo()
            self._subtitle_mgr.set(col, start, sub_data[0], text)
            self._refresh_visible_rows()
            self.subtitle_changed.emit()
