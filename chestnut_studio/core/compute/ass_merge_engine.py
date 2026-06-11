"""ASS+TXT 字幕合并引擎 — 纯计算函数

核心匹配算法，无文件 I/O。输入已解析的 ASS Dialogues 和 TXT Notes，
输出合并计划。不修改输入参数，所有中间状态使用局部变量。

**原则**: 只有 100% 确定的匹配才自动填入——即恰好 1 条 TXT 落在某条 ASS 的独占时间区内。
"""

from dataclasses import dataclass, field, replace
from typing import NamedTuple

from chestnut_studio.core.model.ass_merge import (
    AssDialogue,
    MergePlan,
    TxtNote,
    UncertainMatch,
)


@dataclass
class _ExclusiveState:
    """独占区中间状态（仅在 compute_merge_plan 内部使用）"""

    end: float = 0.0
    notes: list[TxtNote] = field(default_factory=lambda: [])
    text: str = ""
    track: str = ""
    note_idx: int = 0


class _OverlapPair(NamedTuple):
    """单一重叠对"""

    a_idx: int
    b_idx: int
    zone_start: float
    zone_end: float


def _detect_overlap_pairs(dialogues: list[AssDialogue]) -> list[_OverlapPair]:
    """检测连续 ASS Dialogue 之间的时间重叠对"""
    pairs: list[_OverlapPair] = []
    for di in range(len(dialogues) - 1):
        a, b = dialogues[di], dialogues[di + 1]
        if a.end_s > b.start_s + 0.05:  # > 50ms 视为有效重叠
            pairs.append(
                _OverlapPair(
                    a_idx=di,
                    b_idx=di + 1,
                    zone_start=b.start_s,
                    zone_end=min(a.end_s, b.end_s),
                )
            )
    return pairs


def _mark_exclusive_zones(
    dialogues: list[AssDialogue], overlap_pairs: list[_OverlapPair], state: dict[int, _ExclusiveState]
) -> None:
    """标记每条 ASS 的独占区结束点（写入 state）

    重叠区中:
      - 先出现的 A: 独占区 = [A.start, overlap_start)，overlap 部分被截掉
      - 后出现的 B: 独占区 = [B.start, B.start)（零长度），全文在重叠区内
    """
    for di, d in enumerate(dialogues):
        state[di].end = d.end_s

    for op in overlap_pairs:
        state[op.a_idx].end = op.zone_start
        b = dialogues[op.b_idx]
        state[op.b_idx].end = b.start_s  # B 的独占区为零长度


def _collect_exclusive_notes(
    dialogues: list[AssDialogue], notes: list[TxtNote], state: dict[int, _ExclusiveState]
) -> None:
    """将笔记分配到独占区（写入 state）"""
    for note in notes:
        for di, d in enumerate(dialogues):
            excl_end = state[di].end
            if d.start_s <= note.time_s < excl_end:
                state[di].notes.append(note)
                break


def _resolve_exclusive_matches(
    dialogues: list[AssDialogue], state: dict[int, _ExclusiveState]
) -> tuple[int, list[UncertainMatch], set[int]]:
    """独占区匹配：恰好 1 条 → 自动匹配，多条 → 入不确定列表

    Returns:
        (auto_matched, uncertain, matched_note_indices)
    """
    uncertain: list[UncertainMatch] = []
    auto_matched = 0

    for di, d in enumerate(dialogues):
        zone_notes = state[di].notes
        if not zone_notes:
            continue

        if len(zone_notes) == 1:
            note = zone_notes[0]
            state[di].text = note.text
            state[di].track = note.track
            state[di].note_idx = note.index
            auto_matched += 1
        else:
            uncertain.append(
                UncertainMatch(
                    ass_idx=di,
                    ass_start=d.start_str,
                    ass_end=d.end_str,
                    notes=zone_notes,
                    reason=f"同一条 ASS 时间窗口内有 {len(zone_notes)} 条 TXT 笔记",
                )
            )

    matched_note_indices: set[int] = set()
    for st in state.values():
        for n in st.notes:
            matched_note_indices.add(n.index)

    return auto_matched, uncertain, matched_note_indices


