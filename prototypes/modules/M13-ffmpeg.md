# M13 — FFmpeg 封装

> `chestnut_studio/core/ffmpeg.py`　｜　Phase 1~2　｜　视频解析 + 音轨提取

---

## 职责

- 解析视频信息（时长、分辨率、帧率、码率）
- 提取音轨并降采样（用于波形显示）
- 字幕导出时的视频处理

---

## 类设计

```python
import subprocess
import os

class FFmpeg:
    """FFmpeg 封装"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Args:
            ffmpeg_path: ffmpeg 可执行文件路径，默认从 PATH 中查找
        """
        self._path = ffmpeg_path
    
    def get_video_info(self, video_path: str) -> dict:
        """解析视频信息
        
        Returns:
            {
                'duration': int,      # 时长 (ms)
                'width': int,         # 宽度
                'height': int,        # 高度
                'fps': float,         # 帧率
                'bitrate': int,       # 码率 (kbps)
            }
        """
        cmd = [self._path, '-i', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stderr  # ffmpeg 输出到 stderr
        
        info = {
            'duration': 0,
            'width': 0,
            'height': 0,
            'fps': 0,
            'bitrate': 0,
        }
        
        for line in output.split('\n'):
            if 'Duration' in line:
                info['duration'] = self._parse_duration(line)
            if 'Stream' in line and 'Video' in line:
                info.update(self._parse_video_stream(line))
        
        return info
    
    def extract_audio(self, video_path: str, output_path: str, 
                      sample_rate: int = 1000) -> bool:
        """提取音轨并降采样
        
        Args:
            video_path: 视频文件路径
            output_path: 输出 WAV 路径
            sample_rate: 采样率 (Hz)，默认 1000
            
        Returns:
            是否成功
        """
        cmd = [
            self._path, '-y',
            '-i', video_path,
            '-vn',                    # 无视频
            '-ar', str(sample_rate),  # 采样率
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    
    def extract_audio_copy(self, video_path: str, output_path: str) -> bool:
        """提取原始音轨（不转码）
        
        Args:
            video_path: 视频文件路径
            output_path: 输出 AAC 路径
            
        Returns:
            是否成功
        """
        cmd = [
            self._path, '-y',
            '-i', video_path,
            '-vn',
            '-c', 'copy',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    
    def _parse_duration(self, line: str) -> int:
        """解析时长行，返回毫秒"""
        # Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s
        try:
            time_str = line.split('Duration:')[1].split(',')[0].strip()
            h, m, s = time_str.split(':')
            if '.' in s:
                s, ms = s.split('.')
                ms = ms[:3]  # 只取3位
            else:
                ms = '0'
            return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
        except:
            return 0
    
    def _parse_video_stream(self, line: str) -> dict:
        """解析视频流信息行"""
        info = {}
        try:
            # Stream #0:0: Video: h264, yuv420p, 1920x1080, 60 fps, ...
            parts = line.split(',')
            for part in parts:
                part = part.strip()
                if 'x' in part and part[0].isdigit():
                    w, h = part.split('x')[:2]
                    info['width'] = int(w)
                    info['height'] = int(h)
                if 'fps' in part:
                    info['fps'] = float(part.split('fps')[0].strip())
        except:
            pass
        return info
```

---

## FFmpeg 输出解析示例

```
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'input.mp4':
  Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s
  Stream #0:0(und): Video: h264 (High) (avc1 / 0x31637661), yuv420p, 1920x1080, 1800 kb/s, 60 fps, 60 tbr, 16k tbn, 120 tbc
  Stream #0:1(und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 192 kb/s
```

---

## 方法列表

| 方法 | 说明 | 用途 |
|------|------|------|
| `get_video_info()` | 解析视频信息 | 打开视频时 |
| `extract_audio()` | 提取+降采样音轨 | 波形显示 |
| `extract_audio_copy()` | 提取原始音轨 | AI打轴（预留） |

---

## 错误处理

```python
class FFmpegError(Exception):
    """FFmpeg 相关错误"""
    pass

class FFmpegNotFoundError(FFmpegError):
    """FFmpeg 未找到"""
    pass

class VideoParseError(FFmpegError):
    """视频解析失败"""
    pass
```

---

## 测试用例

```python
class TestFFmpeg:
    def test_parse_duration(self):
        ffmpeg = FFmpeg()
        line = "Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s"
        assert ffmpeg._parse_duration(line) == 330120
    
    def test_parse_video_stream(self):
        ffmpeg = FFmpeg()
        line = "Stream #0:0: Video: h264, yuv420p, 1920x1080, 60 fps"
        info = ffmpeg._parse_video_stream(line)
        assert info['width'] == 1920
        assert info['height'] == 1080
        assert info['fps'] == 60.0
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| subprocess (标准库) | 调用 FFmpeg |
| FFmpeg | 外部可执行文件 |
