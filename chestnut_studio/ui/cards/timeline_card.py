"""打轴编辑卡片模块

功能：
- 显示已打轴的字幕列表（编号 + 起止时间 + 时长 + 操作按钮）
- 提供查看（跳转起始点）、编辑（调整区间）、锁定功能
- 支持撤销/重做
- 与音频波形区联动
"""

import copy

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.subtitle import SubtitleManager
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


class TimelineCard(QDockWidget):
    """打轴编辑卡片

    功能：
    - 显示已打轴的字幕列表（编号 + 起止时间 + 时长 + 操作按钮）
    - 查看：跳转到字幕起始点
    - 编辑：弹出对话框调整前后区间
    - 锁定：切换锁定状态
    - 撤销/重做

    信号：
    - jump_to_position(ms): 跳转到指定位置
    - subtitle_changed(): 字幕数据变化（用于同步波形覆盖）
    - subtitle_selected(col, text): 字幕被选中（用于翻译面板）
    """

    # 信号
    jump_to_position = Signal(int)  # 跳转到指定位置 (ms)
    subtitle_changed = Signal()  # 字幕数据变化
    subtitle_selected = Signal(int, str)  # 字幕被选中 (col, text)

    # 默认停靠区域
    default_area = Qt.RightDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("时间轴", parent)
        self._subtitle_mgr = SubtitleManager()
        self._duration_ms = 0

        # 锁定状态集合 {(col, start_ms), ...}
        self._locked_states: set[tuple[int, int]] = set()

        # 撤销/重做后端
        self._backend: list[tuple[dict, set]] = []  # [(subtitle_data, locked_states), ...]
        self._backend_point: int = -1

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

        # --- 字幕列表表格 ---
        self._table = QTableWidget(0, 5, self)
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
        self._table.setSelectionMode(QTableWidget.SingleSelection)

        # 设置列头
        self._table.setHorizontalHeaderLabels(["#", "开始时间", "结束时间", "时长", "操作"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self._table.setColumnWidth(0, 36)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self._table.setColumnWidth(4, 130)

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

        # 全部锁定/解锁按钮
        self._lock_all_btn = QPushButton("全部锁定")
        self._lock_all_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._lock_all_btn.clicked.connect(self._lock_all)

        self._unlock_all_btn = QPushButton("全部解锁")
        self._unlock_all_btn.setStyleSheet(TOOL_BTN_STYLE)
        self._unlock_all_btn.clicked.connect(self._unlock_all)

        bottom_layout.addWidget(self._count_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self._undo_btn)
        bottom_layout.addWidget(self._redo_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self._lock_all_btn)
        bottom_layout.addWidget(self._unlock_all_btn)

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

        # 收集所有字幕条（跨所有轨道）
        all_subtitles: list[tuple[int, int, int, str]] = []  # (start, duration, col, text)
        for col, sub_data in self._subtitle_mgr.data.items():
            for start, (duration, text) in sub_data.items():
                all_subtitles.append((start, duration, col, text))

        # 按开始时间排序
        all_subtitles.sort(key=lambda x: x[0])

        # 填充表格
        for idx, (start, duration, col, text) in enumerate(all_subtitles):
            row = self._table.rowCount()
            self._table.insertRow(row)

            is_locked = (col, start) in self._locked_states

            # # 列（编号）
            num_item = QTableWidgetItem(str(idx + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setData(Qt.UserRole, (col, start))
            self._table.setItem(row, 0, num_item)

            # 开始时间
            start_item = QTableWidgetItem(ms_to_time_str(start))
            start_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 1, start_item)

            # 结束时间
            end_item = QTableWidgetItem(ms_to_time_str(start + duration))
            end_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, end_item)

            # 时长
            duration_item = QTableWidgetItem(f"{duration / 1000:.2f}s")
            duration_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, duration_item)

            # 操作按钮
            op_widget = self._create_operation_buttons(col, start, is_locked)
            self._table.setCellWidget(row, 4, op_widget)

            # 设置行颜色
            if is_locked:
                bg_color = QColor(255, 255, 255, 15)  # 锁定时微亮
            elif duration < 100 or duration > 8000:
                bg_color = QColor(178, 34, 34, 40)  # 异常：红色
            elif duration > 4500:
                bg_color = QColor(250, 128, 114, 30)  # 过长：橙色
            else:
                bg_color = QColor(53, 84, 93, 40)  # 正常：蓝色

            for col_idx in range(5):
                item = self._table.item(row, col_idx)
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
        """创建操作按钮组（查看 / 编辑 / 锁定）"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # 查看按钮
        view_btn = QPushButton("查看")
        view_btn.setStyleSheet(OP_BTN_STYLE)
        view_btn.setToolTip("跳转到字幕起始点")
        view_btn.setFixedSize(36, 22)
        view_btn.clicked.connect(lambda checked, s=start: self._on_view_clicked(s))
        layout.addWidget(view_btn)

        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet(OP_BTN_STYLE)
        edit_btn.setToolTip("编辑字幕区间")
        edit_btn.setFixedSize(36, 22)
        edit_btn.clicked.connect(lambda checked, c=col, s=start: self._on_edit_clicked(c, s))
        layout.addWidget(edit_btn)

        # 锁定按钮
        lock_btn = QPushButton("锁定" if not is_locked else "解锁")
        lock_btn.setStyleSheet(LOCK_ACTIVE_STYLE if is_locked else OP_BTN_STYLE)
        lock_btn.setToolTip("切换锁定状态")
        lock_btn.setFixedSize(36, 22)
        lock_btn.clicked.connect(lambda checked, c=col, s=start: self._on_lock_clicked(c, s))
        layout.addWidget(lock_btn)

        layout.addStretch()
        return widget

    # ========== 操作回调 ==========

    def _on_view_clicked(self, start_ms: int):
        """查看按钮：跳转到字幕起始点"""
        self.jump_to_position.emit(start_ms)

    def _on_edit_clicked(self, col: int, start_ms: int):
        """编辑按钮：弹出编辑对话框"""
        if (col, start_ms) in self._locked_states:
            return  # 锁定状态不可编辑

        subtitle = self._subtitle_mgr.get(col, start_ms)
        if subtitle is None:
            return

        duration, text = subtitle
        end_ms = start_ms + duration

        # 弹出编辑对话框
        from chestnut_studio.ui.dialogs.edit_subtitle_dialog import EditSubtitleDialog

        dialog = EditSubtitleDialog(start_ms, end_ms, self._duration_ms, self)
        if dialog.exec():
            new_start, new_end = dialog.get_result()
            if new_start != start_ms or new_end != end_ms:
                # 保存撤销点
                self._push_undo()
                # 删除旧条目，创建新条目
                self._subtitle_mgr.delete(col, start_ms)
                new_duration = new_end - new_start
                self._subtitle_mgr.set(col, new_start, new_duration, text)
                self._update_table()
                self.subtitle_changed.emit()

    def _on_lock_clicked(self, col: int, start_ms: int):
        """锁定按钮：切换锁定状态"""
        key = (col, start_ms)
        if key in self._locked_states:
            self._locked_states.discard(key)
        else:
            self._locked_states.add(key)
        self._update_table()

    def _on_double_click(self, index):
        """双击行：跳转到字幕起始点"""
        row = index.row()
        num_item = self._table.item(row, 0)
        if num_item:
            data = num_item.data(Qt.UserRole)
            if data:
                col, start = data
                self.jump_to_position.emit(start)
                self.subtitle_selected.emit(col, self._subtitle_mgr.data[col].get(start, [0, ""])[1])

    # ========== 撤销/重做 ==========

    def _push_undo(self):
        """保存当前状态到撤销栈"""
        state = (
            copy.deepcopy(self._subtitle_mgr.data),
            copy.deepcopy(self._locked_states),
        )
        self._backend = self._backend[: self._backend_point + 1]
        self._backend.append(state)
        self._backend_point = len(self._backend) - 1
        if len(self._backend) > 100:
            self._backend.pop(0)
            self._backend_point -= 1
        self._update_undo_redo_buttons()

    def _undo(self):
        """撤销"""
        if self._backend_point > 0:
            self._backend_point -= 1
            data, locked = copy.deepcopy(self._backend[self._backend_point])
            self._subtitle_mgr._data = data
            self._locked_states = locked
            self._update_table()
            self.subtitle_changed.emit()

    def _redo(self):
        """重做"""
        if self._backend_point < len(self._backend) - 1:
            self._backend_point += 1
            data, locked = copy.deepcopy(self._backend[self._backend_point])
            self._subtitle_mgr._data = data
            self._locked_states = locked
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
        self._update_table()

    def _unlock_all(self):
        """解锁所有字幕"""
        self._locked_states.clear()
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

        super().keyPressEvent(event)

    # ========== 公有方法 ==========

    def set_duration(self, duration_ms: int):
        """设置视频时长"""
        self._duration_ms = duration_ms

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
        # 保存撤销点
        self._push_undo()

        duration = end_ms - start_ms
        self._subtitle_mgr.set(col, start_ms, duration, "")
        self._update_table()
        self.subtitle_changed.emit()

    def set_subtitle_text(self, col: int, start_ms: int, text: str):
        """设置字幕文本"""
        if start_ms in self._subtitle_mgr.data[col]:
            if (col, start_ms) in self._locked_states:
                return  # 锁定状态不可编辑
            duration = self._subtitle_mgr.data[col][start_ms][0]
            self._push_undo()
            self._subtitle_mgr.data[col][start_ms] = [duration, text]
            self._update_table()
            self.subtitle_changed.emit()
