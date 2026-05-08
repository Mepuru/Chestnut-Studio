# 字幕导入导出

> `chestnut_studio/core/subtitle_io.py`
> 支持 SRT 和 ASS 格式的导入导出。

---

## 职责

- 导入 SRT/ASS 格式字幕文件
- 导出 SRT/ASS 格式字幕文件
- 时间格式转换辅助函数

---

## SubtitleIO 类

所有方法都是 `@staticmethod`，无需实例化。

```python
from chestnut_studio.core.subtitle_io import SubtitleIO
```

---

## 导入方法

### import_srt

导入 SRT 格式字幕文件。

```python
@staticmethod
def import_srt(path: str) -> dict[int, list]:
    """导入 SRT 文件
    
    Args:
        path: SRT 文件路径
        
    Returns:
        {start_ms: [duration_ms, "text"], ...}
    """
```

**用法示例：**

```python
subs = SubtitleIO.import_srt("subtitle.srt")
# {1000: [2000, "你好"], 4000: [1500, "世界"]}
```

### import_ass

导入 ASS 格式字幕文件。

```python
@staticmethod
def import_ass(path: str) -> dict[int, list]:
    """导入 ASS 文件
    
    Args:
        path: ASS 文件路径
        
    Returns:
        {start_ms: [duration_ms, "text"], ...}
    """
```

**用法示例：**

```python
subs = SubtitleIO.import_ass("subtitle.ass")
# {1000: [2000, "你好"], 4000: [1500, "世界"]}
```

---

## 导出方法

### export_srt

导出 SRT 格式字幕文件。

```python
@staticmethod
def export_srt(
    path: str, 
    data: dict[int, list], 
    video_start: int = 0, 
    sub_start: int = 0
) -> None:
    """导出 SRT 文件
    
    Args:
        path: 输出路径
        data: 字幕数据 {start_ms: [duration_ms, "text"]}
        video_start: 视频起始ms（时间偏移）
        sub_start: 字幕偏移ms
    """
```

**用法示例：**

```python
subs = {1000: [2000, "你好"], 4000: [1500, "世界"]}
SubtitleIO.export_srt("output.srt", subs, video_start=0, sub_start=0)
```

### export_ass

导出多轨道 ASS 格式字幕文件。

```python
@staticmethod
def export_ass(
    path: str, 
    tracks: dict[int, dict[int, list]], 
    track_styles: dict[int, str] = None,
    fontname: str = "Arial",
    fontsize: int = 48
) -> None:
    """导出多轨道 ASS 文件
    
    Args:
        path: 输出路径
        tracks: 多轨道数据 {col: {start_ms: [duration_ms, "text"]}}
        track_styles: 轨道样式名 {col: "样式名"}
        fontname: 字体名称
        fontsize: 字体大小
    """
```

**用法示例：**

```python
tracks = {
    1: {1000: [2000, "你好"], 4000: [1500, "世界"]},
    2: {1000: [2000, "こんにちは"], 4000: [1500, "世界"]},
}
track_styles = {1: "轨道 1", 2: "轨道 2"}
SubtitleIO.export_ass("output.ass", tracks, track_styles)
```

**ASS 导出说明：**
- 样式名根据轨道自动命名：`轨道 1`、`轨道 2` 等
- 不同样式自动分配不同颜色（白色、黄色、绿色、蓝色）
- 输出文件使用 UTF-8-BOM 编码

---

## 时间格式辅助函数

### ms_to_srt_time

毫秒转换为 SRT 时间格式。

```python
@staticmethod
def ms_to_srt_time(ms: int) -> str:
    """毫秒 → SRT 格式
    
    Args:
        ms: 毫秒值
        
    Returns:
        SRT 时间字符串，如 "1:02:03,000"
    """
```

**用法示例：**

```python
SubtitleIO.ms_to_srt_time(3723000)  # "1:02:03,000"
```

### srt_time_to_ms

SRT 时间格式转换为毫秒。

```python
@staticmethod
def srt_time_to_ms(t: str) -> int:
    """SRT 格式 → 毫秒
    
    Args:
        t: SRT 时间字符串，如 "1:02:03,000"
        
    Returns:
        毫秒值
    """
```

**用法示例：**

```python
SubtitleIO.srt_time_to_ms("1:02:03,000")  # 3723000
```

---

## 完整用法示例

```python
from chestnut_studio.core.subtitle_io import SubtitleIO

# 导入 SRT
subs = SubtitleIO.import_srt("subtitle.srt")
# {1000: [2000, "你好"], 4000: [1500, "世界"]}

# 导入 ASS
subs = SubtitleIO.import_ass("subtitle.ass")

# 导出 SRT
SubtitleIO.export_srt("output.srt", subs, video_start=0, sub_start=0)

# 导出多轨道 ASS
tracks = {
    1: {1000: [2000, "你好"], 4000: [1500, "世界"]},
    2: {1000: [2000, "こんにちは"], 4000: [1500, "世界"]},
}
track_styles = {1: "轨道 1", 2: "轨道 2"}
SubtitleIO.export_ass("output.ass", tracks, track_styles)
```

---

## 文件格式说明

### SRT 格式

```
1
00:00:01,000 --> 00:00:03,000
你好

2
00:00:04,000 --> 00:00:05,500
世界
```

### ASS 格式

```
[Script Info]
Title: Chestnut Studio Export
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, ...
Style: 轨道 1,Arial,48,&H00FFFFFF,...
Style: 轨道 2,Arial,48,&H0000FFFF,...

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.00,轨道 1,,0,0,0,,你好
Dialogue: 0,0:00:01.00,0:00:03.00,轨道 2,,0,0,0,,こんにちは
```

---

## 注意事项

### 编码处理

- 导入时自动检测编码（UTF-8、GBK 等）
- 导出时使用 UTF-8-BOM 编码

### 时间偏移

- `video_start`：视频起始时间偏移（用于剪辑场景）
- `sub_start`：字幕起始时间偏移

### 多轨道导出

- `tracks` 字典的键是轨道号（1-4）
- `track_styles` 可选，不提供时使用默认样式名
- 每个轨道自动分配不同颜色

---

## 依赖

- Python 标准库：`re`, `codecs`
