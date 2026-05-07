# Chestnut Studio — 核心层模块

> `chestnut_studio/core/` 下各模块的接口、用法和设计说明。
> 核心层不依赖 PySide6，可独立测试。

---

## 一、FFmpeg 封装 (`ffmpeg.py`)

调用系统 FFmpeg 解析视频信息、提取音轨。

### 数据结构

```python
@dataclass
class VideoInfo:
    duration: int = 0   # 时长 (ms)
    width: int = 0      # 宽度 (px)
    height: int = 0     # 高度 (px)
    fps: float = 0.0    # 帧率
    bitrate: int = 0    # 码率 (kbps)
```

### FFmpeg 类

```python
from chestnut_studio.core.ffmpeg import FFmpeg

ffmpeg = FFmpeg()                          # 默认从 PATH 查找
ffmpeg = FFmpeg("C:/tools/ffmpeg.exe")     # 指定路径
```

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_video_info(path)` | 视频文件路径 | `VideoInfo` | 解析时长/分辨率/帧率/码率 |
| `extract_audio(path, output, rate)` | 视频路径、输出WAV路径、采样率 | `bool` | 提取音轨并降采样 |

**用法示例：**

```python
info = ffmpeg.get_video_info("video.mp4")
print(f"{info.width}x{info.height}, {info.fps}fps, {info.duration}ms")

# 提取 1kHz 采样的 WAV（用于波形显示）
ffmpeg.extract_audio("video.mp4", "output.wav", sample_rate=1000)
```

**注意事项：**
- `get_video_info` 解析 FFmpeg 的 stderr 输出，跳过 `attached pic` 流（封面图）
- 使用 `encoding="utf-8", errors="replace"` 处理多字节文件名
- FFmpeg 不可用时 `get_video_info` 返回全零的 `VideoInfo`，不抛异常

### 异常

| 类 | 说明 |
|------|------|
| `FFmpegError` | FFmpeg 相关错误基类 |

---

## 二、字幕数据结构 (`subtitle.py`)

字幕数据的核心结构和操作，包含撤销/重做支持。

### 数据类型

```python
# 字幕字典：列号 → {起始毫秒: [持续毫秒, "文本"]}
SubtitleDict = dict[int, dict[int, list]]

# 示例
{
    1: {1000: [2000, "你好"], 4000: [1500, "世界"]},  # 第1列（原文）
    2: {},   # 第2列（翻译）
    3: {},   # 第3列
    4: {},   # 第4列
}
```

### SubtitleManager 类

```python
from chestnut_studio.core.subtitle import SubtitleManager

mgr = SubtitleManager()
```

**基础操作：**

| 方法 | 参数 | 说明 |
|------|------|------|
| `get(col, start)` | 列号, 起始ms | 返回 `[duration, text]` 或 `None` |
| `set(col, start, duration, text)` | 列号, 起始ms, 持续ms, 文本 | 设置字幕条 |
| `delete(col, start)` | 列号, 起始ms | 删除字幕条 |
| `delete_range(col, start, end)` | 列号, 起始ms, 结束ms | 删除范围内所有字幕条 |
| `merge(col, start, end, text)` | 列号, 起始ms, 结束ms, 文本 | 合并范围内字幕为一条 |
| `split(col, time_point)` | 列号, 时间点 | 在时间点切割字幕条，返回是否成功 |
| `clear(col)` | 列号 | 清空指定列 |
| `clear_all()` | 无 | 清空所有列 |

**叠轴检测：**

```python
result = mgr.check_overlap(col, start, end, interval)
# 返回值：0=有重叠阻止, 1=安全, 2=有重叠但可调整
```

**撤销/重做：**

```python
mgr.push_undo()    # 保存当前状态到撤销栈（操作前调用）
mgr.undo()         # 撤销，返回是否成功
mgr.redo()         # 重做，返回是否成功
```

- 撤销栈最多 100 步（`MAX_UNDO = 100`）
- 使用 `copy.deepcopy` 隔离状态

---

## 三、字幕导入/导出 (`subtitle_io.py`)

支持 SRT 格式的导入导出（Phase 4 扩展 ASS/VTT/LRC）。

### SubtitleIO 类

所有方法都是 `@staticmethod`，无需实例化。

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `import_srt(path)` | SRT 文件路径 | `dict[int, list]` | 导入为 `{start: [duration, text]}` |
| `export_srt(path, data, video_start, sub_start)` | 输出路径, 字幕数据, 视频起始ms, 字幕偏移ms | `None` | 导出 SRT 文件 |

**用法示例：**

```python
from chestnut_studio.core.subtitle_io import SubtitleIO

