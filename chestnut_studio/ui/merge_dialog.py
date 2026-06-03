"""ASS+TXT 字幕合并对话框

用户选择 ASS 文件和 TXT 文件，自动匹配文本到时间轴，
对无法自动分配的重叠冲突提供可视化解决策略。
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.core.ass_merge import (
    MergePlan,
    apply_conflict_resolution,
    build_merge_plan,
)


class MergeDialog(QDialog):
    """字幕合并对话框"""

    ASS_FILTER = "ASS 字幕 (*.ass)"
    TXT_FILTER = "笔记文件 (*.txt)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plan: MergePlan | None = None
        self._conflict_widgets: list = []
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("合并字幕 (ASS + TXT)")
        self.setMinimumSize(700, 550)
        self.resize(750, 600)

        layout = QVBoxLayout(self)

        # ── 文件选择区域 ──
        file_group = QGroupBox("选择文件")
        file_layout = QFormLayout(file_group)

        ass_row = QWidget()
        ass_row_layout = QHBoxLayout(ass_row)
        ass_row_layout.setContentsMargins(0, 0, 0, 0)
        self._ass_path = QLabel("未选择")
        self._ass_path.setStyleSheet("color: #888;")
        self._ass_btn = QPushButton("浏览...")
        self._ass_btn.clicked.connect(self._browse_ass)
        ass_row_layout.addWidget(self._ass_path, 1)
        ass_row_layout.addWidget(self._ass_btn)
        file_layout.addRow("ASS 文件:", ass_row)

        txt_row = QWidget()
        txt_row_layout = QHBoxLayout(txt_row)
        txt_row_layout.setContentsMargins(0, 0, 0, 0)
        self._txt_path = QLabel("未选择")
        self._txt_path.setStyleSheet("color: #888;")
        self._txt_btn = QPushButton("浏览...")
        self._txt_btn.clicked.connect(self._browse_txt)
        txt_row_layout.addWidget(self._txt_path, 1)
        txt_row_layout.addWidget(self._txt_btn)
        file_layout.addRow("TXT 文件:", txt_row)

        out_row = QWidget()
        out_row_layout = QHBoxLayout(out_row)
        out_row_layout.setContentsMargins(0, 0, 0, 0)
        self._out_path = QLabel("自动生成")
        self._out_path.setStyleSheet("color: #888;")
        self._out_btn = QPushButton("浏览...")
        self._out_btn.clicked.connect(self._browse_output)
        out_row_layout.addWidget(self._out_path, 1)
        out_row_layout.addWidget(self._out_btn)
        file_layout.addRow("输出文件:", out_row)

        layout.addWidget(file_group)

        # ── 分析按钮 ──
        self._analyze_btn = QPushButton("分析合并")
        self._analyze_btn.setStyleSheet("QPushButton { padding: 8px 24px; font-weight: bold; }")
        self._analyze_btn.clicked.connect(self._analyze)
        layout.addWidget(self._analyze_btn, alignment=Qt.AlignCenter)

        # ── 合并结果摘要 ──
        self._summary_label = QLabel("")
        self._summary_label.setVisible(False)
        self._summary_label.setStyleSheet("QLabel { background: #f0f8f0; padding: 8px; border-radius: 4px; }")
        layout.addWidget(self._summary_label)

        # ── 冲突解决区域（滚动） ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVisible(False)
        self._scroll = scroll

        self._conflict_container = QWidget()
        self._conflict_layout = QVBoxLayout(self._conflict_container)
        scroll.setWidget(self._conflict_container)
        layout.addWidget(scroll, 1)

        # ── 操作按钮 ──
        btn_layout = QHBoxLayout()
        self._export_btn = QPushButton("导出合并 ASS")
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
        """根据 ASS 路径自动生成输出路径"""
        ass = self._ass_path.text()
        if ass and ass != "未选择":
            name = Path(ass)
            out = str(name.parent / ("merged_" + name.name))
            self._out_path.setText(out)
            self._out_path.setStyleSheet("")

    # ── 分析合并 ──

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

        # 显示摘要
        nc = len(self._plan.conflicts)
        if nc == 0:
            summary = f"✅ {self._plan.auto_matched}/{self._plan.total_notes} 条已自动匹配\n🎉 没有冲突，可直接导出！"
            self._summary_label.setStyleSheet("QLabel { background: #f0f8f0; padding: 8px; border-radius: 4px; }")
        else:
            summary = (
                f"✅ {self._plan.auto_matched}/{self._plan.total_notes} 条已自动匹配\n"
                f"⚠️ {nc} 个冲突待解决——请在下方为每条重叠轴分配文本"
            )
            self._summary_label.setStyleSheet("QLabel { background: #fff8e0; padding: 8px; border-radius: 4px; }")
        self._summary_label.setText(summary)
        self._summary_label.setVisible(True)

        # 显示冲突区域
        self._build_conflict_ui()
        self._scroll.setVisible(nc > 0)
        self._export_btn.setEnabled(True)

    # ── 冲突 UI ──

    def _build_conflict_ui(self):
        """构建冲突解决界面"""
        # 清除旧内容
        while self._conflict_layout.count():
            item = self._conflict_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._conflict_widgets.clear()

        if not self._plan or not self._plan.conflicts:
            return

        # 标题
        title = QLabel(f"<b>以下 {len(self._plan.conflicts)} 处重叠轴需要分配文本</b>")
        title.setStyleSheet("font-size: 13px; margin-top: 8px;")
        self._conflict_layout.addWidget(title)

        for ci, conflict in enumerate(self._plan.conflicts):
            group = QGroupBox(f"冲突 #{ci + 1}: 重叠区 {conflict.a_start} ~ {conflict.b_end}")
            group.setStyleSheet(
                "QGroupBox { font-weight: bold; border: 1px solid #ddd; "
                "border-radius: 4px; margin-top: 8px; padding-top: 16px; }"
                "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
            )

            glayout = QVBoxLayout(group)

            # 时间轴信息
            info = QLabel(
                f"A (先出现): <b>ASS#{conflict.a_idx + 1}</b> "
                f"({conflict.a_start} → {conflict.a_end})<br>"
                f"B (后出现): <b>ASS#{conflict.b_idx + 1}</b> "
                f"({conflict.b_start} → {conflict.b_end})"
            )
            info.setStyleSheet("font-weight: normal;")
            glayout.addWidget(info)

            # 已有独占区文本
            if conflict.a_text_before:
                glayout.addWidget(QLabel(f"  A 独占区已有: {conflict.a_text_before[:60]}"))
            if conflict.b_text_before:
                glayout.addWidget(QLabel(f"  B 独占区已有: {conflict.b_text_before[:60]}"))

            glayout.addWidget(QLabel("  ▼ 分配重叠区的文本:"))

            # 每个选项
            note_options = [f"TXT#{n.index}: {n.text}" for n in conflict.notes]

            row_a = QHBoxLayout()
            row_a.addWidget(QLabel(f"  → A 轴 (ASS#{conflict.a_idx + 1}):"))
            cb_a = QComboBox()
            cb_a.addItems(note_options)
            # 默认：A 拿第一条
            cb_a.setCurrentIndex(0)
            row_a.addWidget(cb_a, 1)
            glayout.addLayout(row_a)

            row_b = QHBoxLayout()
            row_b.addWidget(QLabel(f"  → B 轴 (ASS#{conflict.b_idx + 1}):"))
            cb_b = QComboBox()
            cb_b.addItems(note_options)
            # 默认：B 拿第二条（如果有）
            cb_b.setCurrentIndex(min(1, len(conflict.notes) - 1))
            row_b.addWidget(cb_b, 1)
            glayout.addLayout(row_b)

            self._conflict_layout.addWidget(group)
            self._conflict_widgets.append((cb_a, cb_b))

        self._conflict_layout.addStretch()

    # ── 导出 ──

    def _export(self):
        if not self._plan:
            return

        # 先应用所有冲突决议
        for ci, (cb_a, cb_b) in enumerate(self._conflict_widgets):
            a_idx = cb_a.currentIndex()
            b_idx = cb_b.currentIndex()
            if ci < len(self._plan.conflicts):
                apply_conflict_resolution(self._plan, ci, a_idx, b_idx)

        # 没有冲突（或已解决完）
        if self._plan.conflicts:
            QMessageBox.warning(self, "错误", "仍有未解决的冲突。")
            return

        # 确定输出路径
        out = self._out_path.text()
        if out == "自动生成" or not out:
            self._auto_output()
            out = self._out_path.text()

        try:
            self._plan.write(out)
            QMessageBox.information(
                self,
                "导出成功",
                f"已生成合并字幕:\n{out}\n\n在 Aegisub 中打开即可预览效果。",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"写入文件出错:\n{e}")
