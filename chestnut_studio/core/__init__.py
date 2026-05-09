"""核心逻辑模块 - 无 UI 依赖"""

from chestnut_studio.core.audio import load_waveform, smooth_waveform
from chestnut_studio.core.ffmpeg import FFmpeg, FFmpegError, VideoInfo
from chestnut_studio.core.subtitle import SubtitleDict, SubtitleManager
from chestnut_studio.core.subtitle_io import SubtitleIO
from chestnut_studio.core.track_config import (
    DEFAULT_TRACK_COUNT,
    MAX_TRACK_COUNT,
    TRACK_COLORS_HEX,
    get_effective_track_count,
    get_track_bg_color_hex,
    get_track_color,
)

__all__ = [
    "FFmpeg",
    "FFmpegError",
    "VideoInfo",
    "SubtitleIO",
    "SubtitleManager",
    "SubtitleDict",
    "load_waveform",
    "smooth_waveform",
    "DEFAULT_TRACK_COUNT",
    "MAX_TRACK_COUNT",
    "TRACK_COLORS_HEX",
    "get_track_color",
    "get_track_bg_color_hex",
    "get_effective_track_count",
]
