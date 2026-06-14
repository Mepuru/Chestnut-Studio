"""计算层测试 — 纯函数，无 I/O，零副作用

这些测试直接调用 compute/ 中的函数，不经过任何 I/O 编排器。
"""

from chestnut_studio.core.compute.ass_merge_engine import compute_merge_plan
from chestnut_studio.core.compute.note_processor import (
    assign_note_ids,
    filter_notes_by_type,
    get_note_id,
    get_used_note_types,
    search_notes,
)
from chestnut_studio.core.model.ass_merge import AssDialogue, MergePlan, TxtNote
from chestnut_studio.core.model.note import Note

# ══════════════════════════════════════════
# note_processor 纯函数测试
# ══════════════════════════════════════════


class TestNoteProcessor:
    def test_filter_notes_by_type(self):
        notes = [
            Note(1000, "A", "轨道1"),
            Note(2000, "B", "轨道2"),
            Note(3000, "C", "轨道1"),
        ]
        result = filter_notes_by_type(notes, "轨道1")
        assert len(result) == 2
        assert all(n.type == "轨道1" for n in result)

    def test_filter_notes_by_type_empty(self):
        assert filter_notes_by_type([], "轨道1") == []

    def test_filter_notes_by_type_no_match(self):
        notes = [Note(1000, "A", "轨道2")]
        assert filter_notes_by_type(notes, "轨道1") == []

    def test_filter_notes_by_type_does_not_mutate_input(self):
        notes = [Note(1000, "A", "轨道1"), Note(2000, "B", "轨道2")]
        original_len = len(notes)
        filter_notes_by_type(notes, "轨道1")
        assert len(notes) == original_len  # 输入未被修改

    def test_get_used_note_types(self):
        notes = [
            Note(1000, "A", "轨道1"),
            Note(2000, "B", "轨道2"),
            Note(3000, "C", "轨道1"),
        ]
        used = get_used_note_types(notes)
        assert used == ["轨道1", "轨道2"]

    def test_get_used_note_types_empty(self):
        assert get_used_note_types([]) == []

    def test_get_used_note_types_maintains_order(self):
        """无配置时按输入中首次出现顺序返回"""
        notes = [
            Note(1000, "C", "轨道3"),
            Note(2000, "A", "轨道1"),
        ]
        used = get_used_note_types(notes)
        assert used[0] == "轨道3"  # 首个出现的轨道
        assert used[1] == "轨道1"

    def test_get_used_note_types_with_custom_order(self):
        """可传入自定义轨道顺序"""
        notes = [
            Note(1000, "A", "轨道1"),
            Note(2000, "B", "轨道3"),
            Note(3000, "C", "轨道2"),
        ]
        custom_order = ["轨道3", "轨道1", "轨道2"]
        used = get_used_note_types(notes, custom_order)
        assert used == ["轨道3", "轨道1", "轨道2"]

    def test_assign_note_ids(self):
        notes = [
            Note(1000, "A"),
            Note(2000, "C"),
            Note(3000, "B"),
        ]
        id_map = assign_note_ids(notes)
        assert len(id_map) == 3
        # 已排序: A:1000 → 1, C:2000 → 2, B:3000 → 3
        a_note = next(n for n in notes if n.text == "A")
        b_note = next(n for n in notes if n.text == "B")
        c_note = next(n for n in notes if n.text == "C")
        assert id_map[a_note] == 1
        assert id_map[c_note] == 2
        assert id_map[b_note] == 3

    def test_assign_note_ids_does_not_mutate_input(self):
        notes = [Note(2000, "B"), Note(1000, "A")]
        original_order = list(notes)
        assign_note_ids(notes)
        # 函数不应修改输入
        assert notes == original_order

    def test_assign_note_ids_empty(self):
        assert assign_note_ids([]) == {}

    def test_get_note_id(self):
        notes = [Note(1000, "A"), Note(2000, "B"), Note(3000, "C")]
        target = notes[1]  # B 在已排序列表中位置 2
        assert get_note_id(notes, target) == 2

    def test_get_note_id_not_found(self):
        notes = [Note(1000, "A")]
        other = Note(2000, "B")
        assert get_note_id(notes, other) == 0

    def test_get_note_id_empty(self):
        assert get_note_id([], Note(1000, "A")) == 0

    # ── search_notes ──

    def test_search_notes_match(self):
        notes = [
            Note(1000, "Hello World"),
            Note(2000, "Goodbye World"),
            Note(3000, "Foo Bar"),
        ]
        result = search_notes(notes, "world")
        assert len(result) == 2
        assert all("world" in n.text.lower() for n in result)

    def test_search_notes_empty_query(self):
        notes = [Note(1000, "Hello"), Note(2000, "World")]
        result = search_notes(notes, "")
        assert result is notes
        result = search_notes(notes, "   ")
        assert result is notes

    def test_search_notes_no_match(self):
        notes = [Note(1000, "Hello"), Note(2000, "World")]
        assert search_notes(notes, "xyz") == []

    def test_search_notes_case_insensitive(self):
        notes = [Note(1000, "HELLO"), Note(2000, "hello"), Note(3000, "World")]
        result = search_notes(notes, "hello")
        assert len(result) == 2

    def test_search_notes_does_not_mutate_input(self):
        notes = [Note(1000, "Hello"), Note(2000, "World")]
        original_len = len(notes)
        search_notes(notes, "hello")
        assert len(notes) == original_len

    def test_search_notes_empty_list(self):
        assert search_notes([], "test") == []


