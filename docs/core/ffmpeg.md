# FFmpeg 封装

> `chestnut_studio/core/ffmpeg.py`
> 调用系统 FFmpeg 解析视频信息、提取音轨。

---

## 职责

- 解析视频文件信息（时长、分辨率、帧率、码率）
- 提取音轨并降采样为 WAV 格式
- 处理 FFmpeg 命令行调用和错误处理

---

## 数据结构

### VideoInfo

```python
@dataclass
class VideoInfo:
    duration: int = 0   # 时长 (ms)
    width: int = 0      # 宽度 (px)
    height: int = 0     # 高度 (px)
    fps: float = 0.0    # 帧率
    bitrate: int = 0    # 码率 (kbps)
```

---

## FFmpeg 类

### 初始化

```python
from chestnut_studio.core.ffmpeg import FFmpeg

# 默认从 PATH 查找
ffmpeg = FFmpeg()

# 指定路径
ffmpeg = FFmpeg("C:/tools/ffmpeg.exe")
```

### 公有方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_video_info(path)` | 视频文件路径 | `VideoInfo` | 解析时长/分辨率/帧率/码率 |
| `extract_audio(path, output, rate)` | 视频路径、输出WAV路径、采样率 | `bool` | 提取音轨并降采样 |

---

## 用法示例

```python
from chestnut_studio.core.ffmpeg import FFmpeg

ffmpeg = FFmpeg()

# 解析视频信息
info = ffmpeg.get_video_info("video.mp4")
print(f"{info.width}x{info.height}, {info.fps}fps, {info.duration}ms")

# 提取 1kHz 采样的 WAV（用于波形显示）
success = ffmpeg.extract_audio("video.mp4", "output.wav", sample_rate=1000)
if success:
    print("音轨提取成功")
```

---

## 注意事项

### 视频信息解析

- `get_video_info` 解析 FFmpeg 的 stderr 输出
- 跳过 `attached pic` 流（封面图）
- 使用 `encoding="utf-8", errors="replace"` 处理多字节文件名

### 错误处理

- FFmpeg 不可用时 `get_video_info` 返回全零的 `VideoInfo`，不抛异常
- `extract_audio` 失败时返回 `False`

### 性能考虑

- `get_video_info` 会启动 FFmpeg 进程，有一定开销
- 建议缓存结果，避免重复调用

---

## 异常

| 类 | 说明 |
|------|------|
| `FFmpegError` | FFmpeg 相关错误基类 |

---

## 依赖

- 系统 FFmpeg（需要加入 PATH，详见 [FFmpeg 安装指南](../ffmpeg-setup.md)）
- Python 标准库：`subprocess`, `dataclasses`
