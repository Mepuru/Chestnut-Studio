"""ASS+TXT 字幕合并对话框

选择 ASS 和 TXT 文件，仅自动匹配 100% 确定的条目，
其余生成报告供用户手动处理。
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.ass_merge import build_merge_plan


class MergeDialog(QDialog):
    """字幕合并对话框"""

    ASS_FILTER = "ASS 字幕 (*.ass)"
    TXT_FILTER = "笔记文件 (*.txt)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plan = None
        self._setup_ui()

    def _make_file_row(self, label: str, path_ref, btn_callback):
        """创建文件选择行"""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(80)
        layout.addWidget(lbl)

        path_ref.setStyleSheet("color: #888; padding: 4px 8px; background: #f5f5f5; border-radius: 3px;")
        path_ref.setMinimumHeight(28)
        layout.addWidget(path_ref, 1)

        btn = QPushButton("Browse...")
        btn.setFixedWidth(80)
        btn.clicked.connect(btn_callback)
        layout.addWidget(btn)

        return row

    def _setup_ui(self):
        self.setWindowTitle("Merge ASS + TXT")
        self.setMinimumSize(680, 480)
        self.resize(720, 520)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── File selection ──
        self._ass_path = QLabel("(not selected)")
        self._txt_path = QLabel("(not selected)")
        self._out_path = QLabel("(auto)")

        layout.addWidget(self._make_file_row("ASS File:", self._ass_path, self._browse_ass))
        layout.addWidget(self._make_file_row("TXT File:", self._txt_path, self._browse_txt))
        layout.addWidget(self._make_file_row("Output:", self._out_path, self._browse_output))

        # ── Analyze button ──
        self._analyze_btn = QPushButton("Analyze")
        self._analyze_btn.setStyleSheet("QPushButton { padding: 6px 20px; font-weight: bold; }")
        self._analyze_btn.clicked.connect(self._analyze)
        layout.addWidget(self._analyze_btn, alignment=Qt.AlignCenter)

        # ── Stats summary ──
        self._stats_label = QLabel("")
        self._stats_label.setVisible(False)
        self._stats_label.setStyleSheet("QLabel { padding: 6px 10px; background: #f0f0f0; border-radius: 3px; }")
        layout.addWidget(self._stats_label)

        # ── Report preview ──
        self._report_view = QTextEdit()
        self._report_view.setReadOnly(True)
        self._report_view.setVisible(False)
        self._report_view.setStyleSheet(
            "QTextEdit { font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; background: #fafafa; }"
        )
        layout.addWidget(self._report_view, 1)

        # ── Action buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._export_btn = QPushButton("Export ASS + Report")
        self._export_btn.setEnabled(False)
        self._export_btn.setStyleSheet("QPushButton { padding: 6px 20px; font-weight: bold; }")
        self._export_btn.clicked.connect(self._export)
        btn_layout.addWidget(self._export_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ── File browsing ──

    def _browse_ass(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ASS file", "", self.ASS_FILTER)
        if path:
            self._ass_path.setText(path)
            self._ass_path.setStyleSheet("padding: 4px 8px; background: #f5f5f5; border-radius: 3px;")
            self._auto_output()

    def _browse_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select TXT file", "", self.TXT_FILTER)
        if path:
            self._txt_path.setText(path)
            self._txt_path.setStyleSheet("padding: 4px 8px; background: #f5f5f5; border-radius: 3px;")
            self._auto_output()

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save merged ASS", "", self.ASS_FILTER)
        if path:
            self._out_path.setText(path)
            self._out_path.setStyleSheet("padding: 4px 8px; background: #f5f5f5; border-radius: 3px;")

    def _auto_output(self):
        ass = self._ass_path.text()
        if ass and "(not selected)" not in ass:
            name = Path(ass)
            self._out_path.setText(str(name.parent / name.name))
            self._out_path.setStyleSheet("padding: 4px 8px; background: #f5f5f5; border-radius: 3px;")

    # ── Analysis ──

    def _analyze(self):
        ass = self._ass_path.text()
        txt = self._txt_path.text()

        if "(not selected)" in ass or "(not selected)" in txt:
            QMessageBox.warning(self, "Notice", "Please select both ASS and TXT files first.")
            return
        if not Path(ass).exists():
            QMessageBox.warning(self, "Error", "ASS file not found:\n" + ass)
            return
        if not Path(txt).exists():
            QMessageBox.warning(self, "Error", "TXT file not found:\n" + txt)
            return

        try:
            self._plan = build_merge_plan(ass, txt)
        except Exception as e:
            QMessageBox.critical(self, "Analysis failed", "Merge error:\n" + str(e))
            return

        # Stats summary
        total = self._plan.total_notes
        auto = self._plan.auto_matched
        manual = len(self._plan.uncertain)

        if manual == 0:
            stats = "[Auto-matched: %d / %d]  All matches are certain." % (auto, total)
        else:
            stats = "[Auto-matched: %d / %d]  [Manual: %d items]" % (auto, total, manual)

        self._stats_label.setText(stats)
        self._stats_label.setVisible(True)

        # Report
        self._report_view.setText(self._plan.generate_report())
        self._report_view.setVisible(True)
        self._export_btn.setEnabled(True)
        self._analyze_btn.setText("Re-analyze")

    # ── Export ──

    def _export(self):
        if not self._plan:
            return

        out = self._out_path.text()
        if "(auto)" in out or not out:
            self._auto_output()
            out = self._out_path.text()

        try:
            ass_path, report_path = self._plan.write(out)
            QMessageBox.information(
                self,
                "Export successful",
                "ASS:  %s\nReport:  %s\n\nAuto-matched: %d / %d\nManual: %d items"
                % (
                    ass_path,
                    report_path,
                    self._plan.auto_matched,
                    self._plan.total_notes,
                    len(self._plan.uncertain),
                ),
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Export failed", "Write error:\n" + str(e))
