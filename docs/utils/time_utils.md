# 时间格式转换

> `chestnut_studio/utils/time_utils.py`
> 毫秒与各种字幕时间格式之间的互转。所有函数均为纯函数，无状态。

---

## 职责

- 毫秒转换为各种时间格式字符串
- 时间格式字符串转换为毫秒
- 支持 SRT、ASS、VTT、LRC 等格式

---

## 毫秒 → 字符串

| 函数 | 格式 | 示例 |
|------|------|------|
| `ms_to_time_str(ms)` | `m:s.ms`（行头显示） | `15200 → "0:15.2"` |
| `ms_to_srt_time(ms)` | `h:m:s,ms`（SRT） | `3723000 → "1:02:03,000"` |
| `ms_to_ass_time(ms)` | `h:m:s.ms`（ASS） | `3723000 → "1:02:03.00"` |
| `ms_to_vtt_time(ms)` | `m:s.ms`（VTT） | `15200 → "0:15.200"` |
| `ms_to_lrc_time(ms)` | `m:s.xx`（LRC） | `15200 → "00:15.20"` |
| `split_time(ms)` | `MM:SS`（简单显示） | `90000 → "01:30"` |

---

## 字符串 → 毫秒

| 函数 | 格式 | 示例 |
|------|------|------|
| `srt_time_to_ms(t)` | `h:m:s,ms` → ms | `"1:02:03,000" → 3723000` |
| `ass_time_to_ms(t)` | `h:m:s.ms` → ms | `"1:02:03.00" → 3723000` |

---

## 用法示例

```python
from chestnut_studio.utils.time_utils import (
    ms_to_time_str,
    ms_to_srt_time,
    ms_to_ass_time,
    ms_to_vtt_time,
    ms_to_lrc_time,
    split_time,
    srt_time_to_ms,
    ass_time_to_ms,
)

# 毫秒 → 字符串
print(ms_to_time_str(15200))      # "0:15.2"
print(ms_to_srt_time(3723000))    # "1:02:03,000"
print(ms_to_ass_time(3723000))    # "1:02:03.00"
print(ms_to_vtt_time(15200))      # "0:15.200"
print(ms_to_lrc_time(15200))      # "00:15.20"
print(split_time(330000))         # "05:30"

# 字符串 → 毫秒
print(srt_time_to_ms("1:02:03,000"))  # 3723000
print(ass_time_to_ms("1:02:03.00"))   # 3723000
```

---

## 函数详细说明

### ms_to_time_str

毫秒转换为 `m:s.ms` 格式（行头显示）。

```python
def ms_to_time_str(ms: int) -> str:
    """毫秒 → m:s.ms 格式
    
    Args:
        ms: 毫秒值
        
    Returns:
        时间字符串，如 "0:15.2"
    """
```

**示例：**
- `15200 → "0:15.2"`
- `60000 → "1:0.0"`
- `3723000 → "62:3.0"`

---

### ms_to_srt_time

毫秒转换为 SRT 时间格式 `h:m:s,ms`。

```python
def ms_to_srt_time(ms: int) -> str:
    """毫秒 → h:m:s,ms 格式
    
    Args:
        ms: 毫秒值
        
    Returns:
        SRT 时间字符串，如 "1:02:03,000"
    """
```

**示例：**
- `3723000 → "1:02:03,000"`
- `0 → "0:00:00,000"`
- `3661000 → "1:01:01,000"`

---

### ms_to_ass_time

毫秒转换为 ASS 时间格式 `h:m:s.ms`。

```python
def ms_to_ass_time(ms: int) -> str:
    """毫秒 → h:m:s.ms 格式
    
    Args:
        ms: 毫秒值
        
    Returns:
        ASS 时间字符串，如 "1:02:03.00"
    """
```

**示例：**
- `3723000 → "1:02:03.00"`
- `0 → "0:00:00.00"`
- `3661000 → "1:01:01.00"`

---

### ms_to_vtt_time

毫秒转换为 VTT 时间格式 `m:s.ms`。

```python
def ms_to_vtt_time(ms: int) -> str:
    """毫秒 → m:s.ms 格式
    
    Args:
        ms: 毫秒值
        
    Returns:
        VTT 时间字符串，如 "0:15.200"
    """
```

**示例：**
- `15200 → "0:15.200"`
- `60000 → "1:0.000"`
- `3723000 → "62:3.000"`

---

### ms_to_lrc_time

毫秒转换为 LRC 时间格式 `m:s.xx`。

```python
def ms_to_lrc_time(ms: int) -> str:
    """毫秒 → m:s.xx 格式
    
    Args:
        ms: 毫秒值
        
    Returns:
        LRC 时间字符串，如 "00:15.20"
    """
```

**示例：**
- `15200 → "00:15.20"`
- `60000 → "01:00.00"`
- `3723000 → "62:03.00"`

---

### split_time

毫秒转换为简单显示格式 `MM:SS`。

```python
def split_time(ms: int) -> str:
    """毫秒 → MM:SS 格式
    
    Args:
        ms: 毫秒值
        
    Returns:
        时间字符串，如 "01:30"
    """
```

**示例：**
- `90000 → "01:30"`
- `0 → "00:00"`
- `3661000 → "61:01"`

---

### srt_time_to_ms

SRT 时间格式转换为毫秒。

```python
def srt_time_to_ms(t: str) -> int:
    """h:m:s,ms 格式 → 毫秒
    
    Args:
        t: SRT 时间字符串，如 "1:02:03,000"
        
    Returns:
        毫秒值
    """
```

**示例：**
- `"1:02:03,000 → 3723000"`
- `"0:00:00,000 → 0"`
- `"1:01:01,000 → 3661000"`

---

### ass_time_to_ms

ASS 时间格式转换为毫秒。

```python
def ass_time_to_ms(t: str) -> int:
    """h:m:s.ms 格式 → 毫秒
    
    Args:
        t: ASS 时间字符串，如 "1:02:03.00"
        
    Returns:
        毫秒值
    """
```

**示例：**
- `"1:02:03.00 → 3723000"`
- `"0:00:00.00 → 0"`
- `"1:01:01.00 → 3661000"`

---

## 注意事项

### 输入类型

- 所有函数接受 `int` 类型的毫秒值
- 负数输入不会报错，但语义无意义

### 中文冒号处理

- `srt_time_to_ms` 和 `ass_time_to_ms` 会自动处理中文冒号（`：` → `:`）
- 提高用户输入的容错性

### 精度说明

- 毫秒精度：1ms
- SRT 格式精度：1ms
- ASS 格式精度：10ms
- LRC 格式精度：10ms

---

## 依赖

- Python 标准库：无
