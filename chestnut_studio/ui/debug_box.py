"""开发者百宝箱 — 测试各种极端条件

隐藏在「帮助 → 百宝箱」菜单中，用于验证日志系统、
崩溃兜底和性能边界。
"""

from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.utils import get_logger

logger = get_logger("DEBUG")


class DebugBox(QDialog):
    """百宝箱对话框"""

    def __init__(self, parent: QWidget | None = None, note_manager=None):
        super().__init__(parent)
        self._note_manager = note_manager
        self.setWindowTitle("百宝箱")
        self.setMinimumSize(480, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # ── 崩溃测试 ──
        crash_group = QGroupBox("崩溃测试")
        crash_layout = QVBoxLayout(crash_group)
        crash_layout.addWidget(QLabel("触发不同类型崩溃，验证 crash hook 是否正常落日志并弹窗："))
        row = QHBoxLayout()
        for label, fn in [
            ("1 ÷ 0", self._crash_divide),
            ("assert False", self._crash_assert),
            ("IndexError", self._crash_index),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(fn)
            row.addWidget(btn)
        crash_layout.addLayout(row)
        layout.addWidget(crash_group)

        # ── 日志测试 ──
        log_group = QGroupBox("日志测试")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(QLabel("写入测试日志到 app.log，验证文件输出和级别过滤："))
        row = QHBoxLayout()
        for label, lvl in [
            ("DEBUG", "debug"),
            ("INFO", "info"),
            ("WARNING", "warning"),
            ("ERROR", "error"),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked=False, level=lvl: getattr(logger, level)(f"测试 {level.upper()} 日志"))
            row.addWidget(btn)
        log_layout.addLayout(row)
        layout.addWidget(log_group)

        # ── 性能测试 ──
        if self._note_manager is not None:
            perf_group = QGroupBox("性能测试")
            perf_layout = QVBoxLayout(perf_group)
            perf_layout.addWidget(QLabel("批量添加笔记，测试列表渲染和数据量边界："))
            row = QHBoxLayout()
            for label, n in [("+100 条", 100), ("+500 条", 500), ("+1000 条", 1000)]:
                btn = QPushButton(label)
                btn.clicked.connect(lambda checked=False, count=n: self._add_bulk_notes(count))
                row.addWidget(btn)
            perf_layout.addLayout(row)
            layout.addWidget(perf_group)

        # ── 关闭按钮 ──
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    # ── 崩溃测试 ──

    def _crash_divide(self):
        logger.info("崩溃测试: 1 ÷ 0")
        1 / 0  # ZeroDivisionError

    def _crash_assert(self):
        logger.info("崩溃测试: assert False")
        assert False, "手动触发的 AssertionError"

    def _crash_index(self):
        logger.info("崩溃测试: IndexError")
        _ = [][0]

    # ── 性能测试 ──

    def _add_bulk_notes(self, count: int):
        for i in range(count):
            self._note_manager.add(
                timestamp_ms=i * 100,
                text=f"性能测试笔记 #{i + 1} — 这是一条用于压力测试的示例文本",
                note_type="轨道1",
            )
        logger.info(f"性能测试: 批量添加 {count} 条笔记")
        # 通知父窗口刷新列表
        parent = self.parent()
        if hasattr(parent, "note_panel"):
            parent.note_panel.refresh()