# 导入
subs = SubtitleIO.import_srt("subtitle.srt")
# {1000: [2000, "你好"], 4000: [1500, "世界"]}

# 导出
SubtitleIO.export_srt("output.srt", subs, video_start=0, sub_start=0)
```

**时间格式辅助函数：**

| 函数 | 说明 | 示例 |
|------|------|------|
| `ms_to_srt_time(ms)` | 毫秒 → SRT 格式 | `3723000 → "1:02:03,000"` |
| `srt_time_to_ms(t)` | SRT 格式 → 毫秒 | `"1:02:03,000" → 3723000` |

---

## 四、音频处理 (`audio.py`)

加载 WAV 文件并提供波形数据，用于波形图显示（Phase 2）。

### 函数

| 函数 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `load_waveform(wav_path, vocal_enhance)` | WAV 文件路径, 是否启用人声增强 | `(time_list, amplitude_list)` | 加载波形数据 |
| `smooth_waveform(amplitude, window)` | 振幅列表, 窗口大小 | `list[float]` | 平滑波形曲线 |
| `compute_envelope(amplitude, window)` | 振幅列表, 窗口大小 | `(upper, lower)` | 计算音频包络线 |
| `compute_envelope_fast(amplitude, window, target_points)` | 振幅列表, 窗口大小, 目标点数 | `(upper, lower)` | 快速计算包络线（下采样） |
| `downsample_waveform(times, amplitudes, target_points)` | 时间列表, 振幅列表, 目标点数 | `(times, amps)` | 下采样波形数据 |

**用法示例：**

```python
from chestnut_studio.core.audio import (
    load_waveform,
    smooth_waveform,
    compute_envelope,
    compute_envelope_fast,
    downsample_waveform,
)

# 加载波形（配合 FFmpeg extract_audio 使用）
times, amps = load_waveform("output.wav")
# times: [0.0, 1.0, 2.0, ...] (ms)
# amps: [123, -456, 789, ...] (int16 振幅)

# 加载波形并启用人声增强（立体声提取中心声道，单声道高通滤波）
times, amps = load_waveform("output.wav", vocal_enhance=True)

# 平滑处理
smoothed = smooth_waveform(amps, window=10)

# 计算包络线（用于波形可视化）
upper, lower = compute_envelope(amps, window=50)
# upper: [0.0, 123.5, 456.2, ...] (上包络，正值)
# lower: [0.0, -123.5, -456.2, ...] (下包络，负值)

# 快速计算包络线（适用于长音频，自动下采样到 5000 点）
upper, lower = compute_envelope_fast(amps, window=50, target_points=5000)

# 下采样波形（保留峰值特征，减少数据点）
ds_times, ds_amps = downsample_waveform(times, amps, target_points=5000)
```

**数据格式：**
- `time_list`: 毫秒时间轴，与采样率对应（1kHz → 每 1ms 一个点）
- `amplitude_list`: int16 振幅值，取第一个声道
- `smooth_waveform`: 使用滑动平均窗口平滑，默认窗口大小 10
- `compute_envelope`: 计算音频包络线，返回上下两条包络曲线
  - 使用滑动窗口最大值 + 峰值保持算法
  - 窗口大小 50 约对应 50ms（采样率 1kHz 时）
  - 适合用于波形可视化，能清晰显示音频能量变化
- `compute_envelope_fast`: 快速版本，先下采样再计算，适用于长音频
- `downsample_waveform`: 保留峰值特征的同时减少数据点，提升绘图性能

**人声增强算法：**
- 立体声：提取中心声道 `(L+R)/2`，减去两侧声道 `(L-R)/2 * 0.5`
- 单声道：高通滤波去除低于 200Hz 的低频噪音
