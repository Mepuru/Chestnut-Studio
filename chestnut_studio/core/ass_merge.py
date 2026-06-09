"""ASS+TXT 字幕合并逻辑

将 Chestnut Studio 导出的 TXT 笔记文本合并到 ASS 字幕时间轴中。
**原则**: 只有 100% 确定的匹配才自动填入——即恰好 1 条 TXT 落在某条 ASS 的独占时间区内。
其他情况（多条 TXT 抢同一 ASS、时间重叠等）均放入报告中，让用户手动处理。

数据模型定义位于 core/model/ass_merge.py。
纯计算引擎位于 core/compute/ass_merge_engine.py。

用法:
    from chestnut_studio.core.ass_merge import build_merge_plan

    plan = build_merge_plan("input.ass", "notes.txt")
    print(plan.generate_report())  # 查看不确定项
    plan.write("output.ass")       # 写出 ASS + 报告
"""

from __future__ import annotations

import re

from chestnut_studio.core.compute.ass_merge_engine import compute_merge_plan
from chestnut_studio.core.model.ass_merge import (
    AssDialogue,
    MergePlan,
    TxtNote,
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


# ── 合并编排器 ──


def build_merge_plan(ass_path: str, txt_path: str) -> MergePlan:
    """构建合并计划——纯计算引擎的 I/O 编排器

    流程:
    1. 解析 ASS 和 TXT 文件
    2. 委托 compute_merge_plan 执行匹配算法
    3. 返回 MergePlan
    """
    dialogues, raw_lines = parse_ass(ass_path)
    notes, track_colors = parse_txt(txt_path)

    return compute_merge_plan(
        dialogues=dialogues,
        notes=notes,
        track_colors=track_colors,
        ass_path=ass_path,
        txt_path=txt_path,
        raw_ass_lines=raw_lines,
    )
