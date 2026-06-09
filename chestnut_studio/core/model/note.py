"""笔记与术语数据模型

纯数据类定义 + 文本格式序列化/反序列化方法。
无业务逻辑、无 PySide6 依赖、不引用 core/ 下其他模块。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# 时间格式: MM:SS.mm（厘秒精度，2位小数）
_TIME_FMT = "{m:02d}:{s:02d}.{cs:02d}"


def _ms_to_time_str(ms: int) -> str:
    """毫秒 → MM:SS.mm（内联实现，不依赖 utils/time_utils）"""
    m, r = divmod(ms, 60000)
    s, cs = divmod(r, 1000)
    return _TIME_FMT.format(m=m, s=s, cs=cs // 10)


def _parse_time_str(t: str) -> int:
    """MM:SS.mm 或 MM:SS.mmm → 毫秒（内联实现）"""
    m, r = t.split(":", 1)
    s, cs = r.split(".")
    cs = cs.ljust(3, "0")[:3]
    return int(m) * 60000 + int(s) * 1000 + int(cs)


@dataclass
class Note:
    """单条笔记"""

    def __lt__(self, other: Note) -> bool:
        return (self.timestamp_ms, self.text, self.type) < (
            other.timestamp_ms,
            other.text,
            other.type,
        )

    def __hash__(self) -> int:
        return hash((self.timestamp_ms, self.text, self.type))

    timestamp_ms: int = 0
    text: str = ""
    type: str = "轨道1"  # 默认值，不依赖外部常量

    def __post_init__(self):
        if self.timestamp_ms < 0:
            raise ValueError(f"时间戳不能为负值: {self.timestamp_ms}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Note:
        return cls(
            timestamp_ms=data["timestamp_ms"],
            text=data["text"],
            type=data.get("type", "轨道1"),
        )

    def to_line(self, note_id: int = 0) -> str:
        """转导出文本行: [#id ]轨道名  时间	| 内容"""
        time_str = _ms_to_time_str(self.timestamp_ms)
        if note_id:
            return f"#{note_id}	{self.type}	{time_str}	| {self.text}"
        return f"{self.type}	{time_str}	| {self.text}"

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
            ms = _parse_time_str(time_str)
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
