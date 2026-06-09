"""笔记列表面板模块

视频播放器右侧的笔记列表，按类型分组显示。
"""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.note_manager import Note, NoteManager
from chestnut_studio.core.track_config import NOTE_TYPES, get_track_color
from chestnut_studio.utils import get_logger, log_operation
from chestnut_studio.utils.time_utils import ms_to_time_str

logger = get_logger("UI")


class _NoteListWidget(QListWidget):
    """支持 Delete 键删除的 QListWidget 子类"""

    delete_requested = Signal()
    m_pressed = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.delete_requested.emit()
        elif event.key() == Qt.Key_M:
            self.m_pressed.emit()
        else:
            super().keyPressEvent(event)


class NoteItemWidget(QWidget):
    """单条笔记的显示控件"""

    def __init__(self, note: Note, note_id: int = 0, parent=None):
        super().__init__(parent)
        self.note = note
        self._note_id = note_id
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # 序号
        id_label = QLabel(f"#{self._note_id}" if self._note_id else "")
        id_label.setObjectName("noteId")
        id_label.setFixedWidth(28)
        layout.addWidget(id_label)

        # 时间戳标签（按轨道区分颜色）
        time_label = QLabel(ms_to_time_str(self.note.timestamp_ms))
        time_label.setObjectName("noteTime")
        time_label.setFixedWidth(52)
        color = get_track_color(NOTE_TYPES.index(self.note.type) + 1)
        time_label.setStyleSheet(f"color: {color};")
        layout.addWidget(time_label)

        # 笔记文本（可换行）
        text_label = QLabel(self.note.text)
        text_label.setObjectName("noteText")
        text_label.setWordWrap(True)
        text_label.setMinimumHeight(16)
        layout.addWidget(text_label, 1)