def _resolve_overlap_notes(
    dialogues: list[AssDialogue],
    notes: list[TxtNote],
    overlap_pairs: list[_OverlapPair],
    matched_note_indices: set[int],
    uncertain: list[UncertainMatch],
    state: dict[int, _ExclusiveState],
) -> tuple[list[UncertainMatch], int]:
    """处理重叠区未匹配的 TXT 笔记

    Returns:
        (risky, additional_auto_matched)
    """
    risky: list[UncertainMatch] = []
    additional_auto = 0

    overlap_notes = [n for n in notes if n.index not in matched_note_indices]

    for op in overlap_pairs:
        zone_notes: list[TxtNote] = []
        remaining: list[TxtNote] = []
        for note in overlap_notes:
            if op.zone_start <= note.time_s <= op.zone_end:
                zone_notes.append(note)
            else:
                remaining.append(note)
        overlap_notes = remaining

        if not zone_notes:
            continue

        a = dialogues[op.a_idx]
        b = dialogues[op.b_idx]

        # 收集哪些 ASS 行可能被这些 TXT 匹配
        involved: list[int] = []
        seen: set[int] = set()
        for note in zone_notes:
            for di, d in enumerate(dialogues):
                if d.start_s <= note.time_s <= d.end_s and di not in seen:
                    seen.add(di)
                    involved.append(di)

        if len(involved) == 1:
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
            if len(zone_notes) == 1:
                note = zone_notes[0]
                is_a = abs(note.time_s - a.start_s) <= abs(note.time_s - b.start_s)
                target_idx = op.a_idx if is_a else op.b_idx
                state[target_idx].text = note.text
                state[target_idx].track = note.track
                state[target_idx].note_idx = note.index
                additional_auto += 1
                risky.append(
                    UncertainMatch(
                        ass_idx=target_idx,
                        ass_start=a.start_str if is_a else b.start_str,
                        ass_end=a.end_str if is_a else b.end_str,
                        notes=[note],
                        reason="重叠区——按时间就近分配到 %s" % ("A 轴" if is_a else "B 轴"),
                    )
                )
            else:
                for ai in involved:
                    ass_notes: list[TxtNote] = [
                        n for n in zone_notes if dialogues[ai].start_s <= n.time_s <= dialogues[ai].end_s
                    ]
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

    return risky, additional_auto


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
    使用 dataclasses.replace() 创建新的 AssDialogue 对象，
    输入列表中的原始对象不会被修改。

    Args:
        dialogues: 已解析的 ASS Dialogue 列表（不会被修改）
        notes: 已解析的 TXT Note 列表
        track_colors: 轨道名 → 颜色映射
        ass_path: ASS 文件路径（仅用于 MergePlan 记录）
        txt_path: TXT 文件路径（仅用于 MergePlan 记录）
        raw_ass_lines: 原始 ASS 行（仅用于 MergePlan 记录）

    Returns:
        包含匹配结果的 MergePlan（内部 dialogues 为新建对象，不影响输入）
    """
    if raw_ass_lines is None:
        raw_ass_lines = []

    # 初始化每个 dialogue 的独占区状态
    state: dict[int, _ExclusiveState] = {di: _ExclusiveState() for di in range(len(dialogues))}

    # 1. 检测重叠对
    overlap_pairs = _detect_overlap_pairs(dialogues)

    # 2. 标记独占区
    _mark_exclusive_zones(dialogues, overlap_pairs, state)

    # 3. 独占区收集 + 匹配
    _collect_exclusive_notes(dialogues, notes, state)
    auto_matched, uncertain, matched_note_indices = _resolve_exclusive_matches(dialogues, state)

    # 4. 处理重叠区
    risky, additional_auto = _resolve_overlap_notes(
        dialogues, notes, overlap_pairs, matched_note_indices, uncertain, state
    )
    auto_matched += additional_auto

    # 5. 收集所有已消费的笔记索引，找出完全未匹配的笔记
    consumed_indices: set[int] = set()
    for st in state.values():
        if st.note_idx > 0:
            consumed_indices.add(st.note_idx)
    for u in uncertain:
        for n in u.notes:
            consumed_indices.add(n.index)
    for r in risky:
        for n in r.notes:
            consumed_indices.add(n.index)
    unmatched = [n for n in notes if n.index not in consumed_indices]

    # 6. 创建新 dialogue 对象写入结果（不修改输入列表中的原始对象）
    result_dialogues = [
        replace(d, text=state[di].text, track=state[di].track, src_note_idx=state[di].note_idx)
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
