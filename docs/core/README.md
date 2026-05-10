# 核心层模块

> `chestnut_studio/core/` 下各模块的接口、用法和设计说明。
> 核心层不依赖 PySide6，可独立测试。

---

## 模块概览

| 模块 | 文件 | 职责 |
|------|------|------|
| [FFmpeg 封装](ffmpeg.md) | `ffmpeg.py` | 视频信息解析、音轨提取 |
| [音频处理](audio.md) | `audio.py` | 波形加载、包络计算、人声增强 |
| [字幕数据结构](subtitle.md) | `subtitle.py` | SubtitleEntry 定义、字幕操作、叠轴检测 |
| [字幕导入导出](subtitle_io.md) | `subtitle_io.py` | SRT/ASS/VTT/LRC 格式支持 |
| [轨道配置](track_config.md) | `track_config.py` | 轨道颜色、数量等集中配置 |

---

## 依赖关系

```
UI 层 (ui/)
  ↓ 调用
核心层 (core/)  ← 本模块
  ↓ 调用
工具层 (utils/)
```

- **核心层**只依赖工具层，不依赖 PySide6
- **UI 层**通过导入核心层模块使用其功能
- **核心层**可独立测试，无需 UI 环境

---

## 设计原则

### 1. 纯逻辑，无 UI 依赖

核心层模块不包含任何 PySide6 相关代码，确保：
- 可独立测试
- 可复用于其他 UI 框架
- 逻辑清晰，职责单一

### 2. 数据驱动

核心层定义数据结构和操作，UI 层负责展示：
- `SubtitleDict` 定义字幕数据格式
- `SubtitleManager` 提供字幕操作接口
- `SubtitleIO` 处理文件导入导出

### 3. 函数式设计

工具函数采用纯函数设计：
- 无状态，无副作用
- 输入输出明确
- 易于测试和复用

---

## 使用示例

```python
from chestnut_studio.core.ffmpeg import FFmpeg
from chestnut_studio.core.audio import load_waveform
from chestnut_studio.core.subtitle import SubtitleManager
from chestnut_studio.core.subtitle_io import SubtitleIO
from chestnut_studio.core.track_config import get_track_color, get_effective_track_count

# FFmpeg 视频信息解析
ffmpeg = FFmpeg()
info = ffmpeg.get_video_info("video.mp4")
print(f"{info.width}x{info.height}, {info.fps}fps")

# 音频波形加载
times, amps = load_waveform("output.wav", vocal_enhance=True)

# 字幕操作
mgr = SubtitleManager()
mgr.set(1, 1000, 2000, "你好")
text = mgr.get(1, 1000)  # [2000, "你好"]

# 字幕导入导出
subs = SubtitleIO.import_srt("subtitle.srt")
SubtitleIO.export_srt("output.srt", subs, video_start=0, sub_start=0)

# 轨道配置
color = get_track_color(1)  # "#3b82f6"
max_track = get_effective_track_count(mgr.get_max_track())
```

---

## 测试要求

| 模块 | 测试要求 |
|------|---------|
| `subtitle.py` | 必须有完整测试（数据结构核心） |
| `subtitle_io.py` | 必须有完整测试（各格式导入导出） |
| `ffmpeg.py` | 至少有集成测试 |
| `audio.py` | 至少有单元测试 |

运行测试：

```bash
uv run pytest tests/test_subtitle.py
```
