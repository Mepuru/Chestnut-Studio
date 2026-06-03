"""核心逻辑模块 - 无 UI 依赖"""

from chestnut_studio.core.ffmpeg import FFmpeg, FFmpegError, VideoInfo
from chestnut_studio.core.note_manager import Note, NoteManager
from chestnut_studio.core.ass_merge import (
    MergeConflict,
    MergePlan,
    build_merge_plan,
    apply_conflict_resolution,
)
from chestnut_studio.core.track_config import (
    DEFAULT_TRACK_COUNT,
    MAX_TRACK_COUNT,
    NOTE_TYPES,
    TRACK_COLORS_HEX,
    get_effective_track_count,
    get_track_bg_color_hex,
    get_track_color,
)

__all__ = [
    "FFmpeg",
    "FFmpegError",
    "VideoInfo",
    "Note",
    "NoteManager",
    "NOTE_TYPES",
    "DEFAULT_TRACK_COUNT",
    "MAX_TRACK_COUNT",
    "TRACK_COLORS_HEX",
    "get_track_color",
    "set_track_color",
    "reset_track_color",
    "get_all_track_colors",
    "get_track_bg_color_hex",
    "get_effective_track_count",
    "save_track_colors",
    "load_track_colors",
    "set_config_path",
    "MergeConflict",
    "MergePlan",
    "build_merge_plan",
    "apply_conflict_resolution",
]
