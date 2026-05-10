# 字幕数据结构

> `chestnut_studio/core/subtitle.py`
> 字幕数据的核心结构和操作。

---

## 职责

- 定义字幕数据结构（SubtitleEntry、SubtitleDict）
- 提供字幕操作接口（增删改查）
- 叠轴检测和处理

---

## 数据类型

### SubtitleEntry

```python
from typing import NamedTuple

class SubtitleEntry(NamedTuple):
    duration_ms: int   # 持续时间（毫秒）
    text: str          # 字幕文本
```

支持多种访问方式：
```python
entry = SubtitleEntry(2000, "你好")
entry.duration_ms    # 2000（属性访问）
entry.text           # "你好"（属性访问）
entry[0]             # 2000（索引访问）
entry[1]             # "你好"（索引访问）
duration, text = entry  # 解包
```

### SubtitleDict

```python
# 字幕字典：列号 → {起始毫秒: SubtitleEntry}
SubtitleDict = dict[int, dict[int, SubtitleEntry]]

# 示例
{
    1: {  # 第 1 列（原文）
        1000: SubtitleEntry(2000, "你好"),
        4000: SubtitleEntry(1500, "世界"),
    },
    2: {},   # 第 2 列（翻译）
    3: {},
    4: {},
}
```

**数据结构说明：**

- 外层字典：列号 → 该列的字幕数据
- 内层字典：起始毫秒 → `SubtitleEntry(duration_ms, text)`
- 列号对应轨道，最多支持 8 个轨道（由 `track_config.py` 配置）

---

## SubtitleManager 类

### 初始化

```python
from chestnut_studio.core.subtitle import SubtitleManager

mgr = SubtitleManager()
# 初始化 8 个空轨道
```

### 基础操作

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get(col, start)` | 列号, 起始ms | `SubtitleEntry` 或 `None` | 获取字幕条 |
| `set(col, start, duration, text)` | 列号, 起始ms, 持续ms, 文本 | `None` | 设置字幕条 |
| `delete(col, start)` | 列号, 起始ms | - | 删除字幕条 |
| `delete_range(col, start, end)` | 列号, 起始ms, 结束ms | - | 删除范围内所有字幕条 |
| `merge(col, start, end, text)` | 列号, 起始ms, 结束ms, 文本 | - | 合并范围内字幕为一条 |
| `split(col, time_point)` | 列号, 时间点 | `bool` | 在时间点切割字幕条 |
| `clear(col)` | 列号 | - | 清空指定列 |
| `clear_all()` | 无 | - | 清空所有列 |
| `copy_track(source_col, target_col)` | 源列号, 目标列号 | `bool` | 复制轨道数据到另一个轨道 |

### 用法示例

```python
from chestnut_studio.core.subtitle import SubtitleManager

mgr = SubtitleManager()

# 设置字幕
mgr.set(1, 1000, 2000, "你好")  # 列1，起始1000ms，持续2000ms，文本"你好"
mgr.set(1, 4000, 1500, "世界")  # 列1，起始4000ms，持续1500ms，文本"世界"

# 获取字幕
result = mgr.get(1, 1000)  # SubtitleEntry(2000, "你好")
result = mgr.get(1, 2000)  # None（不存在）

# 删除字幕
mgr.delete(1, 1000)
mgr.get(1, 1000)  # None

# 合并字幕
mgr.set(1, 1000, 1000, "你")
mgr.set(1, 2000, 1000, "好")
mgr.merge(1, 1000, 3000, "你好")  # 合并为一条

# 切割字幕
mgr.set(1, 1000, 2000, "你好世界")
mgr.split(1, 2000)  # 在2000ms处切割
```

---

## 叠轴检测

### check_overlap

检测字幕条是否重叠。

```python
def check_overlap(col: int, start: int, end: int, interval: float) -> int:
    """检测叠轴

    Returns:
        0 = 有重叠阻止
        1 = 安全
        2 = 有重叠但可调整
    """
```

---

## 轨道操作

### clear / clear_all

```python
mgr.clear(1)     # 清空列1
mgr.clear_all()  # 清空所有
```

### copy_track

```python
success = mgr.copy_track(1, 2)  # 复制列1到列2
```

**注意：** 会覆盖目标轨道的现有数据，使用深拷贝确保两轨道独立。

---

## 轨道管理

### ensure_track / add_track

```python
mgr.ensure_track(5)  # 确保轨道5存在，不存在则创建
mgr.add_track(6)     # 添加轨道6，已存在返回 False
```

### get_max_track

```python
mgr.get_max_track()  # 返回当前最大轨道号
```

---

## 撤销/重做

撤销/重做功能由 UI 层的 `TimelineCard` 管理，不在 `SubtitleManager` 中实现。
详见 [时间轴列表卡片](../ui/cards/timeline_card.md)。

---

## 数据验证

- 起始时间必须 >= 0
- 持续时间必须 > 0
- 文本可以为空字符串
- 列号范围由 `track_config.py` 的 `MAX_TRACK_COUNT` 决定（默认 8）

---

## 依赖

- Python 标准库：`copy`, `typing`
