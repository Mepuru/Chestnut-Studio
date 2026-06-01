"""笔记数据模型模块

核心数据模型，无 UI 依赖。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar

from datetime import datetime

from chestnut_studio.utils.time_utils import ms_to_time_str

NOTE_TYPES: ClassVar[list[str]] = ["轨道1", "轨道2", "轨道3", "轨道4"]
"""笔记类型列表"""

# 导出文本格式说明（文件头）
EXPORT_HEADER = """# Chestnut Studio Notes
# 导出时间: {time}
# 格式: 轨道名  时间\t| 内容
# 批量删除前缀: 用正则替换  ^.+\\d{{2}}:\\d{{2}}\\.\\d{{2}}\\t\\|  为空
# ---"""


@dataclass(order=True)
class Note:
    """单条笔记"""

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

    def to_line(self) -> str:
        """转导出文本行: 轨道名  时间\t| 内容"""
        return f"{self.type}\t{ms_to_time_str(self.timestamp_ms)}\t| {self.text}"

    @classmethod
    def from_line(cls, line: str) -> Note | None:
        """从文本行解析 Note，解析失败返回 None"""
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        try:
            # 格式: 轨道名  时间\t| 内容
            parts = line.split("\t| ", 1)
            if len(parts) != 2:
                return None
            meta, text = parts
            meta_parts = meta.rsplit("\t", 1)
            if len(meta_parts) != 2:
                return None
            track_name, time_str = meta_parts
            if track_name not in NOTE_TYPES:
                return None
            # 解析时间 MM:SS.mm → ms
            m, rest = time_str.split(":", 1)
            s, cs = rest.split(".")
            ms = int(m) * 60000 + int(s) * 1000 + int(cs) * 10
            return cls(timestamp_ms=ms, text=text, type=track_name)
        except Exception:
            return None


class NoteManager:
    """笔记管理器"""

    def __init__(self):
        self._notes: list[Note] = []

    # ── 增 ──

    def add(self, timestamp_ms: int, text: str, note_type: str = "轨道1") -> Note:
        note = Note(timestamp_ms=timestamp_ms, text=text, type=note_type)
        self._notes.append(note)
        self._notes.sort()
        return note

    # ── 删 ──

    def remove(self, note: Note) -> bool:
        try:
            self._notes.remove(note)
            return True
        except ValueError:
            return False

    def clear(self):
        self._notes.clear()

    # ── 查 ──

    def get_all(self) -> list[Note]:
        return list(self._notes)

    def get_by_type(self, note_type: str) -> list[Note]:
        return [n for n in self._notes if n.type == note_type]

    def get_used_types(self) -> list[str]:
        """获取有数据的轨道列表"""
        used = set(n.type for n in self._notes)
        return [t for t in NOTE_TYPES if t in used]

    def count(self) -> int:
        return len(self._notes)

    # ── 文本格式导出/导入 ──

    def export_text(self, path: str | Path, types: list[str] | None = None) -> int:
        """导出指定轨道为文本格式

        Args:
            path: 输出文件路径
            types: 要导出的轨道列表，None 表示全部

        Returns:
            导出的行数
        """
        notes = self._notes if types is None else [n for n in self._notes if n.type in types]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(path, "w", encoding="utf-8") as f:
            f.write(EXPORT_HEADER.format(time=now) + "\n")
            for n in notes:
                f.write(n.to_line() + "\n")
        return len(notes)

    def import_text(self, path: str | Path) -> int:
        """从文本文件导入笔记

        Args:
            path: 文件路径

        Returns:
            导入的笔记数量
        """
        count = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                note = Note.from_line(line)
                if note:
                    self._notes.append(note)
                    count += 1
        self._notes.sort()
        return count

    # ── JSON 格式导出/导入 ──

    def export_json(self, path: str | Path, types: list[str] | None = None) -> int:
        notes = self._notes if types is None else [n for n in self._notes if n.type in types]
        data = {"version": 1, "notes": [n.to_dict() for n in notes]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return len(notes)

    def import_json(self, path: str | Path) -> int:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("notes", []):
            note = Note.from_dict(item)
            self._notes.append(note)
        self._notes.sort()
        return len(data.get("notes", []))
