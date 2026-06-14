"""笔记处理器 — 纯计算函数

笔记的排序、过滤、ID 分配等操作，无 I/O 无副作用。
不依赖 core/ 下任何配置模块，所有配置通过参数传递。
"""

from collections.abc import Sequence

from chestnut_studio.core.model.note import Note


def filter_notes_by_type(notes: list[Note], note_type: str) -> list[Note]:
    """按轨道类型过滤笔记，不修改输入列表"""
    return [n for n in notes if n.type == note_type]


def get_used_note_types(notes: list[Note], note_types: Sequence[str] | None = None) -> list[str]:
    """获取有数据的轨道列表，不修改输入列表

    Args:
        notes: 笔记列表
        note_types: 可选的轨道顺序列表，提供时按此顺序返回；不提供时按出现顺序返回

    Returns:
        有数据的轨道名称列表
    """
    used = set(n.type for n in notes)
    if note_types is not None:
        return [t for t in note_types if t in used]
    # 无配置时按出现顺序返回（保持纯函数特性）
    seen: set[str] = set()
    result: list[str] = []
    for n in notes:
        t = n.type
        if t in used and t not in seen:
            seen.add(t)
            result.append(t)
    return result


def assign_note_ids(sorted_notes: list[Note]) -> dict[Note, int]:
    """为已按时间排序的笔记分配序号，不修改输入列表

    调用方需保证 sorted_notes 已按 timestamp_ms 排序。

    Returns:
        {Note对象: 序号} 映射，序号从 1 开始
    """
    return {note: i for i, note in enumerate(sorted_notes, 1)}


def search_notes(notes: list[Note], query: str) -> list[Note]:
    """按文本内容过滤笔记，大小写不敏感子串匹配

    Args:
        notes: 笔记列表
        query: 搜索关键词（空字符串或空白返回全量）

    Returns:
        匹配的笔记列表
    """
    q = query.strip()
    if not q:
        return notes
    q_lower = q.lower()
    return [n for n in notes if q_lower in n.text.lower()]


def get_note_id(sorted_notes: list[Note], note: Note) -> int:
    """获取指定笔记在已排序列表中的序号，不修改输入列表

    调用方需保证 sorted_notes 已按 timestamp_ms 排序。

    Returns:
        序号（从 1 开始），未找到返回 0
    """
    for i, n in enumerate(sorted_notes, 1):
        if n is note:
            return i
    return 0
