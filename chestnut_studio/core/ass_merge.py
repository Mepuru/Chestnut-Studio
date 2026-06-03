"""ASS+TXT 字幕合并逻辑

将 Chestnut Studio 导出的 TXT 笔记文本合并到 ASS 字幕时间轴中。
支持冲突检测——在重叠区域内无法自动分配时，让用户手动决定。

用法:
    from chestnut_studio.core.ass_merge import build_merge_plan, apply_plan

    plan = build_merge_plan("input.ass", "notes.txt")
    for c in plan.conflicts:
        print(c)  # 让用户选择
    plan.apply_user_choice(conflict_idx, {a_idx: note_idx, b_idx: note_idx})
    plan.write("output.ass")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

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
class MergeConflict:
    """需要用户决策的冲突——重叠区内多条 TXT 需要分摊"""

    a_idx: int  # ASS 中的索引（较早出现的轴）
    b_idx: int  # ASS 中的索引（较晚出现的轴）
    a_start: str  # A 开始时间
    a_end: str  # A 结束时间
    b_start: str  # B 开始时间
    b_end: str  # B 结束时间
    notes: list[TxtNote]  # 落在重叠区的 TXT 笔记
    a_text_before: str = ""  # A 独占区已有的文本
    b_text_before: str = ""  # B 独占区已有的文本


@dataclass
class MergePlan:
    """完整的合并计划"""

    ass_path: str
    txt_path: str
    dialogues: list[AssDialogue]
    notes: list[TxtNote]
    total_notes: int  # TXT 总条数
    auto_matched: int  # 独占区自动匹配的条数
    conflicts: list[MergeConflict]  # 待解决的冲突
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

    def write(self, output_path: str):
        """写出合并后的 ASS 文件"""
        lines = self._repr_lines()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

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
    """构建合并计划——自动匹配 + 检测冲突

    流程:
    1. 解析 ASS 和 TXT
    2. 检测重叠对
    3. 独占区匹配（TXT 落在某条 ASS 独享的时间区间内）
    4. 检测冲突（重叠区内有 >= 2 条 TXT）
    5. 单条重叠区自动按 A→B 分配
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
        b._exclusive_end = b.start_s  # type: ignore[attr-defined]  # B的空独占区

    # ── 第一轮：独占区匹配 ──
    unmatched_notes = []
    auto_matched = 0

    # 为每个 ASS 记录独占区匹配到的文本和轨道
    for d in dialogues:
        d._exclusive_text = ""  # type: ignore[attr-defined]
        d._exclusive_track = ""  # type: ignore[attr-defined]

    for note in notes:
        assigned = False
        for di, d in enumerate(dialogues):
            excl_end = getattr(d, "_exclusive_end", d.end_s)
            if d.start_s <= note.time_s < excl_end:
                if getattr(d, "_exclusive_text", ""):
                    d._exclusive_text += chr(92) + "N" + note.text  # type: ignore[attr-defined]
                else:
                    d._exclusive_text = note.text  # type: ignore[attr-defined]
                    d._exclusive_track = note.track  # type: ignore[attr-defined]  # 取首条轨道
                auto_matched += 1
                assigned = True
                break
        if not assigned:
            unmatched_notes.append(note)

    # ── 第二轮：检测冲突 + 处理重叠区 ──
    conflicts: list[MergeConflict] = []

    # 对每个重叠对，收集落在其重叠区的未匹配 TXT
    for op in overlap_pairs:
        a = dialogues[op["a_idx"]]
        b = dialogues[op["b_idx"]]

        zone_notes = []
        remaining = []
        for note in unmatched_notes:
            if op["zone_start"] <= note.time_s <= op["zone_end"]:
                zone_notes.append(note)
            else:
                remaining.append(note)
        unmatched_notes = remaining

        if not zone_notes:
            continue

        if len(zone_notes) >= 2:
            # ⚠️ 冲突——多条 TXT 需要用户决定
            a_excl = getattr(a, "_exclusive_text", "")
            b_excl = getattr(b, "_exclusive_text", "")
            conflicts.append(
                MergeConflict(
                    a_idx=op["a_idx"],
                    b_idx=op["b_idx"],
                    a_start=a.start_str,
                    a_end=a.end_str,
                    b_start=b.start_str,
                    b_end=b.end_str,
                    notes=zone_notes,
                    a_text_before=a_excl,
                    b_text_before=b_excl,
                )
            )
        else:
            # 单条 TXT：A 先拿（如果A独占区没拿到），否则给B
            note = zone_notes[0]
            a_excl = getattr(a, "_exclusive_text", "")
            b_excl = getattr(b, "_exclusive_text", "")
            if not a_excl:
                a._exclusive_text = note.text  # type: ignore[attr-defined]
                a._exclusive_track = note.track  # type: ignore[attr-defined]
            else:
                b._exclusive_text = note.text  # type: ignore[attr-defined]
                b._exclusive_track = note.track  # type: ignore[attr-defined]
            auto_matched += 1

    # ── 第三轮：剩余未匹配的（基本不会发生，但以防万一） ──
    for note in unmatched_notes:
        best_di = 0
        best_dist = float("inf")
        for di, d in enumerate(dialogues):
            dist = min(abs(note.time_s - d.start_s), abs(note.time_s - d.end_s))
            if dist < best_dist:
                best_dist = dist
                best_di = di
        d = dialogues[best_di]
        excl_text = getattr(d, "_exclusive_text", "")
        if excl_text:
            d._exclusive_text = excl_text + chr(92) + "N" + note.text  # type: ignore[attr-defined]
        else:
            d._exclusive_text = note.text  # type: ignore[attr-defined]
            d._exclusive_track = note.track  # type: ignore[attr-defined]

    # ── 将 _exclusive_text / _exclusive_track 写入 dialogues ──
    for d in dialogues:
        d.text = getattr(d, "_exclusive_text", "")
        d.track = getattr(d, "_exclusive_track", "")
        # 清理临时属性
        for attr in ("_exclusive_end", "_exclusive_text", "_exclusive_track"):
            if hasattr(d, attr):
                delattr(d, attr)

    return MergePlan(
        ass_path=ass_path,
        txt_path=txt_path,
        dialogues=dialogues,
        notes=notes,
        total_notes=len(notes),
        auto_matched=auto_matched,
        conflicts=conflicts,
        track_colors=track_colors,
        _raw_ass_lines=raw_lines,
    )


