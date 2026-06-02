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

NOTE_TYPES: ClassVar[list[str]] = [f"轨道{i}" for i in range(1, 10)] + ["轨道10"]
"""笔记类型列表"""

# 导出文本格式说明（文件头）
EXPORT_HEADER = """# Chestnut Studio Notes
# 术语数: {terms}
# 视频: {video}
# 时长: {duration}
# 分辨率: {resolution}
# 帧率: {fps}
# 码率: {bitrate}
# 导出时间: {time}
# 格式: 轨道名  时间	| 内容
# 批量删除前缀: 用正则替换  ^.+?\d{{2}}:\d{{2}}\.\d{{2}}\t\|  为空
# ---"""


@dataclass
class Note:
    """单条笔记"""

    def __lt__(self, other):
        return self.timestamp_ms < other.timestamp_ms

    timestamp_ms: int = 0
    text: str = ""
    type: str = "轨道1"
    id: int = 0  # 序号（由 NoteManager 自动分配）

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

    def to_line(self, parts: tuple[str, ...] = ("track", "time", "text")) -> str:
        """转导出文本行

        Args:
            parts: 控制包含哪些字段
                "track" — 轨道名
                "time"  — 时间
                "text"  — 内容

        Returns:
            如 parts=("time","text") → "00:15.20\t| 你好"
        """
        cols = []
        for p in parts:
            if p == "track":
                cols.append(self.type)
            elif p == "time":
                cols.append(ms_to_time_str(self.timestamp_ms))
        prefix = "\t".join(cols)
        if "text" in parts:
            return f"{prefix}\t| {self.text}" if prefix else self.text
        return prefix

    @classmethod
    def from_line(cls, line: str) -> Note | None:
        """从文本行解析 Note，解析失败返回 None"""
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        # 跳过注释行（只有 # 开头且第二位不是数字的才是注释）
        if len(line) > 1 and line[0] == "#" and not line[1].isdigit():
            return None
        try:
            # 格式: #id 轨道名  时间	| 内容
            note_id = 0
            rest = line
            if rest[0] == "#":
                space_pos = rest.find(" ")
                if space_pos > 1 and rest[1:space_pos].isdigit():
                    note_id = int(rest[1:space_pos])
                    rest = rest[space_pos+1:]
            
            parts = rest.split("	| ", 1)
            if len(parts) != 2:
                return None
            meta, text = parts
            meta_parts = meta.rsplit("	", 1)
            if len(meta_parts) != 2:
                return None
            track_name, time_str = meta_parts
            if track_name not in NOTE_TYPES:
                return None
            m, r = time_str.split(":", 1)
            s, cs = r.split(".")
            ms = int(m) * 60000 + int(s) * 1000 + int(cs) * 10
            return cls(id=note_id, timestamp_ms=ms, text=text, type=track_name)
        except Exception:
            return None

@dataclass
class Term:
    """术语条目"""
    source: str      # 原文（日语）
    translation: str # 译文（中文）
    origin: str = "" # 出处
    note: str = ""   # 备注

    def to_line(self) -> str:
        """转导出文本行"""
        parts = [self.source, self.translation]
        if self.origin:
            parts.append(self.origin)
        if self.note:
            parts.append(self.note)
        return " | ".join(parts)

    @classmethod
    def from_line(cls, line: str) -> Term | None:
        """从文本行解析 Term"""
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        try:
            parts = [p.strip() for p in line.split(" | ", 3)]
            if len(parts) < 2:
                return None
            term = cls(source=parts[0], translation=parts[1])
            if len(parts) > 2:
                term.origin = parts[2]
            if len(parts) > 3:
                term.note = parts[3]
            return term
        except Exception:
            return None


class NoteManager:
    """笔记管理器"""

    def __init__(self):
        self._notes: list[Note] = []
        self._terms: list[Term] = []
        self._next_id: int = 1

    # ── 增 ──

    def add(self, timestamp_ms: int, text: str, note_type: str = "轨道1") -> Note:
        note = Note(id=self._next_id, timestamp_ms=timestamp_ms, text=text, type=note_type)
        self._next_id += 1
        self._notes.append(note)
        self._notes.sort(key=lambda n: n.timestamp_ms)
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

    def export_text(self, path: str | Path, types: list[str] | None = None,
                    video_name: str = "", video_duration: str = "",
                    video_resolution: str = "", video_fps: str = "",
                    video_bitrate: str = "") -> int:
        notes = self._notes if types is None else [n for n in self._notes if n.type in types]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(path, "w", encoding="utf-8") as f:
            f.write(EXPORT_HEADER.format(video=video_name, duration=video_duration,
                                            resolution=video_resolution, fps=video_fps,
                                            bitrate=video_bitrate, time=now, terms=len(self._terms)) + chr(10))
            for n in notes:
                f.write(n.to_line() + chr(10))
        return len(notes)


    def import_text(self, path: str | Path) -> int:
        """从文本文件导入笔记
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

    # ── 术语库 ──

    def add_term(self, source: str, translation: str, origin: str = "", note: str = "") -> Term:
        """添加术语"""
        term = Term(source=source, translation=translation, origin=origin, note=note)
        # 如果 source 已存在则替换
        for i, t in enumerate(self._terms):
            if t.source == source:
                self._terms[i] = term
                return term
        self._terms.append(term)
        return term

    def get_terms(self) -> list[Term]:
        return list(self._terms)

    def remove_term(self, source: str) -> bool:
        for i, t in enumerate(self._terms):
            if t.source == source:
                self._terms.pop(i)
                return True
        return False

    def clear_terms(self):
        self._terms.clear()

    def term_count(self) -> int:
        return len(self._terms)

    def export_terms(self, path: str | Path) -> int:
        """导出术语库到文件末尾"""
        with open(path, "a", encoding="utf-8") as f:
            f.write(chr(10) + "# --- 术语 ---" + chr(10))
            for term in self._terms:
                f.write(term.to_line() + chr(10))
        return len(self._terms)

    def import_terms(self, path: str | Path) -> int:
        """从文件导入术语"""
        count = 0
        in_terms = False
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line == "# --- 术语 ---" or line == "# 术语库" or line.startswith("# 术语"):
                    in_terms = True
                    continue
                if in_terms:
                    if line.startswith("# ---") or line.startswith("# "):
                        continue
                    term = Term.from_line(line)
                    if term:
                        self._terms.append(term)
                        count += 1
        return count
