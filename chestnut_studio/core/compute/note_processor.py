"""笔记处理器 — 纯计算函数

笔记的排序、过滤、ID 分配等操作，无 I/O 无副作用。
"""

from chestnut_studio.core.model.note import Note
from chestnut_studio.core.track_config import NOTE_TYPES


def filter_notes_by_type(notes: list[Note], note_type: str) -> list[Note]:
    """按轨道类型过滤笔记，不修改输入列表"""
    return [n for n in notes if n.type == note_type]


def get_used_note_types(notes: list[Note]) -> list[str]:
    """获取有数据的轨道列表（按 NOTE_TYPES 顺序），不修改输入列表"""
    used = set(n.type for n in notes)
    return [t for t in NOTE_TYPES if t in used]


def assign_note_ids(notes: list[Note]) -> dict[Note, int]:
    """按时间排序分配序号，不修改输入列表

    Returns:
        {Note对象: 序号} 映射，序号从 1 开始
    """
    sorted_notes = sorted(notes, key=lambda n: n.timestamp_ms)
    return {note: i for i, note in enumerate(sorted_notes, 1)}


def get_note_id(notes: list[Note], note: Note) -> int:
    """获取指定笔记在当前排序下的序号，不修改输入列表

    Returns:
        序号（从 1 开始），未找到返回 0
    """
    sorted_notes = sorted(notes, key=lambda n: n.timestamp_ms)
    for i, n in enumerate(sorted_notes, 1):
        if n is note:
            return i
    return 0