def apply_conflict_resolution(plan: MergePlan, conflict_idx: int, a_note_idx: int, b_note_idx: int):
    """应用用户对某个冲突的决议

    Args:
        plan: 合并计划
        conflict_idx: 冲突索引
        a_note_idx: 分配给 A 的 TXT note 在冲突.notes 中的索引
        b_note_idx: 分配给 B 的 TXT note 在冲突.notes 中的索引
    """
    if conflict_idx >= len(plan.conflicts):
        return
    c = plan.conflicts[conflict_idx]

    # 分配给 A
    if 0 <= a_note_idx < len(c.notes):
        a = plan.dialogues[c.a_idx]
        a.text = c.a_text_before
        a.track = c.notes[a_note_idx].track
        if a.text:
            a.text += chr(92) + "N" + c.notes[a_note_idx].text
        else:
            a.text = c.notes[a_note_idx].text

    # 分配给 B
    if 0 <= b_note_idx < len(c.notes):
        b = plan.dialogues[c.b_idx]
        b.text = c.b_text_before
        b.track = c.notes[b_note_idx].track
        if b.text:
            b.text += chr(92) + "N" + c.notes[b_note_idx].text
        else:
            b.text = c.notes[b_note_idx].text

    # 已处理，从 conflicts 中移除
    plan.conflicts.pop(conflict_idx)
