"""FFmpeg 封装

数据模型（VideoInfo, FFmpegError）定义位于 core/model/ffmpeg.py。
"""

import re
import subprocess
import sys

from chestnut_studio.core.model.ffmpeg import VideoInfo
from chestnut_studio.utils import get_logger

# Windows 下隐藏控制台窗口的标志
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


class FFmpeg:
    """FFmpeg 封装

    功能：
    - 解析视频信息（时长、分辨率、帧率、码率）
    - 提取音轨并降采样（用于波形显示）
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """初始化 FFmpeg

        Args:
            ffmpeg_path: ffmpeg 可执行文件路径，默认从 PATH 中查找
        """
        self._path = ffmpeg_path
        self._logger = get_logger("FFmpeg")

    def get_video_info(self, video_path: str) -> VideoInfo:
        """解析视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            VideoInfo 数据对象
        """
        cmd = [self._path, "-i", video_path]
        self._logger.debug(f"解析视频: {video_path}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW
        )
        output = result.stderr

        info = VideoInfo()
        found_main_video = False
        for line in output.split("\n"):
            if "Duration" in line:
                info.duration = self._parse_duration(line)
                info.bitrate = self._parse_bitrate(line)
            if "Stream" in line and "Video" in line and not found_main_video:
                # 跳过 attached pic 流（封面图），只取第一个真正的视频流
                if "attached pic" in line:
                    continue
                w, h, fps = self._parse_video_stream(line)
                info.width, info.height, info.fps = w, h, fps
                found_main_video = True

        self._logger.info(f"视频: {info.width}x{info.height}, {info.fps:.0f}fps, {info.duration}ms")
        return info

    def extract_audio(self, video_path: str, output_path: str, sample_rate: int = 1000) -> bool:
        """提取音轨并降采样

        Args:
            video_path: 视频文件路径
            output_path: 输出 WAV 路径
            sample_rate: 采样率 (Hz)，默认 1000

        Returns:
            是否成功
        """
        cmd = [self._path, "-y", "-i", video_path, "-vn", "-ar", str(sample_rate), output_path]
        self._logger.debug(f"提取音频: {video_path} → {output_path}, {sample_rate}Hz")
        result = subprocess.run(
            cmd, capture_output=True, encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW
        )
        ok = result.returncode == 0
        if ok:
            self._logger.info(f"音频提取完成: {output_path}")
        else:
            self._logger.warning(f"音频提取失败: {result.stderr[:200]}")
        return ok

    def _parse_duration(self, line: str) -> int:
        """解析时长行，返回毫秒

        示例输入: "  Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s"
        """
        try:
            time_str = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = time_str.split(":")
            if "." in s:
                s, ms = s.split(".")
                ms = ms[:3].ljust(3, "0")  # 补齐到3位：.12 → 120
            else:
                ms = "0"
            return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
        except (ValueError, IndexError):
            return 0

    def _parse_bitrate(self, line: str) -> int:
        """解析码率，返回 kbps

        示例输入: "  Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s"
        """
        try:
            if "bitrate:" in line:
                bitrate_str = line.split("bitrate:")[1].strip()
                # 提取数字部分
                num_str = ""
                for ch in bitrate_str:
                    if ch.isdigit():
                        num_str += ch
                    elif num_str:
                        break
                if num_str:
                    return int(num_str)
        except (ValueError, IndexError):
            pass
        return 0

    def _parse_video_stream(self, line: str) -> tuple[int, int, float]:
        """解析视频流信息行

        示例输入: "  Stream #0:0: Video: h264, yuv420p, 1920x1080, 60 fps, ..."
        """
        width, height, fps = 0, 0, 0.0
        try:
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if "x" in part and part[0].isdigit():
                    w, h = part.split("x")[:2]
                    width, height = int(w), int(h.split()[0])
                m = re.search(r"([\d.]+)\s*fps", part)
                if m:
                    fps = float(m.group(1))
        except (ValueError, IndexError):
            pass
        return width, height, fps
