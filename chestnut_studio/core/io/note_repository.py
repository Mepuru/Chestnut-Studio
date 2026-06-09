"""笔记文件读写

纯 I/O 操作：从磁盘读取或写入笔记数据。
不包含业务逻辑——读取后的数据处理由调用方（manager/）负责。
"""

from __future__ import annotations

from pathlib import Path

from chestnut_studio.core.model.note import Note


def write_notes_text(notes: list[Note], path: str | Path, header: str, id_map: dict[Note, int]) -> None:
    """将笔记写入文本文件

    Args:
        notes: 笔记列表
        path: 输出文件路径
        header: 文件头内容（含换行符）
        id_map: 笔记 → 序号映射
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for n in notes:
            f.write(n.to_line(id_map.get(n, 0)) + "\n")


def read_notes_text(path: str | Path) -> list[Note]:
    """从文本文件读取笔记

    Returns:
        解析成功的笔记列表（不保证排序）
    """
    notes: list[Note] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            note = Note.from_line(line)
            if note:
                notes.append(note)
    return notes
