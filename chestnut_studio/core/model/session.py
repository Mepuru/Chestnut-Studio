"""会话状态模型 — 自动保存/恢复的数据结构

纯数据类，零外部依赖。
包含笔记、术语、播放器状态、UI 状态等全部需要持久化的字段。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, cast


@dataclass
class SessionState:
    """自动保存和项目文件的完整状态快照"""

    version: str = "1"
    notes: list[dict[str, Any]] | None = None  # __post_init__ 设 []，None 仅用于 pyright strict 兼容
    terms: list[dict[str, Any]] | None = None
    video_path: str = ""
    video_position: int = 0
    volume: int = 80
    playback_rate: float = 1.0
    sort_mode: str = "time"
    current_track: int = 0

    def __post_init__(self) -> None:
        if self.notes is None:
            self.notes = []
        if self.terms is None:
            self.terms = []

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionState:
        return cls(
            version=str(data.get("version", "1")),
            notes=cast("list[dict[str, Any]] | None", data.get("notes")),
            terms=cast("list[dict[str, Any]] | None", data.get("terms")),
            video_path=str(data.get("video_path", "")),
            video_position=int(data.get("video_position", 0)),
            volume=int(data.get("volume", 80)),
            playback_rate=float(data.get("playback_rate", 1.0)),
            sort_mode=str(data.get("sort_mode", "time")),
            current_track=int(data.get("current_track", 0)),
        )
