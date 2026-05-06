"""打轴编辑卡片模块 - 完全照搬 DD_KaoRou2 的实现"""

import copy
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

# 字幕条颜色配置（与DD烤肉机一致）
SUBTITLE_COLORS = {
    "normal": QColor(53, 84, 93),    # #35545d 正常持续时间
    "long": QColor(250, 128, 114),   # #FA8072 持续时间 > 4.5s
    "abnormal": QColor(178, 34, 34), # #B22222 持续时间异常
}

# 轨道数量
NUM_COLUMNS = 4

# 可视区域行数（与DD烤肉机一致）
VISIBLE_ROWS = 101


def cnt2time(cnt, interval):
    """将计数转换为时间字符串 m:s.ms"""
    total_ms = int(cnt * interval)
    m, s = divmod(total_ms, 60000)
    s, ms = divmod(s, 1000)
    return '%s:%02d.%03d' % (m, s, ms)


class TimelineCard(QDockWidget):
    """打轴编辑卡片 - 完全照搬 DD_KaoRou2 的实现

    功能：
    - 虚拟滚动：只渲染可视区域，支持任意长度视频
    - 4列字幕轨道
    - 点击跳转到视频对应位置并暂停
    - 右键菜单：合并、切割、拆分、删除等操作
    - 完整的快捷键支持
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
        self._row = 0  # 当前视窗起始行号（与DD烤肉机一致）
        self._total_logical_rows = 0
        self._user_clicked = False
        self._is_refreshing = False  # 标记是否正在刷新，用于禁用鼠标跟随
        self._is_wheel_scrolling = False  # 标记是否正在滚轮滚动，用于禁用鼠标跟随

        # 撤销/重做后端
        self._subtitle_backend = []
        self._subtitle_backend_point = 0

        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI - 照搬DD烤肉机的设置"""
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

        # 创建表格（与DD烤肉机一致：101行）
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

        # 设置表格属性（与DD烤肉机一致）
        self._table.setAutoScroll(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self._table.setDragEnabled(False)
        self._table.setDragDropMode(QAbstractItemView.NoDragDrop)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.setMouseTracking(True)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 隐藏内置滚动条

        # 设置列宽和行高（与DD烤肉机一致）
        for i in range(NUM_COLUMNS):
            self._table.setColumnWidth(i, 130)
            self._table.setHorizontalHeaderItem(i, QTableWidgetItem(self._style_names[i]))
        for row in range(VISIBLE_ROWS):
            self._table.setRowHeight(row, 15)

        # 连接信号（与DD烤肉机一致）
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellEntered.connect(self._follow_mouse)
        self._table.doubleClicked.connect(self._start_edit)
        self._table.verticalHeader().sectionClicked.connect(self._header_click)

        # 重写滚轮事件
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
        self._refresh_table()

    def _follow_mouse(self, row, col):
        """鼠标按住拖动时 全局进度跟随鼠标（与DD烤肉机一致）"""
        # 正在刷新或滚轮滚动时禁用鼠标跟随
        if self._is_refreshing or self._is_wheel_scrolling:
            print(f"[DEBUG] _follow_mouse blocked: is_refreshing={self._is_refreshing}, is_wheel_scrolling={self._is_wheel_scrolling}")
            return
        if self._player_position and self._follow_player:
            position = int(row * self._global_interval) + self._player_position
            print(f"[DEBUG] _follow_mouse: row={row}, col={col}, position={position}, player_position={self._player_position}")
            self.position_jump_requested.emit(position)

    def _header_click(self, row):
        """点击行号跳转（与DD烤肉机一致）"""
        position = int(row * self._global_interval) + self._player_position
        self.position_jump_requested.emit(position)

    def _start_edit(self):
        """双击单元格开始编辑（与DD烤肉机一致）"""
        selected = self._table.selectionModel().selection().indexes()
        if not selected:
            return
        row = selected[0].row()
        col = selected[0].column()
        # 这里可以添加编辑逻辑
        pass

    def _wheel_event(self, event):
        """处理滚轮事件 - 参考 DD_KaoRou2"""
        delta = event.angleDelta().y()
        scroll_speed = 3

        self._is_wheel_scrolling = True  # 标记正在滚轮滚动
        print(f"[DEBUG] _wheel_event: delta={delta}, current_row={self._row}")

        if delta > 0:
            # 向上滚动
            new_row = self._row - scroll_speed
            if new_row < 0:
                new_row = 0
            if new_row != self._row:
                print(f"[DEBUG] _wheel_event: scroll UP, new_row={new_row}")
                self._row = new_row
                self._refresh_table()
        elif delta < 0:
            # 向下滚动
            new_row = self._row + scroll_speed
            print(f"[DEBUG] _wheel_event: scroll DOWN, new_row={new_row}")
            # 不限制最大值，允许无限滚动
            self._row = new_row
            self._refresh_table()

        # 延迟重置标志，确保所有 pending 的 cellEntered 信号都被忽略
        QTimer.singleShot(100, lambda: setattr(self, '_is_wheel_scrolling', False))
        event.accept()

    def _on_scrollbar_changed(self, value):
        """滚动条变化"""
        self._row = value
        self._refresh_table()

    def _refresh_table(self, position=None, select=0, scroll=0):
        """实时刷新表格 - 完全照搬DD烤肉机的实现"""
        self._is_refreshing = True  # 标记正在刷新，禁用鼠标跟随
        self._table.blockSignals(True)
        self._table.clearSpans()
        self._table.clear()

        # 设置当前行号（与DD烤肉机一致）
        # 只有明确传入 position 时才更新 _row，否则保持当前 _row
        if position is not None:
            self._player_position = position
            self._row = int(position / self._global_interval)

        # 设置行头时间戳（与DD烤肉机一致）
        self._table.setVerticalHeaderLabels(
            [cnt2time(i, self._global_interval) for i in range(self._row, self._row + VISIBLE_ROWS)]
        )
        self._table.setHorizontalHeaderLabels(self._style_names)

        # 计算可见时间范围
        subtitle_view_up = int(self._row * self._global_interval)
        subtitle_view_down = int((self._row + VISIBLE_ROWS) * self._global_interval)

        # 填充字幕条（与DD烤肉机一致）
        for col, sub_data in self._subtitle_mgr.data.items():
            for start in sorted(sub_data):
                delta, text = sub_data[start]
                if delta < 500 or delta > 8000:
                    table_color = SUBTITLE_COLORS["abnormal"]
                elif delta > 4500:
                    table_color = SUBTITLE_COLORS["long"]
                else:
                    table_color = SUBTITLE_COLORS["normal"]

                if start >= subtitle_view_down or not delta:
                    break
                elif start + delta >= subtitle_view_up:
                    # 计算字幕条位于表格视窗的位置
                    start_row = int(start / self._global_interval)
                    if start % self._global_interval:
                        start_row += 1
                    start_row = start_row - self._row

                    end_row = int((start + delta) / self._global_interval)
                    if (start + delta) % self._global_interval:
                        end_row += 1
                    end_row = end_row - self._row

                    if start_row < 0:
                        start_row = 0
                    if end_row > VISIBLE_ROWS:
                        end_row = VISIBLE_ROWS

                    if end_row > start_row:
                        for y in range(start_row, end_row):
                            self._table.setItem(y, col, QTableWidgetItem(text))
                        self._table.item(start_row, col).setBackground(table_color)
                        # 只有多行时才设置 span，避免 single cell span 警告
                        if end_row - start_row > 1:
                            self._table.setSpan(start_row, col, end_row - start_row, 1)
                        self._table.item(start_row, col).setTextAlignment(Qt.AlignTop)

        # 更新滚动条
        max_row = max(0, self._total_logical_rows - VISIBLE_ROWS)
        self._scrollbar.setRange(0, max_row)
        self._scrollbar.blockSignals(True)
        self._scrollbar.setValue(self._row)
        self._scrollbar.blockSignals(False)

        self._table.blockSignals(False)
        self._is_refreshing = False  # 刷新完成，启用鼠标跟随

    def _show_context_menu(self, pos):
        """显示右键上下文菜单 - 完全照搬DD烤肉机的实现"""
        menu = QMenu(self)
        set_span = menu.addAction('合并')
        cut_span = menu.addAction('切割')
        clr_span = menu.addAction('拆分')
        cut = menu.addAction('剪切')
        _copy = menu.addAction('复制')
        paste = menu.addAction('粘贴')
        delete = menu.addAction('删除')

        action = menu.exec_(self._table.viewport().mapToGlobal(pos))

        # 获取选区（与DD烤肉机一致）
        selected = self._table.selectionModel().selection().indexes()
        if not selected:
            return

        x_list = []  # 选中列
        for i in range(len(selected)):
            x = selected[i].column()
            if x not in x_list:
                x_list.append(x)
        y_list = [selected[0].row(), selected[-1].row()]

        if action == cut:  # 剪切
            select_range = [int((y + self._row) * self._global_interval) for y in range(y_list[0], y_list[1] + 1)]
            self._clipboard = []
            for x in x_list:
                for start, sub_data in self._subtitle_mgr.data[x].items():
                    end = sub_data[0] + start
                    for position in select_range:
                        if start < position and position < end:
                            self._clipboard.append([start, sub_data])
                            break
                for i in self._clipboard:
                    start = i[0]
                    try:
                        del self._subtitle_mgr.data[x][start]
                    except:
                        pass
                for y in range(y_list[0], y_list[1] + 1):
                    if self._table.item(y, x):
                        self._table.setSpan(y, x, 1, 1)
                        self._table.setItem(y, x, QTableWidgetItem(''))
                        self._table.item(y, x).setBackground(QColor('#232629'))
                break
            self._update_backend()

        elif action == _copy:  # 复制
            select_range = [int((y + self._row) * self._global_interval) for y in range(y_list[0], y_list[1] + 1)]
            self._clipboard = []
            for x in x_list:
                for start, sub_data in self._subtitle_mgr.data[x].items():
                    end = sub_data[0] + start
                    for position in select_range:
                        if start < position and position < end:
                            self._clipboard.append([start, sub_data])
                            break
                break

        elif action == paste:  # 粘贴
            if self._clipboard:
                clip_board = []
                for i in self._clipboard:
                    clip_board.append([i[0] - self._clipboard[0][0], i[1]])
                start_offset = int((y_list[0] + self._row) * self._global_interval)
                for x in x_list:
                    for sub_data in clip_board:
                        start, sub_data = sub_data
                        delta, text = sub_data
                        start += start_offset
                        end = start + delta
                        for sub_start in list(self._subtitle_mgr.data[x].keys()):
                            sub_end = self._subtitle_mgr.data[x][sub_start][0] + sub_start
                            if sub_start < end and end < sub_end or sub_start < start and start < sub_end:
                                del self._subtitle_mgr.data[x][sub_start]
                        self._subtitle_mgr.data[x][start] = [delta, text]
                self._refresh_table()
                self._update_backend()

        elif action == delete:  # 删除选中
            select_range = [int((y + self._row) * self._global_interval) for y in y_list]
            for x in x_list:
                start_list = sorted(self._subtitle_mgr.data[x].keys())
                for start in start_list:
                    end = self._subtitle_mgr.data[x][start][0] + start
                    for position in range(select_range[0], select_range[-1] + 1):
                        if start <= position and position < end:
                            try:
                                del self._subtitle_mgr.data[x][start]
                            except:
                                pass
            for x in x_list:
                for y in range(y_list[0], y_list[1] + 1):
                    if self._table.item(y, x):
                        self._table.setSpan(y, x, 1, 1)
                        self._table.setItem(y, x, QTableWidgetItem(''))
                        self._table.item(y, x).setBackground(QColor('#232629'))
            self._update_backend()

        elif action == set_span:  # 合并（与DD烤肉机一致）
            if y_list[0] < y_list[-1]:
                for x in x_list:
                    first_item = ''
                    for y in range(y_list[0], y_list[1] + 1):
                        if self._table.item(y, x):
                            if self._table.item(y, x).text():
                                first_item = self._table.item(y, x).text()
                                break
                    for y in range(y_list[0], y_list[1] + 1):
                        if self._table.rowSpan(y, x) > 1:
                            self._table.setSpan(y, x, 1, 1)
                    self._table.setItem(y_list[0], x, QTableWidgetItem(first_item))
                    self._table.item(y_list[0], x).setTextAlignment(Qt.AlignTop)
                    self._table.setSpan(y_list[0], x, y_list[1] - y_list[0] + 1, 1)
                    self._table.item(y_list[0], x).setBackground(SUBTITLE_COLORS["normal"])
                    self._set_subtitle_dict(y_list[0], x, y_list[1] - y_list[0] + 1, first_item, concat=True)

        elif action == cut_span:  # 切割（与DD烤肉机一致）
            y = y_list[0]
            cut_token = False
            select_time = int((y + self._row) * self._global_interval)
            copy_dict = copy.deepcopy(self._subtitle_mgr.data)
            for x in copy_dict.keys():
                for start, sub_data in copy_dict[x].items():
                    delta, text = sub_data
                    if select_time >= start and select_time <= start + delta:
                        cut_token = True
                        self._subtitle_mgr.data[x][start] = [select_time - start, text]
                        self._subtitle_mgr.data[x][select_time] = [start + delta - select_time, text]
            if cut_token:
                self._refresh_table()
                self._update_backend()

        elif action == clr_span:  # 拆分（与DD烤肉机一致）
            clear_token = False
            for x in x_list:
                start_list = sorted(self._subtitle_mgr.data[x].keys())
                for cnt, start in enumerate(start_list):
                    delta, text = self._subtitle_mgr.data[x][start]
                    select_list = [int((y + self._row) * self._global_interval) for y in range(y_list[0], y_list[1] + 1)]
                    for select in select_list:
                        if select >= start and select < start + delta:
                            clear_token = True
                            for i in range(int(delta / self._global_interval)):
                                self._subtitle_mgr.data[x][start] = [int(self._global_interval), text]
                                start += int(self._global_interval)
            if clear_token:
                self._refresh_table()
                self._update_backend()

    def _set_subtitle_dict(self, row, col, repeat, text, concat=False, delete=False):
        """更新字典 - 完全照搬DD烤肉机的实现"""
        new_s_row = row + self._row
        new_e_row = new_s_row + repeat
        new_s = int(new_s_row * self._global_interval)
        new_e = int(new_e_row * self._global_interval)
        start_end = [99999999, 0]
        old_start_end = [99999999, 0]
        key_list = copy.deepcopy(list(self._subtitle_mgr.data[col].keys()))

        for old_s in key_list:
            old_e = self._subtitle_mgr.data[col][old_s][0] + old_s
            if (new_s <= old_s and new_e > old_s + int(self._global_interval)) or \
                    (new_s < old_e - int(self._global_interval) and new_e >= old_e):
                del self._subtitle_mgr.data[col][old_s]
                if old_s < old_start_end[0]:
                    old_start_end[0] = old_s
                if old_e > old_start_end[1]:
                    old_start_end[1] = old_e
            if concat:
                if new_s > old_s and new_s < old_e - int(self._global_interval):
                    new_s = old_s
                    if old_s < start_end[0]:
                        start_end[0] = old_s
                if new_e > old_s + int(self._global_interval) and new_e < old_e:
                    new_e = old_e
                    if old_e > start_end[1]:
                        start_end[1] = old_e

        if concat:
            if start_end[0] != 99999999 and start_end[1]:
                self._subtitle_mgr.data[col][start_end[0]] = [start_end[1] - start_end[0], text]
            else:
                start = new_s
                end = new_e
                sub_start_list = sorted(self._subtitle_mgr.data[col].keys())
                for sub_start in sub_start_list:
                    sub_end = self._subtitle_mgr.data[col][sub_start][0] + sub_start
                    if start < sub_end and end > sub_end:
                        start = sub_end
                    if end > sub_start and end < sub_end:
                        end = sub_start
                self._subtitle_mgr.data[col][int(start)] = [int(end - start), text]
        elif old_start_end[0] != 99999999 and old_start_end[1]:
            start, end = old_start_end
            sub_start_list = sorted(self._subtitle_mgr.data[col].keys())
            for sub_start in sub_start_list:
                sub_end = self._subtitle_mgr.data[col][sub_start][0] + sub_start
                if start < sub_end and end > sub_end:
                    start = sub_end
                if end > sub_start and end < sub_end:
                    end = sub_start
            self._subtitle_mgr.data[col][start] = [end - start, text]
        else:
            start = new_s
            end = new_e
            self._subtitle_mgr.data[col][round(start)] = [round(end - start), text]

        if delete:
            try:
                del self._subtitle_mgr.data[col][new_s]
            except:
                pass

        self._update_backend()

    def _update_backend(self):
        """保存修改记录 - 完全照搬DD烤肉机的实现"""
        selected = self._table.selectionModel().selection().indexes()
        if selected:
            y = selected[0].row()
        else:
            y = 0
        scroll_value = self._scrollbar.value()
        self._subtitle_backend = self._subtitle_backend[:self._subtitle_backend_point + 1]
        self._subtitle_backend.append([
            copy.deepcopy(self._subtitle_mgr.data),
            self._player_position,
            y,
            scroll_value
        ])
        self._subtitle_backend_point = len(self._subtitle_backend) - 1
        if len(self._subtitle_backend) > 100:
            self._subtitle_backend.pop(0)
        self.subtitle_changed.emit()

    # ========== 公有方法 ==========

    def set_player_position(self, ms: int):
        """设置播放器位置"""
        print(f"[DEBUG] set_player_position: ms={ms}, follow_player={self._follow_player}, old_row={self._row}")
        self._player_position = ms
        if self._follow_player:
            self._row = int(ms / self._global_interval)
            print(f"[DEBUG] set_player_position: new_row={self._row}")
        # 刷新表格，禁用鼠标跟随
        self._is_wheel_scrolling = True
        self._refresh_table()
        # 延迟重置标志，确保所有 pending 的 cellEntered 信号都被忽略
        QTimer.singleShot(100, lambda: setattr(self, '_is_wheel_scrolling', False))

    def set_interval(self, interval_ms: float):
        """设置间隔"""
        self._global_interval = interval_ms
        self._refresh_table()

    def get_interval(self) -> float:
        """获取当前间隔"""
        return self._global_interval

    def set_duration(self, duration_ms: int):
        """设置视频时长"""
        self._total_logical_rows = int(duration_ms / self._global_interval) + 1
        self._refresh_table()

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
        self._row = int(ms / self._global_interval)
        max_row = max(0, self._total_logical_rows - VISIBLE_ROWS)
        self._row = min(self._row, max_row)
        self._row = max(0, self._row)
        self._refresh_table()

    # ========== 快捷键操作 ==========

    def keyPressEvent(self, event):
        """处理快捷键 - 完全照搬DD烤肉机的实现"""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Left:
            # ←键倒退1行
            position = self._player_position - self._global_interval
            if position < 0:
                position = 0
            self.position_jump_requested.emit(int(position))
        elif key == Qt.Key_Right:
            # →键前进1行
            position = self._player_position + self._global_interval
            if position > self._total_logical_rows * self._global_interval:
                position = self._total_logical_rows * self._global_interval
            self.position_jump_requested.emit(int(position))
        elif key == Qt.Key_Space:
            event.ignore()
            return
        elif key == Qt.Key_Delete:
            # 删除选中字幕
            selected = self._table.selectionModel().selection().indexes()
            if selected:
                x_list = []
                for i in range(len(selected)):
                    x = selected[i].column()
                    if x not in x_list:
                        x_list.append(x)
                y_list = [selected[0].row(), selected[-1].row()]
                select_range = [int((y + self._row) * self._global_interval) for y in y_list]
                for x in x_list:
                    start_list = sorted(self._subtitle_mgr.data[x].keys())
                    for start in start_list:
                        end = self._subtitle_mgr.data[x][start][0] + start
                        for position in range(select_range[0], select_range[-1] + 1):
                            if start <= position and position < end:
                                try:
                                    del self._subtitle_mgr.data[x][start]
                                except:
                                    pass
                for x in x_list:
                    for y in range(y_list[0], y_list[1] + 1):
                        if self._table.item(y, x):
                            self._table.setSpan(y, x, 1, 1)
                            self._table.setItem(y, x, QTableWidgetItem(''))
                            self._table.item(y, x).setBackground(QColor('#232629'))
                self._update_backend()
        elif modifiers == Qt.ControlModifier and key == Qt.Key_Z:
            # 撤回
            if self._subtitle_backend_point > 0:
                self._subtitle_backend_point -= 1
                backup_data = copy.deepcopy(self._subtitle_backend[self._subtitle_backend_point])
                self._subtitle_mgr.data, self._player_position, y, scroll_value = backup_data
                self._refresh_table(int(self._player_position), y, scroll_value)
        elif modifiers == Qt.ControlModifier and key == Qt.Key_Y:
            # 取消撤回
            if self._subtitle_backend_point < len(self._subtitle_backend) - 1:
                self._subtitle_backend_point += 1
                backup_data = copy.deepcopy(self._subtitle_backend[self._subtitle_backend_point])
                self._subtitle_mgr.data, self._player_position, y, scroll_value = backup_data
                self._refresh_table(int(self._player_position), y, scroll_value)
        elif key in [Qt.Key_Q, Qt.Key_W, Qt.Key_E, Qt.Key_R, Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4]:
            # 调整轴端点
            try:
                selected = self._table.selectionModel().selection().indexes()
                if selected:
                    x = selected[0].column()
                    if len(selected) == 1:
                        y = selected[0].row()
                        y_list = [y, y + self._table.rowSpan(y, x) - 1]
                    else:
                        y_list = [selected[0].row(), selected[-1].row()]
                    select = (y_list[0] + self._row) * self._global_interval
                    start_list = sorted(self._subtitle_mgr.data[x].keys())
                    for cnt, start in enumerate(start_list):
                        delta, text = self._subtitle_mgr.data[x][start]
                        if select >= start and select < start + delta:
                            if key in [Qt.Key_Q, Qt.Key_1]:
                                # 左端左移
                                if start >= self._global_interval:
                                    self._subtitle_mgr.data[x][start] = [int(delta + self._global_interval), text]
                                    del self._subtitle_mgr.data[x][start]
                                    start -= int(self._global_interval)
                                    self._subtitle_mgr.data[x][start] = [int(delta + self._global_interval), text]
                            elif key in [Qt.Key_W, Qt.Key_2]:
                                # 左端右移
                                if delta > self._global_interval:
                                    del self._subtitle_mgr.data[x][start]
                                    start += int(self._global_interval)
                                    self._subtitle_mgr.data[x][start] = [int(delta - self._global_interval), text]
                            elif key in [Qt.Key_E, Qt.Key_3]:
                                # 右端左移
                                if delta > self._global_interval:
                                    self._subtitle_mgr.data[x][start] = [delta - int(self._global_interval), text]
                            elif key in [Qt.Key_R, Qt.Key_4]:
                                # 右端右移
                                self._subtitle_mgr.data[x][start] = [int(delta + self._global_interval), text]
                            self._update_backend()
                            self._refresh_table()
                            break
            except Exception as e:
                print(str(e))
        elif key == Qt.Key_5:
            # 切割
            selected = self._table.selectionModel().selection().indexes()
            if selected:
                y = selected[0].row()
                cut_token = False
                select_time = int((y + self._row) * self._global_interval)
                copy_dict = copy.deepcopy(self._subtitle_mgr.data)
                for x in copy_dict.keys():
                    for start, sub_data in copy_dict[x].items():
                        delta, text = sub_data
                        if select_time >= start and select_time <= start + delta:
                            cut_token = True
                            self._subtitle_mgr.data[x][start] = [select_time - start, text]
                            self._subtitle_mgr.data[x][select_time] = [start + delta - select_time, text]
                if cut_token:
                    self._refresh_table(int(self._row * self._global_interval), y, self._scrollbar.value())
                    self._update_backend()

        super().keyPressEvent(event)

    # ========== 字幕条操作 ==========

    def create_subtitle_at_cursor(self):
        """在光标位置创建新字幕条"""
        selected = self._table.selectionModel().selection().indexes()
        if not selected:
            return
        row = selected[0].row()
        col = selected[0].column()
        start_time = int((row + self._row) * self._global_interval)
        duration = int(self._global_interval * 10)
        self._subtitle_mgr.data[col][start_time] = [duration, ""]
        self._refresh_table()
        self._update_backend()

    def set_subtitle_text(self, col: int, start: int, text: str):
        """设置字幕文本"""
        if start in self._subtitle_mgr.data[col]:
            self._subtitle_mgr.data[col][start][1] = text
            self._refresh_table()
            self._update_backend()

    def _split_at_cursor(self):
        """在光标位置切割字幕条"""
        selected = self._table.selectionModel().selection().indexes()
        if not selected:
            return
        y = selected[0].row()
        cut_token = False
        select_time = int((y + self._row) * self._global_interval)
        copy_dict = copy.deepcopy(self._subtitle_mgr.data)
        for x in copy_dict.keys():
            for start, sub_data in copy_dict[x].items():
                delta, text = sub_data
                if select_time >= start and select_time <= start + delta:
                    cut_token = True
                    self._subtitle_mgr.data[x][start] = [select_time - start, text]
                    self._subtitle_mgr.data[x][select_time] = [start + delta - select_time, text]
        if cut_token:
            self._refresh_table(int(self._row * self._global_interval), y, self._scrollbar.value())
            self._update_backend()

    def _undo(self):
        """撤销"""
        if self._subtitle_backend_point > 0:
            self._subtitle_backend_point -= 1
            backup_data = copy.deepcopy(self._subtitle_backend[self._subtitle_backend_point])
            self._subtitle_mgr.data, self._player_position, y, scroll_value = backup_data
            self._refresh_table(int(self._player_position), y, scroll_value)

    def _redo(self):
        """重做"""
        if self._subtitle_backend_point < len(self._subtitle_backend) - 1:
            self._subtitle_backend_point += 1
            backup_data = copy.deepcopy(self._subtitle_backend[self._subtitle_backend_point])
            self._subtitle_mgr.data, self._player_position, y, scroll_value = backup_data
            self._refresh_table(int(self._player_position), y, scroll_value)

    def jump_to_position_at_top(self, ms: int):
        """跳转到指定时间位置，显示在可视行顶部"""
        self._row = int(ms / self._global_interval)
        max_row = max(0, self._total_logical_rows - VISIBLE_ROWS)
        self._row = min(self._row, max_row)
        self._row = max(0, self._row)
        self._refresh_table()
