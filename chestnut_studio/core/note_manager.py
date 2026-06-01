"""笔记数据模型模块

核心数据模型，无 UI 依赖。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar

NOTE_TYPES: ClassVar[list[str]] = ["轨道1", "轨道2", "轨道3", "轨道4"]
"""笔记类型列表"""


@dataclass(order=True)
class Note:
    """单条笔记

    Attributes:
        timestamp_ms: 视频时间戳（毫秒）
        text: 笔记内容
        type: 笔记类型（"字幕" 或 "画面"）
    """

    timestamp_ms: int
    text: str
    type: str = "轨道1"

    def __post_init__(self):
        if self.type not in NOTE_TYPES:
            raise ValueError(f"笔记类型必须为 {NOTE_TYPES}，收到: {self.type}")
        if self.timestamp_ms < 0:
            raise ValueError(f"时间戳不能为负值: {self.timestamp_ms}")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Note:
        return cls(
            timestamp_ms=data["timestamp_ms"],
            text=data["text"],
            type=data.get("type", "轨道1"),
        )


class NoteManager:
    """笔记管理器，管理 Note 对象的增删改查和持久化。"""

    def __init__(self):
        self._notes: list[Note] = []

    # ── 增 ──

    def add(self, timestamp_ms: int, text: str, note_type: str = "轨道1") -> Note:
        """添加一条笔记，自动按时间排序

        Args:
            timestamp_ms: 视频时间戳（毫秒）
            text: 笔记文本
            note_type: 笔记类型

        Returns:
            新创建的 Note 对象
        """
        note = Note(timestamp_ms=timestamp_ms, text=text, type=note_type)
        self._notes.append(note)
        self._notes.sort()
        return note

    # ── 删 ──

    def remove(self, note: Note) -> bool:
        """删除指定笔记

        Args:
            note: 要删除的 Note 对象

        Returns:
            是否成功删除
        """
        try:
            self._notes.remove(note)
            return True
        except ValueError:
            return False

    def clear(self):
        """清空所有笔记"""
        self._notes.clear()

    # ── 查 ──

    def get_all(self) -> list[Note]:
        """获取所有笔记（按时间升序）

        Returns:
            排序后的笔记列表
        """
        return list(self._notes)

    def get_by_type(self, note_type: str) -> list[Note]:
        """获取指定类型的所有笔记

        Args:
            note_type: "字幕" 或 "画面"

        Returns:
            过滤后的笔记列表
        """
        return [n for n in self._notes if n.type == note_type]

    def count(self) -> int:
        return len(self._notes)

    # ── 持久化 ──

    def export_json(self, path: str | Path) -> None:
        """导出笔记为 JSON 文件

        Args:
            path: 输出文件路径
        """
        data = {
            "version": 1,
            "notes": [n.to_dict() for n in self._notes],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_json(self, path: str | Path) -> int:
        """从 JSON 文件导入笔记，追加到现有数据

        Args:
            path: JSON 文件路径

        Returns:
            导入的笔记数量
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        notes_data = data.get("notes", [])
        for item in notes_data:
            note = Note.from_dict(item)
            self._notes.append(note)

        self._notes.sort()
        return len(notes_data)
