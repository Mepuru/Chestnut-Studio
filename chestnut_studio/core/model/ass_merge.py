"""ASS+TXT 字幕合并数据模型

纯数据类定义 + MergePlan 的 I/O 方法（过渡期）。
数据类无 PySide6 依赖。MergePlan 的 write()/generate_report()
后续会拆分到 core/io/ 中，此处为过渡阶段暂留。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from chestnut_studio.utils.version import get_version


@dataclass
class AssDialogue:
    """ASS 文件中的一条 Dialogue"""

    line_index: int  # 在原始文件中的行号
    start_s: float  # 开始时间（秒）
    end_s: float  # 结束时间（秒）
    start_str: str  # 原始时间字符串 h:mm:ss.xx
    end_str: str  # 原始时间字符串 h:mm:ss.xx
    style: str  # 样式名
    text: str  # 文本内容（初始为空）
    raw_before_text: str  # "Dialogue: ..." 最后一个逗号之前的部分
    track: str = ""  # 轨道名（从 TXT 继承）
    src_note_idx: int = 0  # 源 TXT 序号（0=无来源）
    # ── 以下为 build_merge_plan 内部临时字段 ──
    _exclusive_end: float = 0.0
    _exclusive_notes: list = field(default_factory=list)
    _exclusive_text: str = ""
    _exclusive_track: str = ""
    _exclusive_note_idx: int = 0


@dataclass
class TxtNote:
    """TXT 笔记中的一条"""

    index: int  # 在 TXT 中的序号（从1开始）
    time_s: float  # 时间点（秒）
    track: str  # 轨道名
    text: str  # 文本内容


@dataclass
class UncertainMatch:
    """不能 100% 确定的匹配项——需要手动处理"""

    ass_idx: int  # ASS 行索引
    ass_start: str  # ASS 开始时间
    ass_end: str  # ASS 结束时间
    notes: list[TxtNote]  # 候选 TXT 笔记
    reason: str  # 原因


@dataclass
class MergePlan:
    """完整的合并计划"""

    ass_path: str
    txt_path: str
    dialogues: list[AssDialogue]
    notes: list[TxtNote]
    total_notes: int  # TXT 总条数
    auto_matched: int  # 100% 确定自动匹配的条数
    uncertain: list[UncertainMatch]  # 不确定的匹配项（需手动）
    risky: list[UncertainMatch]  # 潜在风险项（重叠区就近分配）
    _raw_ass_lines: list[str] = field(repr=False)  # 原始 ASS 行
    track_colors: dict[str, str] = field(default_factory=dict)  # 轨道名→颜色

    # ── 以下方法为过渡期暂留，后续将拆分到 core.io ──

    @staticmethod
    def _hex_to_ass_color(hex_str: str) -> str:
        """#RRGGBB → &H00BBGGRR"""
        h = hex_str.lstrip("#")
        if len(h) != 6:
            return "&H00FFFFFF"
        r, g, b = h[0:2], h[2:4], h[4:6]
        return f"&H00{b}{g}{r}"

    @staticmethod
    def _build_style_line(name: str, color_hex: str) -> str:
        """生成 ASS Style 行"""
        primary = MergePlan._hex_to_ass_color(color_hex)
        return (
            f"Style: {name},思源黑体 CN,70,{primary},&H000000FF,"
            f"&H00000000,&HFF000000,-1,0,0,0,100,100,0,0,1,5,5,2,10,10,10,1"
        )

    def generate_report(self) -> str:
        """生成合并报告——三节：待处理 / 潜在风险 / 自动匹配

        格式与 Chestnut Studio 导出的 TXT 一致：`#` 注释头、等宽排版。
        """
        total_ass = len(self.dialogues)
        filled = sum(1 for d in self.dialogues if d.text)
        empty = total_ass - filled
        pct = 100.0 * self.auto_matched / self.total_notes if self.total_notes else 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        color_summary = (
            ", ".join(f"{k}={v}" for k, v in sorted(self.track_colors.items())) if self.track_colors else "（无）"
        )

        lines = []
        lines.append("# Chestnut Studio - ASS/TXT 合并报告 v" + get_version())
        lines.append("# 导出时间: " + now)
        lines.append("# ---")
        lines.append("# 源 ASS: " + Path(self.ass_path).name)
        lines.append("# 源 TXT: " + Path(self.txt_path).name)
        lines.append("#")
        lines.append(f"# ASS 行数: {total_ass} / TXT 笔记数: {self.total_notes}")
        lines.append(f"# 自动匹配: {self.auto_matched} / {self.total_notes}（{pct:.1f}%）")
        lines.append(f"# 潜在风险: {len(self.risky)} 项 / 待处理: {len(self.uncertain)} 项 / 空行: {empty}")
        lines.append("# 轨道颜色: " + color_summary)
        lines.append("# ---")

        # Section 1
        lines.append("")
        lines.append(f"# 第 1 节 — 待手动处理（{len(self.uncertain)} 项）")
        lines.append("")

        if not self.uncertain:
            lines.append("# 无待处理项。")
            lines.append("")
        else:
            for i, u in enumerate(self.uncertain, 1):
                lines.append(f"{i}. ASS #{u.ass_idx + 1}  {u.ass_start} → {u.ass_end}")
                lines.append(f"   原因: {u.reason}")
                for n in u.notes:
                    lines.append(f"   · TXT #{n.index}  [{n.track}]  {n.text}")
                lines.append("")

        # Section 2
        lines.append("# ---")
        lines.append("")
        lines.append(f"# 第 2 节 — 潜在风险（{len(self.risky)} 项）")
        lines.append("# 说明：以下条目在重叠时间段内自动分配，建议在 Aegisub 中复核。")
        lines.append("")

        if not self.risky:
            lines.append("# 无潜在风险项。")
            lines.append("")
        else:
            for i, r in enumerate(self.risky, 1):
                sourceline = ""
                if r.notes:
                    n = r.notes[0]
                    sourceline = f"  | 源 TXT #{n.index}  [{n.track}]  {n.text}"
                lines.append(f"{i}. ASS #{r.ass_idx + 1}  {r.ass_start} → {r.ass_end}")
                lines.append(f"   原因: {r.reason}")
                if sourceline:
                    lines.append(sourceline)
                lines.append("")

        # Section 3
        lines.append("# ---")
        lines.append("")

        safe_indices = set(r.ass_idx for r in self.risky)
        safe_items = [d for i, d in enumerate(self.dialogues) if d.text and i not in safe_indices]
        lines.append("# ---")
        lines.append("")
        lines.append(f"# 第 3 节 — 已自动匹配（{len(safe_items)} 条）")
        lines.append("")

        for i, d in enumerate(safe_items, 1):
            src_info = ""
            if d.src_note_idx:
                src_info = f"   | 源 TXT #{d.src_note_idx}  [{d.track}]"
            lines.append(f"{i}. ASS #{d.line_index + 1}  {d.start_str} → {d.end_str}")
            if src_info:
                lines.append(src_info)
            tag = f"[{d.track}] " if d.track else ""
            lines.append(f"   · {tag}{d.text[:80]}")
            lines.append("")

        return "\n".join(lines)

    def write(self, output_path: str) -> tuple[str, str]:
        """写出合并后的 ASS 文件 + 同目录下的报告"""
        ass_path = Path(output_path)

        lines = self._repr_lines()
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        # 报告文件名: 将 ASS 文件名中的 M_ 替换为 R_，后缀改为 .txt
        report_name = ass_path.stem.replace("M_", "R_") + ".txt"
        report_path = ass_path.with_name(report_name)
        report_path.write_text(self.generate_report(), encoding="utf-8")

        return str(ass_path), str(report_path)

    def _collect_used_tracks(self) -> list[str]:
        """收集用到的轨道名（去重，保持出现顺序）"""
        used: list[str] = []
        seen: set[str] = set()
        for d in self.dialogues:
            t = d.track
            if t and t not in seen:
                seen.add(t)
                used.append(t)
        return used

    def _repr_lines(self) -> list[str]:
        """按 ASS 节段重组输出行

        结构:
        [Script Info] / [Aegisub ...] 等头部 → 保留
        [V4+ Styles]                     → 只保留 Format + 轨道样式
        [Events]                         → 保留 Format + 替换 Dialogue
        """
        raw = self._raw_ass_lines

        # 找到各节的起止
        sections: list[tuple[int, str]] = []  # (行号, 节名)
        for i, line in enumerate(raw):
            s = line.strip()
            if s.startswith("[") and s.endswith("]"):
                sections.append((i, s))

        # 提取 [V4+ Styles] 和 [Events] 的位置
        styles_sec = next((s for s in sections if s[1] == "[V4+ Styles]"), None)
        events_sec = next((s for s in sections if s[1] == "[Events]"), None)

        if not styles_sec or not events_sec:
            # 缺节则 fallback: 只替换 dialogue 行
            new_lines = list(raw)
            for d in self.dialogues:
                prefix = d.raw_before_text
                if d.track:
                    parts = prefix.split(",", 8)
                    if len(parts) > 3:
                        parts[3] = d.track
                        prefix = ",".join(parts)
                new_lines[d.line_index] = prefix + "," + d.text
            return new_lines

        # 1. 头部：保留到 styles 节之前的所有内容
        result = list(raw[: styles_sec[0] + 1])

        # 2. 样式表：替换所有 Style 行
        fmt = (
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            "MarginL, MarginR, MarginV, Encoding"
        )
        result.append(fmt)
        for t in self._collect_used_tracks():
            color = self.track_colors.get(t, "#FFFFFF")
            result.append(self._build_style_line(t, color))

        # 3. Events 节
        result.append("[Events]")
        for i in range(events_sec[0] + 1, len(raw)):
            line = raw[i]
            if line.startswith("Dialogue:"):
                # 找到对应 dialogue 并替换
                di = next((d for d in self.dialogues if d.line_index == i), None)
                if di:
                    prefix = di.raw_before_text
                    if di.track:
                        parts = prefix.split(",", 8)
                        if len(parts) > 3:
                            parts[3] = di.track
                            prefix = ",".join(parts)
                    result.append(prefix + "," + di.text)
                else:
                    result.append(line)
            else:
                result.append(line)

        return result
