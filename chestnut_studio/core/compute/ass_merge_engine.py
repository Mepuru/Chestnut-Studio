"""ASS+TXT 字幕合并引擎 — 纯计算函数

核心匹配算法，无文件 I/O。输入已解析的 ASS Dialogues 和 TXT Notes，
输出合并计划。不修改输入参数，所有中间状态使用局部变量。

**算法**: Sweep-line 扫描线。将 ASS 起止和 TXT 笔记按时间排序后单遍扫描：
  1. 当前只有 1 条 ASS 激活 → 该区域的笔记 100% 属于它
  2. 当前有 2+ 条 ASS 激活 → 收集到重叠区，后续用冲突感知分配
  3. 没有 ASS 激活 → 笔记标记为未匹配
  重叠区内先做 Voronoi 近邻分配，已被独占占用的轴自动跳过。
"""

from dataclasses import replace
from enum import IntEnum, auto

from chestnut_studio.core.model.ass_merge import (
    AssDialogue,
    MergePlan,
    TxtNote,
    UncertainMatch,
)


class _EventKind(IntEnum):
    """事件类型枚举——排序时 start 优先于 note 优先于 end"""

    DIALOG_START = auto()
    NOTE = auto()
    DIALOG_END = auto()


def compute_merge_plan(
    dialogues: list[AssDialogue],
    notes: list[TxtNote],
    track_colors: dict[str, str],
    ass_path: str = "",
    txt_path: str = "",
    raw_ass_lines: list[str] | None = None,
) -> MergePlan:
    """从已解析的 ASS dialogues 和 TXT notes 构建合并计划

    纯计算函数：不修改输入参数，无 I/O 操作，结果由输入完全决定。

    Args:
        dialogues: 已解析的 ASS Dialogue 列表（不会被修改）
        notes: 已解析的 TXT Note 列表
        track_colors: 轨道名 → 颜色映射
        ass_path: ASS 文件路径（仅用于 MergePlan 记录）
        txt_path: TXT 文件路径（仅用于 MergePlan 记录）
        raw_ass_lines: 原始 ASS 行（仅用于 MergePlan 记录）

    Returns:
        包含匹配结果的 MergePlan
    """
    if raw_ass_lines is None:
        raw_ass_lines = []

    # ── 1. 构建扫描线事件 ──
    events: list[tuple[float, _EventKind, int | TxtNote]] = []
    for di, d in enumerate(dialogues):
        events.append((d.start_s, _EventKind.DIALOG_START, di))
        events.append((d.end_s, _EventKind.DIALOG_END, di))
    for note in notes:
        events.append((note.time_s, _EventKind.NOTE, note))
    # DIALOG_START(1) < NOTE(2) < DIALOG_END(3)：同一时刻，start 先于 note，note 先于 end
    events.sort(key=lambda x: (x[0], x[1].value))

    # ── 2. 单遍扫描 ──
    # 结果容器
    assignments: dict[int, TxtNote] = {}  # di → note（独占区自动匹配）
    overlap_regions: list[list[TxtNote]] = []  # 每个重叠区的笔记桶
    overlap_active_sets: list[set[int]] = []  # 对应每个桶的激活 dialogue 集合
    uncertain: list[UncertainMatch] = []
    unmatched_notes: list[TxtNote] = []

    active: set[int] = set()
    current_region_notes: list[TxtNote] = []

    def _flush_region():
        """结束当前区域：把收集到的笔记转入对应的结果桶"""
        nonlocal current_region_notes
        if not current_region_notes:
            return
        if len(active) == 1:
            di = next(iter(active))
            if len(current_region_notes) == 1:
                # 独占区恰好 1 条 → 100% 确定
                assignments[di] = current_region_notes[0]
            else:
                # 独占区 2+ 条 → 无法确定，全部 uncertain
                for note in current_region_notes:
                    _add_to_uncertain([di], note, uncertain, dialogues)
        elif len(active) >= 2:
            overlap_regions.append(current_region_notes)
            overlap_active_sets.append(active.copy())
        else:
            unmatched_notes.extend(current_region_notes)
        current_region_notes = []

    for _time, kind, data in events:
        if kind is _EventKind.DIALOG_START:
            _flush_region()
            active.add(data)  # type: ignore[arg-type]
        elif kind is _EventKind.DIALOG_END:
            _flush_region()
            active.discard(data)  # type: ignore[arg-type]
        else:
            current_region_notes.append(data)  # type: ignore[arg-type]

    # 扫尾
    _flush_region()

    # ── 3. 处理重叠区（冲突感知分配） ──
    risky: list[UncertainMatch] = []

    for region_notes, active_set in zip(overlap_regions, overlap_active_sets):
        for note in region_notes:
            candidates = [
                di for di in active_set if dialogues[di].start_s <= note.time_s <= dialogues[di].end_s
            ]
            if not candidates:
                unmatched_notes.append(note)
                continue

            free = [di for di in candidates if di not in assignments]

            if not free:
                _add_to_uncertain(candidates, note, uncertain, dialogues)
                continue

            chosen = min(free, key=lambda di: abs(note.time_s - dialogues[di].start_s))
            assignments[chosen] = note
            risky.append(
                UncertainMatch(
                    ass_idx=chosen,
                    ass_start=dialogues[chosen].start_str,
                    ass_end=dialogues[chosen].end_str,
                    notes=[note],
                    reason="重叠区——Voronoi 分配到最邻近轴",
                )
            )

    # ── 5. 统计 ──
    auto_matched = len(assignments)
    consumed: set[int] = set()
    for note in assignments.values():
        consumed.add(note.index)
    for u in uncertain:
        for n in u.notes:
            consumed.add(n.index)
    for r in risky:
        for n in r.notes:
            consumed.add(n.index)
    unmatched = [n for n in notes if n.index not in consumed]

    # ── 6. 构建结果 ──
    result_dialogues = [
        replace(
            d,
            text=assignments[di].text if di in assignments else "",
            track=assignments[di].track if di in assignments else "",
            src_note_idx=assignments[di].index if di in assignments else 0,
        )
        for di, d in enumerate(dialogues)
    ]

    return MergePlan(
        ass_path=ass_path,
        txt_path=txt_path,
        dialogues=result_dialogues,
        notes=notes,
        total_notes=len(notes),
        auto_matched=auto_matched,
        uncertain=uncertain,
        risky=risky,
        unmatched=unmatched,
        track_colors=track_colors,
        _raw_ass_lines=raw_ass_lines,
    )


def _add_to_uncertain(
    candidates: list[int], note: TxtNote, uncertain: list[UncertainMatch], dialogues: list[AssDialogue]
) -> None:
    """将笔记追加到 uncertain 列表（合并或新建条目）"""
    for entry in uncertain:
        if entry.ass_idx in candidates:
            entry.notes.append(note)
            return
    # 没有对应条目的，新建一个
    first = candidates[0]
    uncertain.append(
        UncertainMatch(
            ass_idx=first,
            ass_start=dialogues[first].start_str,
            ass_end=dialogues[first].end_str,
            notes=[note],
            reason="重叠区——所有候选轴均已占满",
        )
    )
