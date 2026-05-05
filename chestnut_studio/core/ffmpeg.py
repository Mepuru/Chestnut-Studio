"""FFmpeg 封装"""

import subprocess
from dataclasses import dataclass


@dataclass
class VideoInfo:
    """视频信息"""

    duration: int = 0  # 时长 (ms)
    width: int = 0
    height: int = 0
    fps: float = 0.0
    bitrate: int = 0  # kbps


class FFmpegError(Exception):
    """FFmpeg 相关错误"""


class FFmpeg:
    """FFmpeg 封装"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self._path = ffmpeg_path

    def get_video_info(self, video_path: str) -> VideoInfo:
        """解析视频信息"""
        cmd = [self._path, "-i", video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stderr

        info = VideoInfo()
        for line in output.split("\n"):
            if "Duration" in line:
                info.duration = self._parse_duration(line)
            if "Stream" in line and "Video" in line:
                w, h, fps = self._parse_video_stream(line)
                info.width, info.height, info.fps = w, h, fps

        return info

    def extract_audio(self, video_path: str, output_path: str, sample_rate: int = 1000) -> bool:
        """提取音轨并降采样"""
        cmd = [self._path, "-y", "-i", video_path, "-vn", "-ar", str(sample_rate), output_path]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def _parse_duration(self, line: str) -> int:
        """解析时长行，返回毫秒"""
        try:
            time_str = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = time_str.split(":")
            if "." in s:
                s, ms = s.split(".")
                ms = ms[:3]
            else:
                ms = "0"
            return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
        except Exception:
            return 0

    def _parse_video_stream(self, line: str) -> tuple[int, int, float]:
        """解析视频流信息行"""
        width, height, fps = 0, 0, 0.0
        try:
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if "x" in part and part[0].isdigit():
                    w, h = part.split("x")[:2]
                    width, height = int(w), int(h.split()[0])
                if "fps" in part:
                    fps = float(part.split("fps")[0].strip())
        except Exception:
            pass
        return width, height, fps