class NotePanel(QWidget):
    """笔记列表面板

    显示按类型分组的笔记列表，支持点击跳转和右键删除。
    """

    jump_to_position = Signal(int)  # 双击笔记跳转到视频位置
    edit_requested = Signal(str, str)  # 双击笔记载入输入框 (type, text)
    term_requested = Signal(str, str)  # 打开术语录入 (note_text, origin)

    def __init__(self, note_manager: NoteManager, parent=None):
        super().__init__(parent)
        self._note_manager = note_manager
        self._sort_mode = "time"  # "time" | "track"
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("notePanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 标题栏 ──
        title_bar = QWidget()
        title_bar.setObjectName("notePanelTitle")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 8, 12, 8)

        title_label = QLabel("笔记")
        title_label.setObjectName("notePanelTitleText")
        title_layout.addWidget(title_label)

        self._count_label = QLabel("0")
        self._count_label.setObjectName("notePanelCount")
        title_layout.addWidget(self._count_label)

        self._sort_btn = QPushButton("轨道")  # 初始时间排序，点此切换到轨道
        self._sort_btn.setObjectName("sortBtn")
        self._sort_btn.setCursor(Qt.PointingHandCursor)
        self._sort_btn.clicked.connect(self._toggle_sort)
        title_layout.addWidget(self._sort_btn)

        title_layout.addStretch()

        self._term_btn = QPushButton("术语")
        self._term_btn.setObjectName("termBtn")
        self._term_btn.setCursor(Qt.PointingHandCursor)
        self._term_btn.clicked.connect(self._on_term_requested)
        title_layout.addWidget(self._term_btn)

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setObjectName("clearBtn")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_all)
        title_layout.addWidget(self._clear_btn)

        layout.addWidget(title_bar)

        # ── 笔记列表 ──
        self._list = _NoteListWidget()
        self._list.setObjectName("noteList")
        self._list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self._list.itemDoubleClicked.connect(self._on_item_clicked)
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_context_menu)
        self._list.delete_requested.connect(self._delete_selected)
        self._list.m_pressed.connect(self._on_term_requested)
        layout.addWidget(self._list, 1)

        # ── 空状态提示 ──
        self._empty_label = QLabel("暂无笔记\n在下方输入并发送")
        self._empty_label.setObjectName("noteEmptyLabel")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setWordWrap(True)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

    @log_operation("切换排序")
    def _toggle_sort(self):
        """切换排序方式"""
        self._sort_mode = "track" if self._sort_mode == "time" else "time"
        self._sort_btn.setText("轨道" if self._sort_mode == "time" else "时间")
        self.refresh()

    def refresh(self):
        """刷新笔记列表显示"""
        scroll_bar = self._list.verticalScrollBar()
        scroll_pos = scroll_bar.value() if self._list.count() else 0
        at_bottom = scroll_pos >= scroll_bar.maximum() - 5 if self._list.count() else False
        self._list.clear()
        self._count_label.setText(str(self._note_manager.count()))

        if self._note_manager.count() == 0:
            self._empty_label.show()
            return
        self._empty_label.hide()

        if self._sort_mode == "track":
            self._refresh_by_track()
        else:
            self._refresh_by_time()
        self._recalc_item_heights()
        if at_bottom:
            scroll_bar.setValue(scroll_bar.maximum())
        else:
            scroll_bar.setValue(scroll_pos)

    def _add_note_item(self, note: Note):
        """添加一条笔记到列表"""
        item = QListWidgetItem()
        item.setData(Qt.UserRole, id(note))
        note_id = self._note_manager.get_note_id(note)
        widget = NoteItemWidget(note, note_id)
        # 估算多行文本所需高度（初始值，resize 时会重新计算）
        est_lines = max(1, (len(note.text) + 11) // 12)
        h = max(36, 18 + est_lines * 18)
        item.setSizeHint(QSize(0, h))
        self._list.addItem(item)
        self._list.setItemWidget(item, widget)

    def _refresh_by_time(self):
        """按时间排序（不分组）"""
        for note in self._note_manager.get_all():
            self._add_note_item(note)

    def _refresh_by_track(self):
        """按轨道分组排序"""
        for note_type in NOTE_TYPES:
            notes = self._note_manager.get_by_type(note_type)
            if not notes:
                continue

            # 类型分组标题
            group_item = QListWidgetItem()
            group_widget = QWidget()
            group_layout = QHBoxLayout(group_widget)
            group_layout.setContentsMargins(8, 2, 8, 2)
            group_label = QLabel(f"── {note_type} ──")
            group_label.setObjectName("noteGroupLabel")
            color = get_track_color(NOTE_TYPES.index(note_type) + 1)
            group_label.setStyleSheet(f"color: {color};")
            group_layout.addWidget(group_label)
            group_layout.addStretch()
            group_item.setSizeHint(group_widget.sizeHint())
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsSelectable)
            self._list.addItem(group_item)
            self._list.setItemWidget(group_item, group_widget)

            for note in notes:
                self._add_note_item(note)

    def resizeEvent(self, event):
        """窗口大小变化时重新计算笔记高度"""
        super().resizeEvent(event)
        self._recalc_item_heights()

    def _recalc_item_heights(self):
        """根据当前列表宽度重新估算每条笔记的高度"""
        available_width = self._list.viewport().width() - 102  # 减去序号+时间+边距
        chars_per_line = max(8, available_width // 12)  # 中文字符约 12px
        for i in range(self._list.count()):
            item = self._list.item(i)
            widget = self._list.itemWidget(item)
            if isinstance(widget, NoteItemWidget):
                est_lines = max(1, (len(widget.note.text) + chars_per_line - 1) // chars_per_line)
                h = max(36, 18 + est_lines * 18)
                item.setSizeHint(QSize(0, h))

    def _on_item_clicked(self, item: QListWidgetItem):
        """双击笔记：跳转视频位置 + 载入输入框"""
        widget = self._list.itemWidget(item)
        if isinstance(widget, NoteItemWidget):
            self.jump_to_position.emit(widget.note.timestamp_ms)
            self.edit_requested.emit(widget.note.type, widget.note.text)

    def _show_context_menu(self, pos):
        """右键菜单：删除笔记"""
        item = self._list.itemAt(pos)
        if not item:
            return
        widget = self._list.itemWidget(item)
        if not isinstance(widget, NoteItemWidget):
            return

        menu = QMenu(self)
        term_action = menu.addAction("术语 (M)")
        menu.addSeparator()
        delete_action = menu.addAction("删除笔记 (Delete)")
        action = menu.exec(self._list.mapToGlobal(pos))
        if action == term_action:
            self._on_term_requested()
        elif action == delete_action:
            self._note_manager.remove(widget.note)
            self.refresh()

    def _on_term_requested(self):
        """选中笔记后打开术语录入"""
        item = self._list.currentItem()
        if not item:
            return
        widget = self._list.itemWidget(item)
        if isinstance(widget, NoteItemWidget):
            self.term_requested.emit(widget.note.text, f"#{self._note_manager.get_note_id(widget.note)}")

    def _delete_selected(self):
        """删除当前选中的笔记"""
        item = self._list.currentItem()
        if not item:
            return
        widget = self._list.itemWidget(item)
        if isinstance(widget, NoteItemWidget):
            self._note_manager.remove(widget.note)
            self.refresh()

    @log_operation("清空笔记")
    def _clear_all(self):
        """清空所有笔记和术语（需确认）"""
        reply = QMessageBox.question(
            self,
            "清空所有笔记",
            "将清空所有笔记和术语，此操作不可撤销。\n确定继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._note_manager.clear_terms()
        self._note_manager.clear()
        self.refresh()
