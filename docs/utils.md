# Chestnut Studio — 工具层模块

> `chestnut_studio/utils/` 下各模块的接口和用法。
> 工具层无外部依赖，提供通用工具函数。

---

## 时间格式转换 (`time_utils.py`)

毫秒与各种字幕时间格式之间的互转。所有函数均为纯函数，无状态。

### 毫秒 → 字符串

| 函数 | 格式 | 示例 |
|------|------|------|
| `ms_to_time_str(ms)` | `m:s.ms`（行头显示） | `15200 → "0:15.2"` |
| `ms_to_srt_time(ms)` | `h:m:s,ms`（SRT） | `3723000 → "1:02:03,000"` |
| `ms_to_ass_time(ms)` | `h:m:s.ms`（ASS） | `3723000 → "1:02:03.00"` |
| `ms_to_vtt_time(ms)` | `m:s.ms`（VTT） | `15200 → "0:15.200"` |
| `ms_to_lrc_time(ms)` | `m:s.xx`（LRC） | `15200 → "00:15.20"` |
| `split_time(ms)` | `MM:SS`（简单显示） | `90000 → "01:30"` |

### 字符串 → 毫秒

| 函数 | 格式 | 示例 |
|------|------|------|
| `srt_time_to_ms(t)` | `h:m:s,ms` → ms | `"1:02:03,000" → 3723000` |
| `ass_time_to_ms(t)` | `h:m:s.ms` → ms | `"1:02:03.00" → 3723000` |

### 用法示例

```python
from chestnut_studio.utils.time_utils import ms_to_srt_time, split_time

# 状态栏显示
print(split_time(330000))       # "05:30"

# SRT 导出
print(ms_to_srt_time(330012))   # "0:05:30,012"
```

### 注意事项

- 所有函数接受 `int` 类型的毫秒值
- 负数输入不会报错，但语义无意义
- `srt_time_to_ms` 和 `ass_time_to_ms` 会自动处理中文冒号（`：` → `:`）
