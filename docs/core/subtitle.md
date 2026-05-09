# 字幕数据结构

> `chestnut_studio/core/subtitle.py`
> 字幕数据的核心结构和操作，包含撤销/重做支持。

---

## 职责

- 定义字幕数据结构（SubtitleDict）
- 提供字幕操作接口（增删改查）
- 支持撤销/重做功能
- 叠轴检测和处理

---

## 数据类型

### SubtitleDict

```python
# 字幕字典：列号 → {起始毫秒: [持续毫秒, "文本"]}
SubtitleDict = dict[int, dict[int, list]]

# 示例
{
    1: {1000: [2000, "你好"], 4000: [1500, "世界"]},  # 轨道1
    2: {},   # 轨道2
    3: {},   # 轨道3
    4: {},   # 轨道4
    # ... 最多 8 个轨道
}
```

**数据结构说明：**

- 外层字典：列号 → 该列的字幕数据
- 内层字典：起始毫秒 → `[持续毫秒, "文本"]`
- 列号对应轨道，最多支持 8 个轨道（由 `track_config.py` 配置）

---

## SubtitleManager 类

### 初始化

```python
from chestnut_studio.core.subtitle import SubtitleManager

mgr = SubtitleManager()
```

### 基础操作

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get(col, start)` | 列号, 起始ms | `[duration, text]` 或 `None` | 获取字幕条 |
| `set(col, start, duration, text)` | 列号, 起始ms, 持续ms, 文本 | `None` | 设置字幕条 |
| `delete(col, start)` | 列号, 起始ms | `bool` | 删除字幕条 |
| `delete_range(col, start, end)` | 列号, 起始ms, 结束ms | `int` | 删除范围内所有字幕条 |
| `merge(col, start, end, text)` | 列号, 起始ms, 结束ms, 文本 | `bool` | 合并范围内字幕为一条 |
| `split(col, time_point)` | 列号, 时间点 | `bool` | 在时间点切割字幕条 |
| `clear(col)` | 列号 | `None` | 清空指定列 |
| `clear_all()` | 无 | `None` | 清空所有列 |
| `copy_track(source_col, target_col)` | 源列号, 目标列号 | `bool` | 复制轨道数据到另一个轨道 |

### 用法示例

```python
from chestnut_studio.core.subtitle import SubtitleManager

mgr = SubtitleManager()

# 设置字幕
mgr.set(1, 1000, 2000, "你好")  # 列1，起始1000ms，持续2000ms，文本"你好"
mgr.set(1, 4000, 1500, "世界")  # 列1，起始4000ms，持续1500ms，文本"世界"

# 获取字幕
result = mgr.get(1, 1000)  # [2000, "你好"]
result = mgr.get(1, 2000)  # None（不存在）

# 删除字幕
mgr.delete(1, 1000)  # True
mgr.get(1, 1000)     # None

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
def check_overlap(col: int, start: int, end: int, interval: int = 0) -> int:
    """检测叠轴
    
    Args:
        col: 列号
        start: 起始ms
        end: 结束ms
        interval: 最小间隔ms
        
    Returns:
        0 = 有重叠阻止
        1 = 安全
        2 = 有重叠但可调整
    """
```

**用法示例：**

```python
mgr.set(1, 1000, 2000, "第一条")

# 检测重叠
result = mgr.check_overlap(1, 1500, 2500)  # 0，有重叠阻止
result = mgr.check_overlap(1, 3000, 4000)  # 1，安全
result = mgr.check_overlap(1, 2500, 3500, interval=500)  # 2，有重叠但可调整
```

---

## 撤销/重做

### 接口

```python
def push_undo() -> None:
    """保存当前状态到撤销栈（操作前调用）"""

def undo() -> bool:
    """撤销，返回是否成功"""

def redo() -> bool:
    """重做，返回是否成功"""
```

### 用法示例

```python
mgr = SubtitleManager()

# 操作前保存状态
mgr.push_undo()
mgr.set(1, 1000, 2000, "你好")

# 撤销
mgr.undo()  # True，恢复到之前的状态

# 重做
mgr.redo()  # True，恢复到设置后的状态
```

### 注意事项

- 撤销栈最多 100 步（`MAX_UNDO = 100`）
- 使用 `copy.deepcopy` 隔离状态
- 每次操作前调用 `push_undo()` 保存状态

---

## 轨道操作

### clear

清空指定列的所有字幕。

```python
mgr.clear(1)  # 清空列1
```

### clear_all

清空所有列的所有字幕。

```python
mgr.clear_all()  # 清空所有
```

### copy_track

复制轨道数据到另一个轨道。

```python
success = mgr.copy_track(1, 2)  # 复制列1到列2
```

**注意事项：**
- 会覆盖目标轨道的现有数据
- 操作前需要用户确认

---

## 数据验证

### 时间范围

- 起始时间必须 >= 0
- 持续时间必须 > 0
- 文本可以为空字符串

### 轨道范围

- 列号范围由 `track_config.py` 的 `MAX_TRACK_COUNT` 决定（默认 8）
- 超出范围的列号会返回空字典

---

## 性能考虑

### 深拷贝开销

- `push_undo()` 使用 `copy.deepcopy` 保存状态
- 每次保存会复制整个字典结构
- 建议在批量操作前只调用一次 `push_undo()`

### 内存占用

- 撤销栈最多保存 100 个状态
- 每个状态是完整的字典副本
- 大量字幕时内存占用较高

---

## 依赖

- Python 标准库：`copy`
