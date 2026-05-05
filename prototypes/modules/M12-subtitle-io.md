# M12 — 字幕导入/导出

> `src/core/subtitle_io.py`　｜　Phase 4　｜　纯逻辑，无 UI 依赖

---

## 职责

- SRT 格式导入/导出
- ASS 格式导入/导出
- VTT 格式导入（YouTube 格式）
- LRC 格式导入

---

## 类设计

```python
class SubtitleIO:
    """字幕导入/导出"""
    
    @staticmethod
    def import_srt(path: str) -> dict[int, list]:
        """导入 SRT 文件
        
        Returns:
            {start_ms: [duration_ms, "text"], ...}
        """
        ...
    
    @staticmethod
    def import_vtt(path: str) -> dict[int, list]:
        """导入 VTT 文件（支持 YouTube 逐字格式）"""
        ...
    
    @staticmethod
    def import_ass(path: str) -> dict[str, dict[int, list]]:
        """导入 ASS 文件
        
        Returns:
            {"样式名": {start_ms: [duration_ms, "text"], ...}}
        """
        ...
    
    @staticmethod
    def import_lrc(path: str) -> dict[int, list]:
        """导入 LRC 文件"""
        ...
    
    @staticmethod
    def export_srt(path: str, data: dict[int, list], 
                   video_start: int = 0, sub_start: int = 0):
        """导出 SRT 文件
        
        Args:
            path: 输出路径
            data: 字幕数据
            video_start: 视频起始时间 (ms)
            sub_start: 字幕起始偏移 (ms)
        """
        ...
    
    @staticmethod
    def export_ass(path: str, data: dict[int, list], 
                   styles: dict = None):
        """导出 ASS 文件
        
        Args:
            path: 输出路径
            data: 字幕数据
            styles: 样式配置
        """
        ...
```

---

## 时间格式转换

```python
def ms_to_srt_time(ms: int) -> str:
    """毫秒 → SRT 时间格式 (h:m:s,ms)"""
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h}:{m:02d}:{s:02d},{ms:03d}"

def ms_to_ass_time(ms: int) -> str:
    """毫秒 → ASS 时间格式 (h:m:s.ms)"""
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h}:{m:02d}:{s:02d}.{ms:02d}"

def ms_to_vtt_time(ms: int) -> str:
    """毫秒 → VTT 时间格式 (m:s.ms)"""
    m, r = divmod(ms, 60000)
    s, ms = divmod(r, 1000)
    return f"{m}:{s:02d}.{ms:03d}"

def srt_time_to_ms(t: str) -> int:
    """SRT 时间格式 → 毫秒"""
    t = t.replace(',', '.')
    h, m, s = t.split(':')
    if '.' in s:
        s, ms = s.split('.')
    else:
        ms = '0'
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
```

---

## SRT 格式

```
1
00:00:01,000 --> 00:00:03,500
你好世界

2
00:00:05,000 --> 00:00:07,200
谢谢
```

解析逻辑：
```python
def import_srt(path: str) -> dict[int, list]:
    result = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '-->' in line:
            start_str, end_str = line.split('-->')
            start = srt_time_to_ms(start_str.strip())
            end = srt_time_to_ms(end_str.strip())
            text = lines[i + 1].strip() if i + 1 < len(lines) else ""
            result[start] = [end - start, text]
            i += 3  # 跳过序号、时间、文本、空行
        else:
            i += 1
    return result
```

---

## VTT 格式

标准格式：
```
WEBVTT

00:00:01.000 --> 00:00:03.500
你好世界
```

YouTube 逐字格式：
```
00:00:01.000 --> 00:00:01.500
<c>你</c>
00:00:01.500 --> 00:00:02.000
<c>好</c>
```

---

## ASS 格式

```ass
[V4+ Styles]
Format: Name, Fontname, Fontsize, ...
Style: Default,Arial,20,...

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.50,Default,,0,0,0,,你好世界
```

解析逻辑：
```python
def import_ass(path: str) -> dict[str, dict[int, list]]:
    result = {}
    current_style = "Default"
    
    with open(path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line.startswith('Dialogue:'):
                parts = line.split(',', 9)
                start = ass_time_to_ms(parts[1])
                end = ass_time_to_ms(parts[2])
                style = parts[3]
                text = parts[9].replace('\\N', '\n')
                
                if style not in result:
                    result[style] = {}
                result[style][start] = [end - start, text]
    
    return result
```

---

## LRC 格式

```
[00:01.00]你好世界
[00:05.00]谢谢
```

解析逻辑：
```python
def import_lrc(path: str) -> dict[int, list]:
    result = {}
    times = []
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('[') and ']' in line:
                time_str = line[1:line.index(']')]
                text = line[line.index(']') + 1:]
                ms = lrc_time_to_ms(time_str)
                times.append((ms, text))
    
    # 计算持续时间（到下一个时间点）
    for i, (start, text) in enumerate(times):
        if i + 1 < len(times):
            duration = times[i + 1][0] - start
        else:
            duration = 3000  # 默认 3 秒
        result[start] = [duration, text]
    
    return result
```

---

## 测试用例

```python
class TestSubtitleIO:
    def test_srt_import(self):
        # 创建测试 SRT 文件
        ...
        data = SubtitleIO.import_srt("test.srt")
        assert 1000 in data
        assert data[1000] == [2500, "你好世界"]
    
    def test_srt_export(self):
        data = {1000: [2500, "你好世界"]}
        SubtitleIO.export_srt("test.srt", data)
        # 验证文件内容
        ...
    
    def test_lrc_import(self):
        data = SubtitleIO.import_lrc("test.lrc")
        assert 1000 in data
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| codecs (标准库) | 文件编码处理 |
| 无外部依赖 | 纯逻辑模块 |
