"""FFmpeg 相关数据模型

纯数据类定义，无 I/O、无业务逻辑、无 PySide6 依赖。
"""

from dataclasses import dataclass


@dataclass
class VideoInfo:
    """视频信息"""

    duration: int = 0  # 时长 (ms)
    width: int = 0  # 宽度
    height: int = 0  # 高度
    fps: float = 0.0  # 帧率
    bitrate: int = 0  # 码率 (kbps)


class FFmpegError(Exception):
    """FFmpeg 相关错误"""
