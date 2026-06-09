"""ASS+TXT 合并结果输出

将 MergePlan 写出为 ASS 文件和文本报告。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from chestnut_studio.core.model.ass_merge import AssDialogue, MergePlan
from chestnut_studio.utils.version import get_version


def _hex_to_ass_color(hex_str: str) -> str:
    """#RRGGBB → &H00BBGGRR"""
    h = hex_str.lstrip("#")
    if len(h) != 6:
        return "&H00FFFFFF"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}"


def _build_style_line(name: str, color_hex: str) -> str:
    """生成 ASS Style 行"""
    primary = _hex_to_ass_color(color_hex)
    return (
        f"Style: {name},思源黑体 CN,70,{primary},&H000000FF,"
        f"&H00000000,&HFF000000,-1,0,0,0,100,100,0,0,1,5,5,2,10,10,10,1"
    )


def _collect_used_tracks(dialogues: list[AssDialogue]) -> list[str]:
    """收集用到的轨道名（去重，保持出现顺序）"""
    used: list[str] = []
    seen: set[str] = set()
    for d in dialogues:
        t = d.track
        if t and t not in seen:
            seen.add(t)
            used.append(t)
    return used


def generate_merge_report(plan: MergePlan) -> str:
    """生成合并报告——三节：待处理 / 潜在风险 / 自动匹配"""
    total_ass = len(plan.dialogues)
    filled = sum(1 for d in plan.dialogues if d.text)
    empty = total_ass - filled
    pct = 100.0 * plan.auto_matched / plan.total_notes if plan.total_notes else 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    color_summary = (
        ", ".join(f"{k}={v}" for k, v in sorted(plan.track_colors.items())) if plan.track_colors else "（无）"
    )

    lines: list[str] = []
    lines.append("# Chestnut Studio - ASS/TXT 合并报告 v" + get_version())
    lines.append("# 导出时间: " + now)
    lines.append("# ---")
    lines.append("# 源 ASS: " + Path(plan.ass_path).name)
    lines.append("# 源 TXT: " + Path(plan.txt_path).name)
    lines.append("#")
    lines.append(f"# ASS 行数: {total_ass} / TXT 笔记数: {plan.total_notes}")
    lines.append(f"# 自动匹配: {plan.auto_matched} / {plan.total_notes}（{pct:.1f}%）")
    lines.append(f"# 潜在风险: {len(plan.risky)} 项 / 待处理: {len(plan.uncertain)} 项 / 空行: {empty}")
    lines.append("# 轨道颜色: " + color_summary)
    lines.append("# ---")
    lines.append("")
    lines.append(f"# 第 1 节 — 待手动处理（{len(plan.uncertain)} 项）")
    lines.append("")

    if not plan.uncertain:
        lines.append("# 无待处理项。")
        lines.append("")
    else:
        for i, u in enumerate(plan.uncertain, 1):
            lines.append(f"{i}. ASS #{u.ass_idx + 1}  {u.ass_start} → {u.ass_end}")
            lines.append(f"   原因: {u.reason}")
            for n in u.notes:
                lines.append(f"   · TXT #{n.index}  [{n.track}]  {n.text}")
            lines.append("")

    lines.append("# ---")
    lines.append("")
    lines.append(f"# 第 2 节 — 潜在风险（{len(plan.risky)} 项）")
    lines.append("# 说明：以下条目在重叠时间段内自动分配，建议在 Aegisub 中复核。")
    lines.append("")

    if not plan.risky:
        lines.append("# 无潜在风险项。")
        lines.append("")
    else:
        for i, r in enumerate(plan.risky, 1):
            sourceline = ""
            if r.notes:
                n = r.notes[0]
                sourceline = f"  | 源 TXT #{n.index}  [{n.track}]  {n.text}"
            lines.append(f"{i}. ASS #{r.ass_idx + 1}  {r.ass_start} → {r.ass_end}")
            lines.append(f"   原因: {r.reason}")
            if sourceline:
                lines.append(sourceline)
            lines.append("")

    lines.append("# ---")
    lines.append("")

    safe_indices = set(r.ass_idx for r in plan.risky)
    safe_items = [d for i, d in enumerate(plan.dialogues) if d.text and i not in safe_indices]
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


def write_output(plan: MergePlan, output_path: str) -> tuple[str, str]:
    """写出合并后的 ASS 文件 + 同目录下的报告"""
    ass_path = Path(output_path)

    lines = _repr_lines(plan)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    report_name = ass_path.stem.replace("M_", "R_") + ".txt"
    report_path = ass_path.with_name(report_name)
    report_path.write_text(generate_merge_report(plan), encoding="utf-8")

    return str(ass_path), str(report_path)


def _repr_lines(plan: MergePlan) -> list[str]:
    """按 ASS 节段重组输出行"""
    raw = plan._raw_ass_lines

    sections: list[tuple[int, str]] = []
    for i, line in enumerate(raw):
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            sections.append((i, s))

    styles_sec = next((s for s in sections if s[1] == "[V4+ Styles]"), None)
    events_sec = next((s for s in sections if s[1] == "[Events]"), None)

    if not styles_sec or not events_sec:
        new_lines = list(raw)
        for d in plan.dialogues:
            prefix = d.raw_before_text
            if d.track:
                parts = prefix.split(",", 8)
                if len(parts) > 3:
                    parts[3] = d.track
                    prefix = ",".join(parts)
            new_lines[d.line_index] = prefix + "," + d.text
        return new_lines

    result = list(raw[: styles_sec[0] + 1])

    fmt = (
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding"
    )
    result.append(fmt)
    for t in _collect_used_tracks(plan.dialogues):
        color = plan.track_colors.get(t, "#FFFFFF")
        result.append(_build_style_line(t, color))

    result.append("[Events]")
    for i in range(events_sec[0] + 1, len(raw)):
        line = raw[i]
        if line.startswith("Dialogue:"):
            di = next((d for d in plan.dialogues if d.line_index == i), None)
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
