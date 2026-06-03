"""ASS+TXT 字幕合并逻辑

将 Chestnut Studio 导出的 TXT 笔记文本合并到 ASS 字幕时间轴中。
**原则**: 只有 100% 确定的匹配才自动填入——即恰好 1 条 TXT 落在某条 ASS 的独占时间区内。
其他情况（多条 TXT 抢同一 ASS、时间重叠等）均放入报告中，让用户手动处理。

用法:
    from chestnut_studio.core.ass_merge import build_merge_plan

    plan = build_merge_plan("input.ass", "notes.txt")
    print(plan.generate_report())  # 查看不确定项
    plan.write("output.ass")       # 写出 ASS + 报告
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ── 数据结构 ──


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
    uncertain: list[UncertainMatch]  # 不确定的匹配项
    _raw_ass_lines: list[str] = field(repr=False)  # 原始 ASS 行
    track_colors: dict[str, str] = field(default_factory=dict)  # 轨道名→颜色

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

    def generate_report(self, max_success_show: int = 20) -> str:
        """生成合并报告——头信息 + 待处理区 + 成功区

        Args:
            max_success_show: 成功匹配最多显示条数（0 表示全部）
        """
        sep = "=" * 60
        sub = "-" * 60

        lines = [sep]
        lines.append("  ASS+TXT Merge Report")
        lines.append(sep)
        lines.append(f"  Source ASS:       {Path(self.ass_path).name}")
        lines.append(f"  Source TXT:       {Path(self.txt_path).name}")
        lines.append(f"  Total TXT notes:  {self.total_notes}")
        lines.append(f"  Auto-matched:     {self.auto_matched} / {self.total_notes}")
        lines.append(f"  Manual needed:    {len(self.uncertain)}")
        lines.append("")

        # Section 1: Manual items
        lines.append(sub)
        lines.append("  Section 1 -- Manual (%d items)" % len(self.uncertain))
        lines.append(sub)
        lines.append("")

        if not self.uncertain:
            lines.append("  No manual items -- all matches are certain.")
            lines.append("")
        else:
            for i, u in enumerate(self.uncertain, 1):
                lines.append("  %d. ASS #%d  %s --> %s" % (i, u.ass_idx + 1, u.ass_start, u.ass_end))
                lines.append("     Reason: %s" % u.reason)
                for n in u.notes:
                    lines.append("     |  TXT #%d  [%s]  %s" % (n.index, n.track, n.text))
                lines.append("")

            lines.append("  How to fix:")
            lines.append("  1. Open the output ASS in Aegisub")
            lines.append("  2. Navigate to the timecodes listed above")
            lines.append("  3. Copy text from TXT and paste into the matching ASS line")
            lines.append("")

        # Section 2: Auto-matched
        lines.append(sub)
        lines.append("  Section 2 -- Auto-matched (%d items)" % self.auto_matched)
        lines.append(sub)
        lines.append("")

        success_items = [d for d in self.dialogues if d.text]
        show_count = max_success_show if max_success_show > 0 else len(success_items)
        show_count = min(show_count, len(success_items))

        for i, d in enumerate(success_items[:show_count], 1):
            track_tag = "[%s] " % d.track if d.track else ""
            lines.append("  %d. ASS #%d  %s --> %s" % (i, d.line_index + 1, d.start_str, d.end_str))
            lines.append("     |  %s%s" % (track_tag, d.text[:80]))
            lines.append("")

        if show_count < len(success_items):
            lines.append(
                "  ... %d more auto-matched items (total %d)" % (len(success_items) - show_count, len(success_items))
            )
            lines.append("")

        lines.append(sep)
        return "\n".join(lines)

    def write(self, output_path: str):
        """写出合并后的 ASS 文件 + 同目录下的报告"""
        from datetime import datetime

        date_tag = datetime.now().strftime("%y%m%d")
        ass_path = Path(output_path)

        # ASS 文件名: [YYMMDD]M_originname.ass
        ass_name = f"{date_tag}M_{ass_path.name}"
        final_ass = ass_path.parent / ass_name

        lines = self._repr_lines()
        with open(final_ass, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        # 报告文件名: [YYMMDD]R_originname.txt
        report_name = f"{date_tag}R_{ass_path.stem}.txt"
        report_path = ass_path.parent / report_name
        report_path.write_text(self.generate_report(), encoding="utf-8")

        return str(final_ass), str(report_path)

    def get_ass_content(self) -> str:
        """获取合并后的 ASS 文本内容（用于预览）"""
        return "\n".join(self._repr_lines())

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

    def get_ass_content(self) -> str:
        """获取合并后的 ASS 文本内容（用于预览）"""
        return "\n".join(self._repr_lines())


# ── 解析器 ──


def _parse_ass_time(s: str) -> float:
    """h:mm:ss.xx → 秒"""
    parts = s.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def _parse_txt_time(s: str) -> float:
    """mm:ss.xx 或 h:mm:ss.xx → 秒"""
    parts = s.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def parse_ass(filepath: str) -> tuple[list[AssDialogue], list[str]]:
    """解析 ASS 文件，返回 (dialogues, raw_lines)"""
    with open(filepath, encoding="utf-8") as f:
        raw_lines = f.read().split("\n")

    dialogues = []
    for i, line in enumerate(raw_lines):
        if line.startswith("Dialogue:"):
            # 只拆前9个逗号字段，第10个是 Text
            idx = _nth_comma(line, 8)
            if idx < 0:
                continue
            prefix = line[:idx]  # 前9个字段
            parts = prefix.split(",")
            # parts[1]=start, parts[2]=end, parts[3]=style
            d = AssDialogue(
                line_index=i,
                start_s=_parse_ass_time(parts[1].strip()),
                end_s=_parse_ass_time(parts[2].strip()),
                start_str=parts[1].strip(),
                end_str=parts[2].strip(),
                style=parts[3].strip(),
                text="",
                raw_before_text=prefix,
            )
            dialogues.append(d)

    return dialogues, raw_lines


def _nth_comma(s: str, n: int) -> int:
    """找到第 n 个逗号的位置（0-based）"""
    idx = -1
    for _ in range(n + 1):
        idx = s.find(",", idx + 1)
        if idx < 0:
            return -1
    return idx


def _parse_track_colors(raw: str) -> dict[str, str]:
    """从 TXT 头部解析轨道颜色定义

    格式: # 轨道颜色: 轨道1=#3b82f6, 轨道2=#10b981, ...
    """
    colors: dict[str, str] = {}
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("# 轨道颜色:"):
            color_part = line[len("# 轨道颜色:") :].strip()
            for pair in color_part.split(","):
                pair = pair.strip()
                if "=" in pair:
                    name, color = pair.split("=", 1)
                    name = name.strip()
                    color = color.strip()
                    if color.startswith("#") and len(color) == 7:
                        colors[name] = color
            break
    return colors


def parse_txt(filepath: str) -> tuple[list[TxtNote], dict[str, str]]:
    """解析 TXT 笔记文件，返回 (notes, track_colors)"""
    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    track_colors = _parse_track_colors(raw)

    notes = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line or not re.match(r"#\d+\t", line):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue

        # 提取序号
        idx_str = parts[0][1:]  # 去掉 '#'
        try:
            note_idx = int(idx_str)
        except ValueError:
            note_idx = len(notes) + 1

        track = parts[1]
        time_str = parts[2]

        # 内容在 "| " 之后
        content_part = "\t".join(parts[3:])
        if "| " in content_part:
            text = content_part.split("| ", 1)[1]
        else:
            text = content_part

        try:
            t = _parse_txt_time(time_str)
        except (ValueError, IndexError):
            continue

        notes.append(TxtNote(index=note_idx, time_s=t, track=track, text=text))

    return notes, track_colors


# ── 合并引擎 ──


def build_merge_plan(ass_path: str, txt_path: str) -> MergePlan:
    """构建合并计划——仅 100% 确定的才自动匹配

    流程:
    1. 解析 ASS 和 TXT
    2. 检测重叠对，标记每条 ASS 的独占区
    3. 独占区匹配：恰好 1 条 TXT → 自动填入；多条 TXT → 入不确定列表
    4. 所有落在重叠区的 TXT → 入不确定列表（不做自动分配）
    5. 生成报告
    """
    dialogues, raw_lines = parse_ass(ass_path)
    notes, track_colors = parse_txt(txt_path)

    # ── 检测重叠对 ──
    overlap_pairs = []
    for di in range(len(dialogues) - 1):
        a, b = dialogues[di], dialogues[di + 1]
        if a.end_s > b.start_s + 0.05:  # > 50ms 视为有效重叠
            overlap_pairs.append(
                {
                    "a_idx": di,
                    "b_idx": di + 1,
                    "zone_start": b.start_s,
                    "zone_end": min(a.end_s, b.end_s),
                }
            )

    # ── 标记独占区结束点 ──
    for d in dialogues:
        d._exclusive_end = d.end_s  # type: ignore[attr-defined]

    for op in overlap_pairs:
        a = dialogues[op["a_idx"]]
        b = dialogues[op["b_idx"]]
        a._exclusive_end = op["zone_start"]  # type: ignore[attr-defined]
        b._exclusive_end = b.start_s  # type: ignore[attr-defined]

    # ── 初始化临时字段 ──
    for d in dialogues:
        d._exclusive_text = ""  # type: ignore[attr-defined]
        d._exclusive_track = ""  # type: ignore[attr-defined]
        d._exclusive_notes: list[TxtNote] = []  # type: ignore[attr-defined]

    # ── 第一轮：独占区收集 ──
    for note in notes:
        for d in dialogues:
            excl_end = getattr(d, "_exclusive_end", d.end_s)
            if d.start_s <= note.time_s < excl_end:
                d._exclusive_notes.append(note)  # type: ignore[attr-defined]
                break

    # ── 第二轮：确定匹配 / 入不确定列表 ──
    uncertain: list[UncertainMatch] = []
    auto_matched = 0

    for di, d in enumerate(dialogues):
        zone_notes: list[TxtNote] = getattr(d, "_exclusive_notes", [])
        if not zone_notes:
            continue

        if len(zone_notes) == 1:
            # ✅ 100% 确定：独占区内恰好 1 条 TXT
            note = zone_notes[0]
            d._exclusive_text = note.text  # type: ignore[attr-defined]
            d._exclusive_track = note.track  # type: ignore[attr-defined]
            auto_matched += 1
        else:
            # ⚠️ 不确定：独占区内多条 TXT
            uncertain.append(
                UncertainMatch(
                    ass_idx=di,
                    ass_start=d.start_str,
                    ass_end=d.end_str,
                    notes=zone_notes,
                    reason=f"同一条 ASS 时间窗口内有 {len(zone_notes)} 条 TXT 笔记",
                )
            )

    # ── 收集重叠区 TXT（排除已在独占区匹配掉的） ──
    matched_note_indices: set[int] = set()
    for d in dialogues:
        for n in getattr(d, "_exclusive_notes", []):
            matched_note_indices.add(n.index)

    overlap_notes = [n for n in notes if n.index not in matched_note_indices]

    # 将重叠区未匹配的 TXT 按所属重叠对分组
    # 先找每个重叠 TXT 属于哪个重叠对
    for op in overlap_pairs:
        zone_notes = []
        remaining = []
        for note in overlap_notes:
            if op["zone_start"] <= note.time_s <= op["zone_end"]:
                zone_notes.append(note)
            else:
                remaining.append(note)
        overlap_notes = remaining

        if not zone_notes:
            continue

        a = dialogues[op["a_idx"]]
        b = dialogues[op["b_idx"]]

        # 收集哪些 ASS 行可能被这些 TXT 匹配
        involved: list[int] = []
        seen: set[int] = set()
        for note in zone_notes:
            for di, d in enumerate(dialogues):
                if d.start_s <= note.time_s <= d.end_s and di not in seen:
                    seen.add(di)
                    involved.append(di)

        if len(involved) == 1:
            # 虽然涉及重叠区，但 TXT 都在同一条 ASS 的时间窗口内
            uncertain.append(
                UncertainMatch(
                    ass_idx=involved[0],
                    ass_start=dialogues[involved[0]].start_str,
                    ass_end=dialogues[involved[0]].end_str,
                    notes=zone_notes,
                    reason=f"重叠区内 {len(zone_notes)} 条 TXT 落在同一条 ASS 窗口",
                )
            )
        elif len(involved) >= 2:
            # 多条 ASS 竞争
            # 逐个 ASS 报告
            for ai in involved:
                ass_notes = [n for n in zone_notes if dialogues[ai].start_s <= n.time_s <= dialogues[ai].end_s]
                if ass_notes:
                    uncertain.append(
                        UncertainMatch(
                            ass_idx=ai,
                            ass_start=dialogues[ai].start_str,
                            ass_end=dialogues[ai].end_str,
                            notes=ass_notes,
                            reason="时间重叠——多条 ASS 竞争该时间段",
                        )
                    )

    # ── 将 _exclusive_text / _exclusive_track 写入 dialogues ──
    for d in dialogues:
        d.text = getattr(d, "_exclusive_text", "")
        d.track = getattr(d, "_exclusive_track", "")
        for attr in ("_exclusive_end", "_exclusive_text", "_exclusive_track", "_exclusive_notes"):
            if hasattr(d, attr):
                delattr(d, attr)

    return MergePlan(
        ass_path=ass_path,
        txt_path=txt_path,
        dialogues=dialogues,
        notes=notes,
        total_notes=len(notes),
        auto_matched=auto_matched,
        uncertain=uncertain,
        track_colors=track_colors,
        _raw_ass_lines=raw_lines,
    )
