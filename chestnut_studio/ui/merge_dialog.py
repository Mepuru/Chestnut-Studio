"""ASS+TXT 字幕合并对话框

选择 ASS 和 TXT 文件，仅自动匹配 100% 确定的条目，
其余生成报告供用户手动处理。
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
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

    def _setup_ui(self):
        self.setWindowTitle("合并字幕 (ASS + TXT)")
        self.setMinimumSize(700, 500)
        self.resize(750, 550)

        layout = QVBoxLayout(self)

        # ── 文件选择 ──
        file_group = QGroupBox("选择文件")
        file_layout = QFormLayout(file_group)

        ass_row = QWidget()
        ass_layout = QHBoxLayout(ass_row)
        ass_layout.setContentsMargins(0, 0, 0, 0)
        self._ass_path = QLabel("未选择")
        self._ass_path.setStyleSheet("color: #888;")
        ass_btn = QPushButton("浏览...")
        ass_btn.clicked.connect(self._browse_ass)
        ass_layout.addWidget(self._ass_path, 1)
        ass_layout.addWidget(ass_btn)
        file_layout.addRow("ASS 文件:", ass_row)

        txt_row = QWidget()
        txt_layout = QHBoxLayout(txt_row)
        txt_layout.setContentsMargins(0, 0, 0, 0)
        self._txt_path = QLabel("未选择")
        self._txt_path.setStyleSheet("color: #888;")
        txt_btn = QPushButton("浏览...")
        txt_btn.clicked.connect(self._browse_txt)
        txt_layout.addWidget(self._txt_path, 1)
        txt_layout.addWidget(txt_btn)
        file_layout.addRow("TXT 文件:", txt_row)

        out_row = QWidget()
        out_layout = QHBoxLayout(out_row)
        out_layout.setContentsMargins(0, 0, 0, 0)
        self._out_path = QLabel("自动生成")
        self._out_path.setStyleSheet("color: #888;")
        out_btn = QPushButton("浏览...")
        out_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(self._out_path, 1)
        out_layout.addWidget(out_btn)
        file_layout.addRow("输出文件:", out_row)

        layout.addWidget(file_group)

        # ── 分析按钮 ──
        self._analyze_btn = QPushButton("分析合并")
        self._analyze_btn.setStyleSheet("QPushButton { padding: 8px 24px; font-weight: bold; }")
        self._analyze_btn.clicked.connect(self._analyze)
        layout.addWidget(self._analyze_btn, alignment=Qt.AlignCenter)

        # ── 结果预览 ──
        self._report_view = QTextEdit()
        self._report_view.setReadOnly(True)
        self._report_view.setVisible(False)
        self._report_view.setStyleSheet("QTextEdit { font-family: monospace; font-size: 12px; }")
        layout.addWidget(self._report_view, 1)

        # ── 操作按钮 ──
        btn_layout = QHBoxLayout()
        self._export_btn = QPushButton("导出合并 ASS + 报告")
        self._export_btn.setEnabled(False)
        self._export_btn.setStyleSheet("QPushButton { padding: 8px 24px; font-weight: bold; }")
        self._export_btn.clicked.connect(self._export)
        btn_layout.addStretch()
        btn_layout.addWidget(self._export_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    # ── 文件选择 ──

    def _browse_ass(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 ASS 文件", "", self.ASS_FILTER)
        if path:
            self._ass_path.setText(path)
            self._ass_path.setStyleSheet("")
            self._auto_output()

    def _browse_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 TXT 文件", "", self.TXT_FILTER)
        if path:
            self._txt_path.setText(path)
            self._txt_path.setStyleSheet("")
            self._auto_output()

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存合并后的 ASS", "", self.ASS_FILTER)
        if path:
            self._out_path.setText(path)
            self._out_path.setStyleSheet("")

    def _auto_output(self):
        ass = self._ass_path.text()
        if ass and ass != "未选择":
            name = Path(ass)
            self._out_path.setText(str(name.parent / name.name))
            self._out_path.setStyleSheet("")

    # ── 分析 ──

    def _analyze(self):
        ass = self._ass_path.text()
        txt = self._txt_path.text()

        if ass == "未选择" or txt == "未选择":
            QMessageBox.warning(self, "提示", "请先选择 ASS 和 TXT 文件。")
            return
        if not Path(ass).exists():
            QMessageBox.warning(self, "错误", f"ASS 文件不存在:\n{ass}")
            return
        if not Path(txt).exists():
            QMessageBox.warning(self, "错误", f"TXT 文件不存在:\n{txt}")
            return

        try:
            self._plan = build_merge_plan(ass, txt)
        except Exception as e:
            QMessageBox.critical(self, "分析失败", f"合并分析出错:\n{e}")
            return

        self._report_view.setText(self._plan.generate_report())
        self._report_view.setVisible(True)
        self._export_btn.setEnabled(True)
        self._analyze_btn.setText("重新分析")

    # ── 导出 ──

    def _export(self):
        if not self._plan:
            return

        out = self._out_path.text()
        if out == "自动生成" or not out:
            self._auto_output()
            out = self._out_path.text()

        try:
            ass_path, report_path = self._plan.write(out)
            QMessageBox.information(
                self,
                "导出成功",
                f"已生成合并字幕:\n{ass_path}\n\n"
                f"合并报告:\n{report_path}\n\n"
                f"自动匹配: {self._plan.auto_matched}/{self._plan.total_notes}\n"
                f"待处理: {len(self._plan.uncertain)} 项（详见报告）",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"写入文件出错:\n{e}")
