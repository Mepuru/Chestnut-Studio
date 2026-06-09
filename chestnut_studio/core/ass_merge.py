"""ASS+TXT 字幕合并逻辑

将 Chestnut Studio 导出的 TXT 笔记文本合并到 ASS 字幕时间轴中。
**原则**: 只有 100% 确定的匹配才自动填入——即恰好 1 条 TXT 落在某条 ASS 的独占时间区内。
其他情况（多条 TXT 抢同一 ASS、时间重叠等）均放入报告中，让用户手动处理。

数据模型定义位于 core/model/ass_merge.py。

用法:
    from chestnut_studio.core.ass_merge import build_merge_plan

    plan = build_merge_plan("input.ass", "notes.txt")
    print(plan.generate_report())  # 查看不确定项
    plan.write("output.ass")       # 写出 ASS + 报告
"""

from __future__ import annotations

import re

from chestnut_studio.core.model.ass_merge import (
    AssDialogue,
    MergePlan,
    TxtNote,
    UncertainMatch,
)

# ── 解析器 ──


def _parse_ass_time(s: str) -> float:
    """h:mm:ss.xx → 秒，解析失败返回 0.0"""
    try:
        parts = s.split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except (ValueError, IndexError):
        return 0.0


def _parse_txt_time(s: str) -> float:
    """mm:ss.xx 或 h:mm:ss.xx → 秒，解析失败返回 0.0"""
    try:
        parts = s.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except (ValueError, IndexError):
        return 0.0


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
            try:
                prefix = line[:idx]  # 前9个字段
                parts = prefix.split(",")
                # parts[1]=start, parts[2]=end, parts[3]=style
                start_str = parts[1].strip()
                end_str = parts[2].strip()
                d = AssDialogue(
                    line_index=i,
                    start_s=_parse_ass_time(start_str),
                    end_s=_parse_ass_time(end_str),
                    start_str=start_str,
                    end_str=end_str,
                    style=parts[3].strip(),
                    text="",
                    raw_before_text=prefix,
                )
                dialogues.append(d)
            except (ValueError, IndexError):
                continue

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
        d._exclusive_end = d.end_s

    for op in overlap_pairs:
        a = dialogues[op["a_idx"]]
        b = dialogues[op["b_idx"]]
        a._exclusive_end = op["zone_start"]
        b._exclusive_end = b.start_s

    # ── 第一轮：独占区收集 ──
    for note in notes:
        for d in dialogues:
            excl_end = d._exclusive_end
            if d.start_s <= note.time_s < excl_end:
                d._exclusive_notes.append(note)
                break

    # ── 第二轮：确定匹配 / 入不确定列表 ──
    uncertain: list[UncertainMatch] = []
    risky: list[UncertainMatch] = []
    auto_matched = 0

    for di, d in enumerate(dialogues):
        zone_notes = d._exclusive_notes
        if not zone_notes:
            continue

        if len(zone_notes) == 1:
            # ✅ 100% 确定：独占区内恰好 1 条 TXT
            note = zone_notes[0]
            d._exclusive_text = note.text
            d._exclusive_track = note.track
            d._exclusive_note_idx = note.index
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
        for n in d._exclusive_notes:
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
            # 多条 ASS 竞争同一重叠区间
            # 如果只有 1 条 TXT，按时间就近分配
            if len(zone_notes) == 1:
                note = zone_notes[0]
                a = dialogues[op["a_idx"]]
                b = dialogues[op["b_idx"]]
                # 选离 start 更近的那条 ASS
                if abs(note.time_s - a.start_s) <= abs(note.time_s - b.start_s):
                    a._exclusive_text = note.text
                    a._exclusive_track = note.track
                    a._exclusive_note_idx = note.index
                else:
                    b._exclusive_text = note.text
                    b._exclusive_track = note.track
                    b._exclusive_note_idx = note.index
                auto_matched += 1
                # 记录为潜在风险
                risky.append(
                    UncertainMatch(
                        ass_idx=op["a_idx"]
                        if abs(note.time_s - a.start_s) <= abs(note.time_s - b.start_s)
                        else op["b_idx"],
                        ass_start=a.start_str
                        if abs(note.time_s - a.start_s) <= abs(note.time_s - b.start_s)
                        else b.start_str,
                        ass_end=a.end_str
                        if abs(note.time_s - a.start_s) <= abs(note.time_s - b.start_s)
                        else b.end_str,
                        notes=[note],
                        reason="重叠区——按时间就近分配到 %s"
                        % ("A 轴" if abs(note.time_s - a.start_s) <= abs(note.time_s - b.start_s) else "B 轴"),
                    )
                )
            else:
                # 多条 TXT 争重叠区，无法自动判断
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
        d.text = d._exclusive_text
        d.track = d._exclusive_track
        d.src_note_idx = d._exclusive_note_idx

    return MergePlan(
        ass_path=ass_path,
        txt_path=txt_path,
        dialogues=dialogues,
        notes=notes,
        total_notes=len(notes),
        auto_matched=auto_matched,
        uncertain=uncertain,
        risky=risky,
        track_colors=track_colors,
        _raw_ass_lines=raw_lines,
    )
