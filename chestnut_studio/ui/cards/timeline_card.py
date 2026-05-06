"""打轴编辑卡片模块 - 简化版，使用音频图+快捷键打轴"""

import copy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
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


class TimelineCard(QDockWidget):
    """打轴编辑卡片 - 简化版

    功能：
    - 显示字幕列表（只读）
    - 通过音频图调整位置
    - 通过快捷键打轴
    - 右键菜单编辑字幕
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
        self._duration_ms = 0
        self._player_position = 0
        
        # 撤销/重做后端
        self._subtitle_backend = []
        self._subtitle_backend_point = 0

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

        # 创建字幕列表表格（只读）
        self._table = QTableWidget(0, 4, self)
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
        """)

        # 设置表格属性
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 设置列头
        self._table.setHorizontalHeaderLabels(["轨道1", "轨道2", "轨道3", "轨道4"])
        self._table.horizontalHeader().setStretchLastSection(True)
        
        # 连接信号
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)

        # 布局
        layout.addWidget(self._table)
        self.setWidget(content)

    def _update_table(self):
        """更新字幕列表"""
        self._table.setRowCount(0)
        
        # 收集所有字幕
        all_subtitles = []
        for col, sub_data in self._subtitle_mgr.data.items():
            for start, (delta, text) in sub_data.items():
                all_subtitles.append((start, delta, text, col))
        
        # 按开始时间排序
        all_subtitles.sort(key=lambda x: x[0])
        
        # 填充表格
        for start, delta, text, col in all_subtitles:
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            # 开始时间
            start_item = QTableWidgetItem(ms_to_time_str(start))
            start_item.setData(Qt.UserRole, (start, col))
            self._table.setItem(row, 0, start_item)
            
            # 结束时间
            end_item = QTableWidgetItem(ms_to_time_str(start + delta))
            self._table.setItem(row, 1, end_item)
            
            # 持续时间
            duration_item = QTableWidgetItem(f"{delta/1000:.2f}s")
            self._table.setItem(row, 2, duration_item)
            
            # 文本
            text_item = QTableWidgetItem(text)
            self._table.setItem(row, 3, text_item)
            
            # 设置颜色
            color = QColor(53, 84, 93)  # 正常
            if delta < 100 or delta > 8000:
                color = QColor(178, 34, 34)  # 异常
            elif delta > 4500:
                color = QColor(250, 128, 114)  # 过长
            
            for col_idx in range(4):
                self._table.item(row, col_idx).setBackground(color)

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 获取选中的行
        selected = self._table.selectedItems()
        if selected:
            row = selected[0].row()
            start_item = self._table.item(row, 0)
            if start_item:
                start, col = start_item.data(Qt.UserRole)
                
                # 编辑字幕文本
                edit_action = QAction("编辑字幕文本", self)
                edit_action.triggered.connect(lambda: self._edit_subtitle_text(col, start))
                menu.addAction(edit_action)
                
                # 删除字幕
                delete_action = QAction("删除字幕", self)
                delete_action.triggered.connect(lambda: self._delete_subtitle(col, start))
                menu.addAction(delete_action)
                
                menu.addSeparator()
        
        # 创建新字幕
        create_action = QAction("在当前位置创建字幕", self)
        create_action.triggered.connect(self._create_subtitle_at_cursor)
        menu.addAction(create_action)
        
        menu.addSeparator()
        
        # 撤销/重做
        undo_action = QAction("撤销", self)
        undo_action.triggered.connect(self._undo)
        menu.addAction(undo_action)
        
        redo_action = QAction("重做", self)
        redo_action.triggered.connect(self._redo)
        menu.addAction(redo_action)
        
        menu.exec_(self._table.viewport().mapToGlobal(pos))

    def _on_double_click(self, index):
        """双击跳转到字幕位置"""
        row = index.row()
        start_item = self._table.item(row, 0)
        if start_item:
            start, col = start_item.data(Qt.UserRole)
            self.position_jump_requested.emit(start)

    def _edit_subtitle_text(self, col, start):
        """编辑字幕文本"""
        if start not in self._subtitle_mgr.data[col]:
            return
        
        delta, text = self._subtitle_mgr.data[col][start]
        new_text, ok = QInputDialog.getText(self, "编辑字幕", "字幕文本:", text=text)
        
        if ok and new_text != text:
            self._subtitle_mgr.data[col][start] = [delta, new_text]
            self._update_backend()
            self._update_table()
            self.subtitle_changed.emit()

    def _delete_subtitle(self, col, start):
        """删除字幕"""
        if start not in self._subtitle_mgr.data[col]:
            return
        
        reply = QMessageBox.question(
            self, "删除字幕",
            "确定要删除这条字幕吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self._subtitle_mgr.data[col][start]
            self._update_backend()
            self._update_table()
            self.subtitle_changed.emit()

    def _create_subtitle_at_cursor(self):
        """在当前位置创建字幕"""
        start_time = int(self._player_position / self._global_interval) * int(self._global_interval)
        duration = int(self._global_interval * 10)
        col = 0  # 默认在第一列创建
        
        # 检查是否重叠
        for existing_start, (existing_delta, _) in self._subtitle_mgr.data[col].items():
            existing_end = existing_start + existing_delta
            if start_time < existing_end and start_time + duration > existing_start:
                QMessageBox.warning(self, "重叠检测", "该位置已有字幕，无法创建")
                return
        
        self._subtitle_mgr.data[col][start_time] = [duration, ""]
        self._update_backend()
        self._update_table()
        self.subtitle_changed.emit()

    def _update_backend(self):
        """保存修改记录"""
        self._subtitle_backend = self._subtitle_backend[:self._subtitle_backend_point + 1]
        self._subtitle_backend.append(copy.deepcopy(self._subtitle_mgr.data))
        self._subtitle_backend_point = len(self._subtitle_backend) - 1
        if len(self._subtitle_backend) > 100:
            self._subtitle_backend.pop(0)

    def _undo(self):
        """撤销"""
        if self._subtitle_backend_point > 0:
            self._subtitle_backend_point -= 1
            self._subtitle_mgr.data = copy.deepcopy(self._subtitle_backend[self._subtitle_backend_point])
            self._update_table()
            self.subtitle_changed.emit()

    def _redo(self):
        """重做"""
        if self._subtitle_backend_point < len(self._subtitle_backend) - 1:
            self._subtitle_backend_point += 1
            self._subtitle_mgr.data = copy.deepcopy(self._subtitle_backend[self._subtitle_backend_point])
            self._update_table()
            self.subtitle_changed.emit()

    def _split_at_cursor(self):
        """在光标位置切割字幕"""
        # 找到当前位置所在的字幕
        for col, sub_data in self._subtitle_mgr.data.items():
            for start, (delta, text) in list(sub_data.items()):
                end = start + delta
                if start <= self._player_position < end:
                    # 在当前位置切割
                    split_time = int(self._player_position / self._global_interval) * int(self._global_interval)
                    if split_time > start and split_time < end:
                        # 创建两个字幕
                        self._subtitle_mgr.data[col][start] = [split_time - start, text]
                        self._subtitle_mgr.data[col][split_time] = [end - split_time, text]
                        self._update_backend()
                        self._update_table()
                        self.subtitle_changed.emit()
                        return

    # ========== 公有方法 ==========

    def set_player_position(self, ms: int):
        """设置播放器位置"""
        self._player_position = ms

    def set_interval(self, interval_ms: float):
        """设置间隔"""
        self._global_interval = interval_ms

    def get_interval(self) -> float:
        """获取当前间隔"""
        return self._global_interval

    def set_duration(self, duration_ms: int):
        """设置视频时长"""
        self._duration_ms = duration_ms

    def get_subtitle_data(self) -> dict:
        """获取字幕数据"""
        return self._subtitle_mgr.data

    def get_subtitle_manager(self) -> SubtitleManager:
        """获取字幕管理器实例"""
        return self._subtitle_mgr

    def set_follow_player(self, follow: bool):
        """设置是否跟随播放位置"""
        pass  # 简化版不需要这个功能

    def is_following_player(self) -> bool:
        """是否跟随播放位置"""
        return False

    def jump_to_position(self, ms: int):
        """跳转到指定时间位置"""
        self._player_position = ms

    def jump_to_position_at_top(self, ms: int):
        """跳转到指定时间位置"""
        self._player_position = ms

    # ========== 快捷键操作 ==========

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

    # ========== 工具栏集成方法 ==========

    def create_subtitle_at_cursor(self):
        """在光标位置创建新字幕条"""
        self._create_subtitle_at_cursor()

    def set_subtitle_text(self, col: int, start: int, text: str):
        """设置字幕文本"""
        if start in self._subtitle_mgr.data[col]:
            delta = self._subtitle_mgr.data[col][start][0]
            self._subtitle_mgr.data[col][start] = [delta, text]
            self._update_backend()
            self._update_table()
            self.subtitle_changed.emit()
