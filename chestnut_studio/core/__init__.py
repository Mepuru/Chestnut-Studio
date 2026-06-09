"""核心逻辑模块 - 无 UI 依赖

分层结构:
  model/     — 纯数据类（Note, Term, AssDialogue, MergePlan, VideoInfo）
  compute/   — 纯计算函数（note_processor, ass_merge_engine）
  io/        — 文件/网络 I/O（note_repository, term_repository, ass_repository, ass_writer）

各模块职责:
  note_manager.py  — NoteManager 编排器（CRUD + 导入导出编排）
  ass_merge.py     — build_merge_plan 编排（解析 + 委托 compute）
  ffmpeg.py        — FFmpeg 子进程封装
   model/config.py  — 轨道颜色/数量配置（单源，track_config.py 已废弃）
"""

from chestnut_studio.core.ffmpeg import FFmpeg
from chestnut_studio.core.io.ass_repository import read_ass, read_txt_notes
from chestnut_studio.core.manager.ass_merge import build_merge_plan
from chestnut_studio.core.manager.note_manager import NoteManager
from chestnut_studio.core.model.ass_merge import AssDialogue, MergePlan, TxtNote, UncertainMatch
from chestnut_studio.core.model.config import (
    DEFAULT_TRACK_COUNT,
    MAX_TRACK_COUNT,
    NOTE_TYPES,
    TRACK_COLORS_HEX,
    get_track_bg_color_hex,
    get_track_color,
)
from chestnut_studio.core.model.ffmpeg import FFmpegError, VideoInfo
from chestnut_studio.core.model.note import Note, Term

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
    "read_ass",
    "read_txt_notes",
]
