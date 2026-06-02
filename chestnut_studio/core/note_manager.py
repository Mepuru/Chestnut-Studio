"""笔记数据模型模块

核心数据模型，无 UI 依赖。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from chestnut_studio.core.track_config import NOTE_TYPES
from chestnut_studio.utils.time_utils import ms_to_time_str

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
# 批量删除前缀: 用正则替换  ^.+?\\d{{2}}:\\d{{2}}\\.\\d{{2}}\t\\|  为空
# ---"""


@dataclass
class Note:
    """单条笔记"""

    def __lt__(self, other):
        return self.timestamp_ms < other.timestamp_ms

    timestamp_ms: int = 0
    text: str = ""
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

    def to_line(self, note_id: int = 0) -> str:
        """转导出文本行: #id 轨道名  时间	| 内容"""
        if note_id:
            return f"#{note_id}	{self.type}	{ms_to_time_str(self.timestamp_ms)}	| {self.text}"
        return f"{self.type}	{ms_to_time_str(self.timestamp_ms)}	| {self.text}"

    @classmethod
    def from_line(cls, line: str) -> Note | None:
        """从文本行解析 Note，解析失败返回 None"""
        line = line.strip()
        if not line:
            return None
        # 跳过注释行（# 开头且第二位不是数字的）
        if line.startswith("#") and (len(line) < 2 or not line[1].isdigit()):
            return None
        try:
            # 格式: [#id ]轨道名  时间	| 内容
            rest = line
            # 跳过可选的 #id 前缀
            if rest[0] == "#":
                sep = rest.find(chr(9))
                if sep > 1 and rest[1:sep].isdigit():
                    rest = rest[sep + 1 :]

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
            return cls(timestamp_ms=ms, text=text, type=track_name)
        except (ValueError, IndexError, KeyError):
            return None


@dataclass
class Term:
    """术语条目"""

    source: str  # 原文（日语）
    translation: str  # 译文（中文）
    origin: str = ""  # 出处
    note: str = ""  # 备注

    def to_line(self) -> str:
        """转导出块格式"""
        lines = ["# ---"]
        lines.append(f"# 词: {self.source}")
        lines.append(f"# 译: {self.translation}")
        if self.origin:
            lines.append(f"# 出: {self.origin}")
        if self.note:
            for n_line in self.note.split("\n"):
                lines.append(f"# {n_line}")
        return "\n".join(lines)

    @classmethod
    def from_block(cls, block: str) -> Term | None:
        """从块格式解析 Term（跨多行）"""
        lines = [ln.strip() for ln in block.strip().split("\n")]
        source = ""
        translation = ""
        origin = ""
        note_lines = []
        for line in lines:
            if line.startswith("# 词: "):
                source = line[5:]
            elif line.startswith("# 译: "):
                translation = line[5:]
            elif line.startswith("# 出: "):
                origin = line[5:]
            elif (
                line.startswith("# ")
                and not line.startswith("# ---")
                and not line.startswith("# 词:")
                and not line.startswith("# 译:")
                and not line.startswith("# 出:")
            ):
                note_lines.append(line[2:])
        if source and translation:
            return cls(source=source, translation=translation, origin=origin, note="\n".join(note_lines))
        return None

    @classmethod
    def from_line(cls, line: str) -> Term | None:
        """保留旧版单行解析兼容"""
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
        except (ValueError, IndexError):
            return None


class NoteManager:
    """笔记管理器"""

    def __init__(self):
        self._notes: list[Note] = []
        self._terms: list[Term] = []

    # ── 增 ──

    def add(self, timestamp_ms: int, text: str, note_type: str = "轨道1") -> Note:
        note = Note(timestamp_ms=timestamp_ms, text=text, type=note_type)
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

    def export_text(
        self,
        path: str | Path,
        types: list[str] | None = None,
        video_name: str = "",
        video_duration: str = "",
        video_resolution: str = "",
        video_fps: str = "",
        video_bitrate: str = "",
    ) -> int:
        notes = self._notes if types is None else [n for n in self._notes if n.type in types]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                EXPORT_HEADER.format(
                    video=video_name,
                    duration=video_duration,
                    resolution=video_resolution,
                    fps=video_fps,
                    bitrate=video_bitrate,
                    time=now,
                    terms=len(self._terms),
                )
                + "\n"
            )
            id_map = self.assign_ids()
            for n in notes:
                f.write(n.to_line(id_map.get(id(n), 0)) + "\n")
        return len(notes)

    def assign_ids(self) -> dict[int, int]:
        """按时间排序分配序号，返回 {序号: position} 映射"""
        self._notes.sort(key=lambda n: n.timestamp_ms)
        id_map = {}
        for i, note in enumerate(self._notes, 1):
            id_map[id(note)] = i
        return id_map

    def get_note_id(self, note: Note) -> int:
        """获取笔记在当前排序下的序号"""
        self._notes.sort(key=lambda n: n.timestamp_ms)
        for i, n in enumerate(self._notes, 1):
            if n is note:
                return i
        return 0

    def import_text(self, path: str | Path) -> int:
        """从文本文件导入笔记"""
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

    def update_term(self, old_source: str, new_source: str, translation: str, origin: str, note: str) -> bool:
        """更新术语"""
        for i, t in enumerate(self._terms):
            if t.source == old_source:
                self._terms[i] = Term(source=new_source, translation=translation, origin=origin, note=note)
                return True
        return False

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
            f.write("\n" + "# --- 术语 ---" + "\n")
            for term in self._terms:
                f.write(term.to_line() + "\n")
        return len(self._terms)

    def import_terms(self, path: str | Path) -> int:
        """从文件导入术语（区块格式）"""
        count = 0
        in_terms = False
        block = ""
        with open(path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not in_terms:
                    if s == "# --- 术语 ---" or s == "# 术语":
                        in_terms = True
                    continue
                if not s:
                    continue
                if s.startswith("# ---"):
                    if block:
                        t = Term.from_block(block)
                        if t:
                            self._terms.append(t)
                            count += 1
                    block = s + "\n"
                else:
                    block += line
            if block:
                t = Term.from_block(block)
                if t:
                    self._terms.append(t)
                    count += 1
        return count
