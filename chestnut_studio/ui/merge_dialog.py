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
from chestnut_studio.utils import get_logger

logger = get_logger("UI")


class MergeDialog(QDialog):
    """字幕合并对话框"""

    ASS_FILTER = "ASS 字幕 (*.ass)"
    TXT_FILTER = "笔记文件 (*.txt)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plan = None
        self._setup_ui()

    def _make_file_row(self, label: str, path_ref, btn_callback):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setObjectName("fileLabel")
        lbl.setFixedWidth(70)
        layout.addWidget(lbl)

        path_ref.setObjectName("pathLabel")
        path_ref.setText("（未选择）")
        layout.addWidget(path_ref, 1)

        btn = QPushButton("选择...")
        btn.setObjectName("browseBtn")
        btn.clicked.connect(btn_callback)
        layout.addWidget(btn)

        return row

    def _setup_ui(self):
        self.setWindowTitle("合并字幕")
        self.setMinimumSize(680, 480)
        self.resize(720, 520)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── 文件选择 ──
        self._ass_path = QLabel("（未选择）")
        self._txt_path = QLabel("（未选择）")
        self._out_path = QLabel("（自动）")

        layout.addWidget(self._make_file_row("ASS", self._ass_path, self._browse_ass))
        layout.addWidget(self._make_file_row("TXT", self._txt_path, self._browse_txt))
        layout.addWidget(self._make_file_row("输出", self._out_path, self._browse_output))

        # ── 分析按钮 ──
        self._analyze_btn = QPushButton("分析合并")
        self._analyze_btn.setObjectName("primaryBtn")
        self._analyze_btn.clicked.connect(self._analyze)
        layout.addWidget(self._analyze_btn, alignment=Qt.AlignCenter)

        # ── 统计摘要 ──
        self._stats_label = QLabel("")
        self._stats_label.setObjectName("statsLabel")
        self._stats_label.setVisible(False)
        layout.addWidget(self._stats_label)

        # ── 报告预览 ──
        self._report_view = QTextEdit()
        self._report_view.setObjectName("reportView")
        self._report_view.setReadOnly(True)
        self._report_view.setVisible(False)
        layout.addWidget(self._report_view, 1)

        # ── 操作按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._export_btn = QPushButton("导出")
        self._export_btn.setObjectName("primaryBtn")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._export)
        btn_layout.addWidget(self._export_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("browseBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ── 文件选择 ──

    def _browse_ass(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 ASS 文件", "", self.ASS_FILTER)
        if path:
            self._ass_path.setText(path)
            self._auto_output()

    def _browse_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 TXT 文件", "", self.TXT_FILTER)
        if path:
            self._txt_path.setText(path)
            self._auto_output()

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存合并后的 ASS", "", self.ASS_FILTER)
        if path:
            self._out_path.setText(path)

    def _auto_output(self):
        ass = self._ass_path.text()
        if ass and ass != "（未选择）":
            from datetime import datetime

            date_tag = datetime.now().strftime("%y%m%d")
            name = Path(ass)
            out_name = f"{date_tag}M_{name.name}"
            self._out_path.setText(str(name.parent / out_name))

    # ── 分析 ──

    def _analyze(self):
        ass = self._ass_path.text()
        txt = self._txt_path.text()

        if "（未选择）" in ass or "（未选择）" in txt:
            QMessageBox.warning(self, "提示", "请先选择 ASS 和 TXT 文件。")
            return
        if not Path(ass).exists():
            QMessageBox.warning(self, "错误", "ASS 文件不存在:\n" + ass)
            return
        if not Path(txt).exists():
            QMessageBox.warning(self, "错误", "TXT 文件不存在:\n" + txt)
            return

        try:
            self._plan = build_merge_plan(ass, txt)
            logger.info(f"合并分析: ASS={ass}, TXT={txt}")
        except Exception as e:
            logger.error(f"合并分析失败: {e}")
            QMessageBox.critical(self, "分析失败", "合并分析出错:\n" + str(e))
            return

        total = self._plan.total_notes
        auto = self._plan.auto_matched
        manual = len(self._plan.uncertain)

        if manual == 0:
            self._stats_label.setText(f"已匹配 {auto} / {total} — 全部确定")
        else:
            self._stats_label.setText(f"已匹配 {auto} / {total} — 待处理 {manual} 项")
        self._stats_label.setVisible(True)

        self._report_view.setText(self._plan.generate_report())
        self._report_view.setVisible(True)
        self._export_btn.setEnabled(True)
        self._analyze_btn.setText("重新分析")

    # ── 导出 ──

    def _export(self):
        if not self._plan:
            return

        out = self._out_path.text()
        if "（自动）" in out or not out:
            self._auto_output()
            out = self._out_path.text()

        try:
            ass_path, report_path = self._plan.write(out)
            logger.info(f"合并导出: {ass_path}, {report_path}")
            QMessageBox.information(
                self,
                "导出成功",
                f"字幕: {ass_path}\n报告: {report_path}\n\n"
                f"已匹配 {self._plan.auto_matched} / {self._plan.total_notes}，"
                f"待处理 {len(self._plan.uncertain)} 项",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "导出失败", "写入文件出错:\n" + str(e))
