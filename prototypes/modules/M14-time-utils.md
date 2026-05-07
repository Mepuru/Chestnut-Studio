# M14 — 时间工具函数

> `chestnut_studio/utils/time_utils.py`　｜　Phase 0　｜　纯逻辑工具
> **注意：部分函数尚未实现（vtt_time_to_ms, lrc_time_to_ms）**

---

## 职责

- 毫秒 ↔ 各种时间格式互转
- 供多个模块共用

---

## 函数列表

```python
def ms_to_time_str(ms: int) -> str:
    """毫秒 → m:s.ms 格式 (用于行头显示)
    
    示例: 15200 → "0:15.2"
    """
    m, r = divmod(ms, 60000)
    s, ms = divmod(r, 1000)
    return f"{m}:{s:02d}.{ms // 100}"


def ms_to_srt_time(ms: int) -> str:
    """毫秒 → h:m:s,ms 格式 (SRT)
    
    示例: 3723000 → "1:02:03,000"
    """
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h}:{m:02d}:{s:02d},{ms:03d}"


def ms_to_ass_time(ms: int) -> str:
    """毫秒 → h:m:s.ms 格式 (ASS)
    
    示例: 3723000 → "1:02:03.00"
    """
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h}:{m:02d}:{s:02d}.{ms // 10:02d}"


def ms_to_vtt_time(ms: int) -> str:
    """毫秒 → m:s.ms 格式 (VTT)
    
    示例: 15200 → "0:15.200"
    """
    m, r = divmod(ms, 60000)
    s, ms = divmod(r, 1000)
    return f"{m}:{s:02d}.{ms:03d}"


def ms_to_lrc_time(ms: int) -> str:
    """毫秒 → m:s.xx 格式 (LRC)
    
    示例: 15200 → "00:15.20"
    """
    m, r = divmod(ms, 60000)
    s, ms = divmod(r, 1000)
    return f"{m:02d}:{s:02d}.{ms // 10:02d}"


def srt_time_to_ms(t: str) -> int:
    """h:m:s,ms 格式 → 毫秒 (SRT)
    
    示例: "1:02:03,000" → 3723000
    """
    t = t.replace(',', '.').replace('：', ':')
    h, m, s = t.split(':')
    if '.' in s:
        s, ms = s.split('.')
        ms = ms[:3]
    else:
        ms = '0'
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def ass_time_to_ms(t: str) -> int:
    """h:m:s.ms 格式 → 毫秒 (ASS)
    
    示例: "1:02:03.00" → 3723000
    """
    t = t.replace(',', '.').replace('：', ':')
    h, m, s = t.split(':')
    if '.' in s:
        s, ms = s.split('.')
        ms = (ms + '00')[:2]
    else:
        ms = '0'
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms) * 10


def vtt_time_to_ms(t: str) -> int:
    """m:s.ms 格式 → 毫秒 (VTT)
    
    示例: "0:15.200" → 15200
    """
    t = t.replace(',', '.').replace('：', ':')
    m, s = t.split(':')
    if '.' in s:
        s, ms = s.split('.')
        ms = ms[:3]
    else:
        ms = '0'
    return int(m) * 60000 + int(s) * 1000 + int(ms)


def lrc_time_to_ms(t: str) -> int:
    """m:s.xx 格式 → 毫秒 (LRC)
    
    示例: "00:15.20" → 15200
    """
    t = t.replace(',', '.').replace('：', ':')
    m, s = t.split(':')
    if '.' in s:
        s, ms = s.split('.')
        ms = (ms + '00')[:2]
    else:
        ms = '0'
    return int(m) * 60000 + int(s) * 1000 + int(ms) * 10


def split_time(ms: int) -> str:
    """毫秒 → m:s 格式 (用于简单显示)
    
    示例: 90000 → "01:30"
    """
    s = ms // 1000
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"
```

---

## 测试用例

```python
class TestTimeUtils:
    def test_ms_to_time_str(self):
        assert ms_to_time_str(15200) == "0:15.2"
        assert ms_to_time_str(65000) == "1:05.0"
    
    def test_srt_roundtrip(self):
        ms = 3723000
        assert srt_time_to_ms(ms_to_srt_time(ms)) == ms
    
    def test_ass_roundtrip(self):
        ms = 3723000
        assert ass_time_to_ms(ms_to_ass_time(ms)) == ms
    
    def test_split_time(self):
        assert split_time(90000) == "01:30"
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| 无 | 纯函数模块 |
