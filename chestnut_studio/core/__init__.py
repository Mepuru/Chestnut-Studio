"""核心逻辑模块 - 无 UI 依赖

分层结构:
  model/     — 纯数据类（Note, Term, AssDialogue, MergePlan, VideoInfo）
  compute/   — 纯计算函数（note_processor, ass_merge_engine）
  io/        — 文件/网络 I/O（规划中）

各模块职责:
  note_manager.py  — NoteManager 编排器（CRUD + 导入导出编排）
  ass_merge.py     — ASS+TXT 文件解析 + build_merge_plan 编排
  ffmpeg.py        — FFmpeg 子进程封装
  track_config.py  — 轨道颜色/数量配置（单源）
"""

from chestnut_studio.core.ass_merge import (
    MergePlan,
    build_merge_plan,
    parse_ass,
    parse_txt,
)
from chestnut_studio.core.ffmpeg import FFmpeg
from chestnut_studio.core.model.ass_merge import AssDialogue, TxtNote, UncertainMatch
from chestnut_studio.core.model.ffmpeg import FFmpegError, VideoInfo
from chestnut_studio.core.model.note import Note, Term
from chestnut_studio.core.note_manager import NoteManager
from chestnut_studio.core.track_config import (
    DEFAULT_TRACK_COUNT,
    MAX_TRACK_COUNT,
    NOTE_TYPES,
    TRACK_COLORS_HEX,
    get_track_bg_color_hex,
    get_track_color,
)

__all__ = [
    "FFmpeg",
    "FFmpegError",
    "VideoInfo",
    "Note",
    "Term",
    "NoteManager",
    "NOTE_TYPES",
    "DEFAULT_TRACK_COUNT",
    "MAX_TRACK_COUNT",
    "TRACK_COLORS_HEX",
    "get_track_color",
    "get_track_bg_color_hex",
    "UncertainMatch",
    "MergePlan",
    "AssDialogue",
    "TxtNote",
    "build_merge_plan",
    "parse_ass",
    "parse_txt",
]