# ══════════════════════════════════════════
# ass_merge_engine 纯函数测试
# ══════════════════════════════════════════


def _make_dialogue(start_s: float, end_s: float, line_index: int = 0) -> AssDialogue:
    """构造一条不含 I/O 的 AssDialogue 纯数据"""
    return AssDialogue(
        line_index=line_index,
        start_s=start_s,
        end_s=end_s,
        start_str=f"{int(start_s // 3600)}:{int(start_s % 3600 // 60):02d}:{start_s % 60:05.2f}",
        end_str=f"{int(end_s // 3600)}:{int(end_s % 3600 // 60):02d}:{end_s % 60:05.2f}",
        style="Default",
        text="",
        raw_before_text="Dialogue: 0,",
    )


def _make_note(time_s: float, text: str, track: str = "轨道1", index: int = 1) -> TxtNote:
    """构造一条不含 I/O 的 TxtNote 纯数据"""
    return TxtNote(index=index, time_s=time_s, track=track, text=text)


class TestAssMergeEngine:
    """直接测试 compute_merge_plan 纯函数（无文件 I/O）"""

    def test_simple_non_overlap(self):
        dialogues = [
            _make_dialogue(1.0, 4.0, line_index=0),
            _make_dialogue(5.0, 8.0, line_index=1),
        ]
        notes = [
            _make_note(2.0, "笔记A", index=1),
            _make_note(6.0, "笔记B", index=2),
        ]
        plan = compute_merge_plan(dialogues, notes, {"轨道1": "#3b82f6"})
        assert plan.total_notes == 2
        assert plan.auto_matched == 2
        assert len(plan.uncertain) == 0
        assert len(plan.risky) == 0
        assert plan.dialogues[0].text == "笔记A"
        assert plan.dialogues[1].text == "笔记B"

    def test_single_txt_in_overlap(self):
        """重叠区内单条 TXT，按时间就近分配"""
        dialogues = [
            _make_dialogue(1.0, 6.0, line_index=0),
            _make_dialogue(4.0, 9.0, line_index=1),
        ]
        notes = [_make_note(4.5, "中间笔记", index=1)]
        plan = compute_merge_plan(dialogues, notes, {"轨道1": "#3b82f6"})
        assert plan.auto_matched == 1
        assert len(plan.risky) == 1
        assert len(plan.uncertain) == 0

    def test_multiple_txt_in_exclusive(self):
        """独占区内多条 TXT → 不确定"""
        dialogues = [_make_dialogue(1.0, 6.0, line_index=0)]
        notes = [
            _make_note(2.0, "笔记A", index=1),
            _make_note(4.0, "笔记B", index=2),
        ]
        plan = compute_merge_plan(dialogues, notes, {"轨道1": "#3b82f6"})
        assert plan.auto_matched == 0
        assert len(plan.uncertain) == 1
        assert len(plan.uncertain[0].notes) == 2

    def test_no_notes(self):
        """无 TXT 笔记"""
        dialogues = [_make_dialogue(1.0, 4.0, line_index=0)]
        plan = compute_merge_plan(dialogues, [], {})
        assert plan.total_notes == 0
        assert plan.auto_matched == 0
        assert len(plan.uncertain) == 0

    def test_no_dialogues(self):
        """无 ASS Dialogue"""
        plan = compute_merge_plan([], [_make_note(1.0, "笔记A")], {})
        assert plan.total_notes == 1
        assert plan.auto_matched == 0
        assert len(plan.uncertain) == 0

    def test_preserves_track_colors(self):
        """轨道颜色传递"""
        colors = {"轨道1": "#3b82f6", "轨道2": "#10b981"}
        plan = compute_merge_plan([], [], colors)
        assert plan.track_colors == colors

    def test_returns_merge_plan_type(self):
        plan = compute_merge_plan([], [], {})
        assert isinstance(plan, MergePlan)

    def test_does_not_mutate_input_dialogues(self):
        """计算后输入列表中的原始 AssDialogue 对象不应被修改"""
        d1 = _make_dialogue(1.0, 4.0, line_index=0)
        d2 = _make_dialogue(5.0, 8.0, line_index=1)
        original_d1_text = d1.text
        original_d2_text = d2.text
        original_d1_track = d1.track
        original_d2_track = d2.track

        dialogues = [d1, d2]
        notes = [_make_note(2.0, "笔记A", index=1)]
        plan = compute_merge_plan(dialogues, notes, {})
        # 输入对象不应被修改
        assert d1.text == original_d1_text
        assert d2.text == original_d2_text
        assert d1.track == original_d1_track
        assert d2.track == original_d2_track
        # 结果在 MergePlan 内部的新对象上
        assert plan.dialogues[0].text == "笔记A"

    def test_chain_overlap_notes_correctly_matched(self):
        """三链重叠中每条独占区内的笔记正确匹配"""
        dialogues = [
            _make_dialogue(0.0, 5.0, line_index=0),
            _make_dialogue(3.0, 8.0, line_index=1),
            _make_dialogue(6.0, 10.0, line_index=2),
        ]
        notes = [
            _make_note(1.0, "A独占", track="轨道1", index=1),
            _make_note(5.5, "B独占", track="轨道1", index=2),
            _make_note(9.0, "C独占", track="轨道1", index=3),
        ]
        plan = compute_merge_plan(dialogues, notes, {"轨道1": "#3b82f6"})
        assert plan.auto_matched == 3
        assert len(plan.uncertain) == 0
        assert len(plan.risky) == 0
        assert len(plan.unmatched) == 0
        assert plan.dialogues[0].text == "A独占"
        assert plan.dialogues[1].text == "B独占"
        assert plan.dialogues[2].text == "C独占"

    def test_chain_5_overlap_notes_correctly_matched(self):
        """五链重叠中各独占区笔记正确自动匹配"""
        dialogues = [
            _make_dialogue(0.0, 5.0, line_index=0),
            _make_dialogue(3.0, 8.0, line_index=1),
            _make_dialogue(6.0, 11.0, line_index=2),
            _make_dialogue(9.0, 14.0, line_index=3),
            _make_dialogue(12.0, 17.0, line_index=4),
        ]
        notes = [
            _make_note(1.0, "A独占", track="轨道1", index=1),
            _make_note(5.5, "B独占", track="轨道1", index=2),
            _make_note(8.5, "C独占", track="轨道1", index=3),
            _make_note(11.5, "D独占", track="轨道1", index=4),
            _make_note(15.0, "E独占", track="轨道1", index=5),
        ]
        plan = compute_merge_plan(dialogues, notes, {"轨道1": "#3b82f6"})
        assert plan.auto_matched == 5
        assert len(plan.uncertain) == 0
        assert len(plan.risky) == 0
        assert len(plan.unmatched) == 0
        assert plan.dialogues[0].text == "A独占"
        assert plan.dialogues[1].text == "B独占"
        assert plan.dialogues[2].text == "C独占"
        assert plan.dialogues[3].text == "D独占"
        assert plan.dialogues[4].text == "E独占"

    def test_chain_5_overlap_notes_not_leaked_into_exclusive(self):
        """五链重叠中重叠区笔记不覆写已独占匹配的 dialogue"""
        dialogues = [
            _make_dialogue(0.0, 5.0, line_index=0),
            _make_dialogue(3.0, 8.0, line_index=1),
            _make_dialogue(6.0, 11.0, line_index=2),
            _make_dialogue(9.0, 14.0, line_index=3),
            _make_dialogue(12.0, 17.0, line_index=4),
        ]
        notes = [
            _make_note(1.0, "A独占", track="轨道1", index=1),
            _make_note(4.0, "A-B重叠", track="轨道1", index=2),
            _make_note(5.5, "B独占", track="轨道1", index=3),
            _make_note(7.0, "B-C重叠", track="轨道1", index=4),
            _make_note(8.5, "C独占", track="轨道1", index=5),
            _make_note(10.0, "C-D重叠", track="轨道1", index=6),
            _make_note(11.5, "D独占", track="轨道1", index=7),
            _make_note(13.0, "D-E重叠", track="轨道1", index=8),
            _make_note(15.0, "E独占", track="轨道1", index=9),
        ]
        plan = compute_merge_plan(dialogues, notes, {"轨道1": "#3b82f6"})
        # 独占区 5 条自动匹配；两侧均已独占总 4 条 → uncertain，不覆写
        assert plan.auto_matched == 5
        assert len(plan.uncertain) == 4
        assert len(plan.risky) == 0
        assert len(plan.unmatched) == 0
        # 独占区笔记不被覆写
        assert plan.dialogues[0].text == "A独占"
        assert plan.dialogues[1].text == "B独占"
        assert plan.dialogues[2].text == "C独占"
        assert plan.dialogues[3].text == "D独占"
        assert plan.dialogues[4].text == "E独占"
