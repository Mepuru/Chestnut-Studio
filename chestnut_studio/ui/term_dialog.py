"""术语编辑对话框组件

封装术语查看表格和编辑表单，消除 _show_terms / _show_shortcuts 之间的代码重复。
"""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.manager.note_manager import NoteManager
from chestnut_studio.core.model.note import Term
from chestnut_studio.utils import get_logger

logger = get_logger("UI")


def _parse_note(note: str) -> tuple[str, str, str]:
    """从 note 字段中提取原文上下文和参考资料

    Returns:
        (context, reference, rest_note)
    """
    ctx = ""
    ref = ""
    lines = note.split("\n")
    clean: list[str] = []
    for ln in lines:
        if ln.startswith("原文: "):
            ctx = ln[4:]
        elif ln.startswith("参考: "):
            ref = ln[4:]
        elif ln.strip():
            clean.append(ln)
    rest_note = "\n".join(clean)
    return ctx, ref, rest_note


def _build_note(context: str, reference: str, rest_note: str) -> str:
    """将上下文、参考资料和备注合并为 note 字段"""
    parts: list[str] = []
    if context:
        parts.append("原文: " + context)
    if reference:
        parts.append("参考: " + reference)
    if rest_note:
        parts.append(rest_note)
    return "\n".join(parts).strip()


class TermEditDialog(QDialog):
    """单个术语的编辑/新建对话框"""

    def __init__(
        self,
        parent: QWidget | None = None,
        term: Term | None = None,
        note_manager: NoteManager | None = None,
        context: str = "",
        origin: str = "",
    ):
        super().__init__(parent)
        self._note_manager = note_manager
        self._context = context
        self._origin = origin
        self._setup_ui(term)

    def _setup_ui(self, term: Term | None):
        self.setWindowTitle(f"编辑术语: {term.source}" if term else "新建术语")
        self.setMinimumSize(450, 420)
        self.setObjectName("termEditDialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # 从 term 提取各字段，新建时使用传入的上下文
        if term:
            ctx, ref, rest_note = _parse_note(term.note)
        else:
            ctx, ref, rest_note = self._context, "", ""

        # 原文上下文
        layout.addWidget(QLabel("原文（上下文）:"))
        self._context_edit = QLineEdit(ctx)
        layout.addWidget(self._context_edit)

        # 术语
        layout.addWidget(QLabel("术语（关键词）*:"))
        self._source_edit = QLineEdit(term.source if term else "")
        self._source_edit.setPlaceholderText("必填")
        layout.addWidget(self._source_edit)

        # 译文
        layout.addWidget(QLabel("译文（中文）*:"))
        self._trans_edit = QLineEdit(term.translation if term else "")
        self._trans_edit.setPlaceholderText("必填")
        layout.addWidget(self._trans_edit)

        # 出处
        layout.addWidget(QLabel("出处:"))
        self._origin_edit = QLineEdit(term.origin if term else self._origin)
        layout.addWidget(self._origin_edit)

        # 参考资料
        layout.addWidget(QLabel("参考资料:"))
        self._ref_edit = QLineEdit(ref)
        self._ref_edit.setPlaceholderText("词典/网站/工具书名称或链接...")
        layout.addWidget(self._ref_edit)

        # 备注
        layout.addWidget(QLabel("备注:"))
        self._note_edit = QTextEdit()
        self._note_edit.setPlainText(rest_note)
        self._note_edit.setAcceptRichText(False)
        self._note_edit.setMinimumHeight(80)
        layout.addWidget(self._note_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def accept(self):
        """验证必填字段后再保存"""
        if not self._source_edit.text().strip() or not self._trans_edit.text().strip():
            QMessageBox.warning(self, "保存术语", "术语和译文不能为空，请填写完整再保存。")
            return
        super().accept()

    def get_result(self) -> tuple[str, str, str, str] | None:
        """获取编辑结果

        Returns:
            (source, translation, origin, note) 或 None（取消）
        """
        new_s = self._source_edit.text().strip()
        new_t = self._trans_edit.text().strip()
        new_o = self._origin_edit.text().strip()
        new_ctx = self._context_edit.text().strip()
        new_ref = self._ref_edit.text().strip()
        new_n = self._note_edit.toPlainText().strip()
        if not new_s or not new_t:
            return None
        return (new_s, new_t, new_o, _build_note(new_ctx, new_ref, new_n))


class TermTableDialog(QDialog):
    """术语表格对话框 — 显示所有术语，支持右键编辑/删除"""

    def __init__(self, parent: QWidget | None, note_manager: NoteManager):
        super().__init__(parent)
        self._note_manager = note_manager
        self._setup_ui()

    def _populate_table(self):
        """填充表格数据"""
        terms = self._note_manager.get_terms()
        self._table.setRowCount(len(terms))
        for i, t in enumerate(terms):
            ctx = ""
            for ln in t.note.split("\n"):
                if ln.startswith("原文: "):
                    ctx = ln[4:]
                    break
            self._table.setItem(i, 0, QTableWidgetItem(t.source))
            self._table.setItem(i, 1, QTableWidgetItem(t.translation))
            self._table.setItem(i, 2, QTableWidgetItem(t.origin))
            self._table.setItem(i, 3, QTableWidgetItem(ctx))
            self._table.setItem(i, 4, QTableWidgetItem(t.note.replace("\n", " ")))
        self._table.resizeColumnsToContents()

    def _setup_ui(self):
        terms = self._note_manager.get_terms()
        self.setWindowTitle(f"术语 ({len(terms)})")
        self.setMinimumSize(500, 400)
        self.setObjectName("termTableDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(self)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["术语", "译文", "出处", "原文", "备注"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().hide()

        self._populate_table()

        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self._table)

    def _on_context_menu(self, pos: QPoint):
        """右键菜单：编辑/删除术语"""
        row = self._table.rowAt(pos.y())
        terms = self._note_manager.get_terms()
        if row < 0 or row >= len(terms):
            return
        t = terms[row]

        menu = QMenu(self._table)
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        action = menu.exec(self._table.mapToGlobal(pos))

        if action == edit_action:
            self._edit_term(row)
        elif action == delete_action:
            logger.info(f"用户操作: 删除术语 {t.source}")
            self._note_manager.remove_term(t.source)
            self._populate_table()

    def _edit_term(self, row: int):
        """编辑指定行的术语"""
        terms = self._note_manager.get_terms()
        if row >= len(terms):
            return
        t = terms[row]

        dialog = TermEditDialog(self, term=t, note_manager=self._note_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_result()
            if result:
                new_s, new_t, new_o, new_n = result
                logger.info(f"用户操作: 编辑术语 {t.source} → {new_s}")
                self._note_manager.update_term(t.source, new_s, new_t, new_o, new_n)
                self._populate_table()
