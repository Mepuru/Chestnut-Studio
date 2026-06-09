"""数据模型模块 — 纯数据类，零外部依赖

本包中的所有模块均为纯数据定义（dataclass），
不包含 I/O、不包含业务逻辑、不依赖 PySide6。

分层规则:
  model/ → 可被 compute/、io/、manager/、ui/ 任意引用
  compute/、io/、manager/ 等不可反向依赖 model/
"""

from chestnut_studio.core.model.ass_merge import (
    AssDialogue,
    MergePlan,
    TxtNote,
    UncertainMatch,
)
from chestnut_studio.core.model.ffmpeg import FFmpegError, VideoInfo
from chestnut_studio.core.model.note import Note, Term
from chestnut_studio.core.model.session import SessionState

__all__ = [
    "Note",
    "Term",
    "SessionState",
    "AssDialogue",
    "TxtNote",
    "UncertainMatch",
    "MergePlan",
    "VideoInfo",
    "FFmpegError",
]
