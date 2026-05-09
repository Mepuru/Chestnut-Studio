# 轨道配置

> `chestnut_studio/core/track_config.py`
> 集中管理轨道颜色、数量等配置，供 UI 层各组件统一使用。

---

## 职责

- 定义轨道颜色方案（前景色）
- 定义默认/最大轨道数量
- 提供颜色和数量的辅助函数
- 确保所有 UI 组件使用统一的轨道配置

---

## 设计理念

### 为什么需要集中配置

项目中有多个 UI 组件需要显示轨道颜色：

| 组件 | 用途 |
|------|------|
| `TimelineCard` | 时间轴表格中的轨道列、筛选器、复制轴下拉框 |
| `WaveformCard` | 波形图中的字幕条颜色、轨道选择器 |
| `TranslateCard` | 翻译面板中的轨道标签颜色 |

如果每个组件各自定义颜色，会导致：
- 颜色不一致
- 新增轨道时需要修改多处代码
- 维护成本高

### 配置原则

- **单一来源**：所有轨道相关配置在此文件中定义
- **核心层**：不依赖 PySide6，只定义十六进制颜色字符串
- **UI 层**：从核心层获取配置，自行创建 `QColor` 等 UI 对象

---

## 常量

### DEFAULT_TRACK_COUNT

```python
DEFAULT_TRACK_COUNT = 4
```

默认初始显示的轨道数。即使数据中没有这么多轨道，UI 也会显示至少这么多轨道选项。

### MAX_TRACK_COUNT

```python
MAX_TRACK_COUNT = 8
```

最大支持的轨道数。导入 ASS 字幕时，如果样式数超过此限制，多余的样式会被忽略。

### TRACK_COLORS_HEX

```python
TRACK_COLORS_HEX: list[str] = [
    "#3b82f6",  # 轨道1: 蓝色
    "#10b981",  # 轨道2: 绿色
    "#f59e0b",  # 轨道3: 橙色
    "#ec4899",  # 轨道4: 粉色
    "#8b5cf6",  # 轨道5: 紫色
    "#06b6d4",  # 轨道6: 青色
    "#f97316",  # 轨道7: 橙红色
    "#84cc16",  # 轨道8: 黄绿色
]
```

轨道前景色列表，按轨道号索引。轨道号从 1 开始，使用时需 `-1` 作为列表索引。超出范围时循环使用。

---

## 函数

### get_track_color

```python
def get_track_color(track: int) -> str:
```

获取指定轨道的前景色（十六进制字符串）。

| 参数 | 类型 | 说明 |
|------|------|------|
| `track` | `int` | 轨道号（从 1 开始） |

**返回值：** `#RRGGBB` 格式的颜色字符串，超出范围时循环使用。

**用法示例：**

```python
from chestnut_studio.core.track_config import get_track_color

color = get_track_color(1)   # "#3b82f6" (蓝色)
color = get_track_color(5)   # "#8b5cf6" (紫色)
color = get_track_color(9)   # "#3b82f6" (循环回蓝色)
```

---

### get_track_bg_color_hex

```python
def get_track_bg_color_hex(track: int, alpha: int = 30) -> str:
```

获取指定轨道的背景色（带透明度的十六进制字符串）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `track` | `int` | - | 轨道号（从 1 开始） |
| `alpha` | `int` | `30` | 透明度 (0-255) |

**返回值：** `#AARRGGBB` 格式的颜色字符串。

**用法示例：**

```python
from chestnut_studio.core.track_config import get_track_bg_color_hex

bg_color = get_track_bg_color_hex(1)      # "#1e3b82f6" (蓝色，低透明度)
bg_color = get_track_bg_color_hex(2, 50)  # "#3210b981" (绿色，中透明度)
```

---

### get_effective_track_count

```python
def get_effective_track_count(current_max: int) -> int:
```

获取有效的轨道显示数量。保证至少显示 `DEFAULT_TRACK_COUNT` 个轨道，不超过 `MAX_TRACK_COUNT`。

| 参数 | 类型 | 说明 |
|------|------|------|
| `current_max` | `int` | 当前数据中的最大轨道号 |

**返回值：** 应显示的轨道数量。

**用法示例：**

```python
from chestnut_studio.core.track_config import get_effective_track_count

count = get_effective_track_count(2)   # 4 (至少显示4个)
count = get_effective_track_count(6)   # 6 (数据有6个就显示6个)
count = get_effective_track_count(10)  # 8 (最多显示8个)
```

---

## 使用方式

### 在 UI 组件中使用

```python
from PySide6.QtGui import QColor
from chestnut_studio.core.track_config import (
    TRACK_COLORS_HEX,
    get_track_color,
    get_effective_track_count,
)

# 获取颜色字符串
color_hex = get_track_color(1)  # "#3b82f6"

# 创建 QColor 对象（UI 层职责）
qcolor = QColor(color_hex)

# 批量创建 QColor 列表
qcolors = [QColor(c) for c in TRACK_COLORS_HEX]

# 获取应显示的轨道数
max_track = get_effective_track_count(subtitle_mgr.get_max_track())
```

### 在下拉框中填充轨道选项

```python
from chestnut_studio.core.track_config import get_effective_track_count, get_track_color

max_track = get_effective_track_count(data_max_track)
for i in range(max_track):
    color = get_track_color(i + 1)
    combo.addItem(f"轨道 {i + 1}")
    combo.setItemData(i, QColor(color), Qt.ForegroundRole)
```

---

## 扩展轨道

### 添加新轨道颜色

如需支持更多轨道，只需在 `TRACK_COLORS_HEX` 列表中添加新颜色：

```python
TRACK_COLORS_HEX: list[str] = [
    # ... 现有颜色 ...
    "#新颜色1",  # 轨道9
    "#新颜色2",  # 轨道10
]
```

同时更新 `MAX_TRACK_COUNT` 常量。

### 注意事项

- 颜色应有足够的区分度，避免相邻轨道颜色过于相似
- 颜色在深色背景上应有良好的可读性
- 建议使用饱和度中等、亮度适中的颜色

---

## 依赖关系

```
core/track_config.py  ← 无外部依赖（纯数据配置）
       ↑
       ├── ui/cards/timeline_card.py
       ├── ui/cards/waveform_card.py
       └── ui/cards/translate_card.py
```

- **核心层**：不依赖 PySide6，只定义十六进制颜色字符串
- **UI 层**：导入配置后自行创建 `QColor` 等 UI 对象

---

## 依赖

- Python 标准库：无
