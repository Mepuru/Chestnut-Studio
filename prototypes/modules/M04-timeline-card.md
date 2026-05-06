# M04 — 打轴编辑卡片（双轴版）

> `src/ui/cards/timeline_card.py`　｜　Phase 3　｜　核心模块，最复杂

---

## 职责

- 双轴时间轴系统（源轴 + 译文轴）
- 字幕条的创建、编辑、合并、拆分、切割
- 快捷键微调轴端
- 撤销/重做
- 右键菜单
- 字幕导入/导出联动
- ASS 文件生成

---

## 双轴设计理念

### 核心概念

| 轴 | 名称 | 用途 | ASS 样式 |
|---|------|------|----------|
| 轴1 | 源轴 | 输入源语言字幕 | `Default` 或自定义 |
| 轴2 | 译文轴 | 输入翻译后的字幕 | `Translation` 或自定义 |

### 同步机制

- **默认同步**：调整轴1的开始/结束时间时，轴2自动同步调整
- **独立模式**：可选择解除同步，独立调整各轴时间
- **同步指示器**：UI 上显示同步状态（锁定/解锁图标）

---

## 类设计

```python
class TimelineCard(QDockWidget):
    """打轴编辑卡片 - 双轴版"""
    
    # 信号
    subtitle_selected = Signal(int, str)  # 字幕被选中 (index, text)
    subtitle_changed = Signal()           # 字幕数据变化（用于刷新波形覆盖）
    axis_switched = Signal(int)           # 轴切换信号 (1 或 2)
    sync_state_changed = Signal(bool)     # 同步状态变化
    
    def __init__(self, parent=None):
        super().__init__("时间轴", parent)
        # 双轴数据结构
        self._axis1_data = {}  # 源轴数据
        self._axis2_data = {}  # 译文轴数据
        self._current_axis = 1  # 当前活动轴 (1 或 2)
        self._sync_enabled = True  # 是否同步
        self._global_interval = 33.33  # ms
        self._current_row = 0
        self._undo_stack = []
        self._undo_index = -1
        self._setup_ui()
        self._connect_signals()
```

---

## 数据结构

```python
# 双轴数据结构
axis_data = {
    1: {  # 源轴
        start_ms: [duration_ms, "text"],
        15200: [3200, "你好"],
        22000: [1800, "谢谢"],
    },
    2: {  # 译文轴
        start_ms: [duration_ms, "text"],
        15200: [3200, "Hello"],
        22000: [1800, "Thank you"],
    },
}

# 同步状态下的数据关联
# 当 sync_enabled = True 时：
# axis1[start_ms] 和 axis2[start_ms] 共享相同的时间点
# 调整 axis1 的时间 → axis2 自动跟随
```

---

## 表格设计

| 属性 | 值 | 说明 |
|------|-----|------|
| 行数 | 101 | 固定可视窗口 |
| 列数 | 2 | 源轴 + 译文轴 |
| 行高 | 15px | |
| 行头 | 动态时间戳 | `m:s.ms` 格式 |
| 列头 | "源轴" / "译文轴" | 双击可编辑样式名 |
| 间隔 | 可选 | 10ms ~ 1s |

### 表格布局

```
┌─────────────────────────────────────────────────────────────┐
│  时间        │  源轴 (轴1)        │  译文轴 (轴2)           │
├──────────────┼────────────────────┼─────────────────────────┤
│  00:15.200   │  ████████ 你好      │  ████████ Hello         │
│  00:18.400   │  ██████   谢谢      │  ██████   Thank you     │
│  00:22.000   │  ████████████████   │  ████████████████       │
│  00:25.600   │                    │                         │
│  00:29.200   │  ██ 对             │  ██ sorry               │
│  00:32.800   │  ████████████ 不起  │  ████████████ about     │
└──────────────┴────────────────────┴─────────────────────────┘
```

---

## 播放控制区域集成

### 工具栏按钮布局

```
┌──────────────────────────────────────────────────────────────────────┐
│  [帧号] | [<<5s] [播放] [5s>>] | [A] [B] [×] | [1] [2] | [🔒] | [倍速] │
└──────────────────────────────────────────────────────────────────────┘
```

### 按钮说明

| 按钮 | 功能 | 样式 |
|------|------|------|
| `[1]` | 选择源轴（轴1） | 选中时高亮蓝色 |
| `[2]` | 选择译文轴（轴2） | 选中时高亮蓝色 |
| `[🔒]` | 同步锁定开关 | 锁定蓝色，解锁灰色 |

### 按钮交互

```python
# 工具栏信号
axis_selected = Signal(int)      # 轴选择 (1 或 2)
sync_toggled = Signal(bool)      # 同步开关

# TimelineCard 槽函数
def set_current_axis(self, axis: int):
    """设置当前活动轴"""
    self._current_axis = axis
    self._refresh_table()
    self.axis_switched.emit(axis)

def toggle_sync(self, enabled: bool):
    """切换同步状态"""
    self._sync_enabled = enabled
    self.sync_state_changed.emit(enabled)
```

---

## 快捷键映射

```python
KEY_MAP = {
    Qt.Key_Q:      "shift_start_left",    # 轴左端左移
    Qt.Key_1:      "shift_start_left",
    Qt.Key_W:      "shift_start_right",   # 轴左端右移
    Qt.Key_2:      "shift_start_right",
    Qt.Key_E:      "shift_end_left",      # 轴右端左移
    Qt.Key_3:      "shift_end_left",
    Qt.Key_R:      "shift_end_right",     # 轴右端右移
    Qt.Key_4:      "shift_end_right",
    Qt.Key_5:      "split_at_cursor",     # 切割
    Qt.Key_Delete: "delete_selected",     # 删除
    Qt.Key_Space:  "toggle_play",         # 播放/暂停
    Qt.Key_S:      "play_selection",      # 试听选区
    Qt.Key_Tab:    "switch_axis",         # 切换轴 (1↔2)
}

CTRL_KEY_MAP = {
    Qt.Key_S: "save",           # Ctrl+S 保存
    Qt.Key_Z: "undo",           # Ctrl+Z 撤销
    Qt.Key_Y: "redo",           # Ctrl+Y 重做
    Qt.Key_X: "cut",            # Ctrl+X 剪切
    Qt.Key_C: "copy",           # Ctrl+C 复制
    Qt.Key_V: "paste",          # Ctrl+V 粘贴
}
```

---

## 核心操作

### 同步调整

```python
def _adjust_subtitle_time(self, axis: int, start_ms: int, delta_ms: int):
    """调整字幕时间（支持同步）
    
    Args:
        axis: 轴编号 (1 或 2)
        start_ms: 字幕开始时间
        delta_ms: 时间变化量
    """
    # 调整当前轴
    if start_ms in self._get_axis_data(axis):
        duration, text = self._get_axis_data(axis)[start_ms]
        new_start = start_ms + delta_ms
        self._get_axis_data(axis)[new_start] = [duration, text]
        del self._get_axis_data(axis)[start_ms]
    
    # 如果启用同步，调整另一个轴
    if self._sync_enabled:
        other_axis = 2 if axis == 1 else 1
        if start_ms in self._get_axis_data(other_axis):
            duration, text = self._get_axis_data(other_axis)[start_ms]
            new_start = start_ms + delta_ms
            self._get_axis_data(other_axis)[new_start] = [duration, text]
            del self._get_axis_data(other_axis)[start_ms]
```

### 合并 (Merge)

```python
def merge_selected(self):
    """合并选中的多行为一条字幕"""
    selected = self._get_selected_range()
    if selected.y_start < selected.y_end:
        # 合并当前轴
        self._merge_axis(self._current_axis, selected)
        
        # 如果启用同步，合并另一个轴
        if self._sync_enabled:
            other_axis = 2 if self._current_axis == 1 else 1
            self._merge_axis(other_axis, selected)
        
        self._push_undo()
        self._refresh_table()
```

### 切割 (Split)

```python
def split_at_cursor(self):
    """在光标位置切割字幕条"""
    selected = self._get_selected_range()
    split_time = int((selected.y_start + self._current_row) * self._global_interval)
    
    # 切割当前轴
    self._split_axis(self._current_axis, split_time)
    
    # 如果启用同步，切割另一个轴
    if self._sync_enabled:
        other_axis = 2 if self._current_axis == 1 else 1
        self._split_axis(other_axis, split_time)
    
    self._push_undo()
    self._refresh_table()
```

### 撤销/重做

```python
def _push_undo(self):
    """保存当前状态到撤销栈"""
    import copy
    state = {
        'axis1_data': copy.deepcopy(self._axis1_data),
        'axis2_data': copy.deepcopy(self._axis2_data),
        'position': self._current_row,
        'current_axis': self._current_axis,
        'sync_enabled': self._sync_enabled,
    }
    # 清除当前位置之后的历史
    self._undo_stack = self._undo_stack[:self._undo_index + 1]
    self._undo_stack.append(state)
    self._undo_index += 1
    # 限制栈大小
    if len(self._undo_stack) > 100:
        self._undo_stack.pop(0)
        self._undo_index -= 1

def undo(self):
    """撤销"""
    if self._undo_index > 0:
        self._undo_index -= 1
        self._restore_state(self._undo_stack[self._undo_index])

def redo(self):
    """重做"""
    if self._undo_index < len(self._undo_stack) - 1:
        self._undo_index += 1
        self._restore_state(self._undo_stack[self._undo_index])
```

---

## 右键菜单

```python
CONTEXT_MENU_ITEMS = [
    ("合并", "merge_selected"),
    ("切割", "split_at_cursor"),
    ("拆分", "break_selected"),
    None,  # 分隔线
    ("剪切", "cut"),
    ("复制", "copy"),
    ("粘贴", "paste"),
    ("删除", "delete_selected"),
    None,
    ("导入字幕", "import_subtitle"),
    ("导出 ASS", "export_ass"),
    None,
    ("切换到源轴", "switch_to_axis1"),
    ("切换到译文轴", "switch_to_axis2"),
    ("切换同步状态", "toggle_sync"),
    None,
    ("循环播放", "loop_selection"),
    ("取消循环", "cancel_loop"),
]
```

---

## 叠轴检测

```python
def _check_overlap(self, axis: int, start: int, end: int) -> int:
    """检测叠轴
    
    Args:
        axis: 轴编号 (1 或 2)
        start: 开始时间
        end: 结束时间
    
    Returns:
        0: 有重叠，阻止操作
        1: 安全，可操作
        2: 有重叠但可调整
    """
    axis_data = self._get_axis_data(axis)
    for s, (d, _) in axis_data.items():
        e = s + d
        if start < e and end > s:  # 有重叠
            if start >= e - self._global_interval:
                return 2  # 可调整
            return 0  # 阻止
    return 1  # 安全
```

---

## 刷新机制

```python
def _refresh_table(self, position: int = 0, select: int = 0, scroll: int = 0):
    """刷新表格显示"""
    self._table.clearSpans()
    self._table.clear()
    
    # 计算当前行号
    if not position:
        position = self._player_position
    self._current_row = int(position / self._global_interval)
    
    # 设置行头时间戳
    headers = [self._ms_to_time(i * self._global_interval + position) 
               for i in range(101)]
    self._table.setVerticalHeaderLabels(headers)
    
    # 填充源轴（轴1）
    self._fill_axis_column(0, self._axis1_data, position)
    
    # 填充译文轴（轴2）
    self._fill_axis_column(1, self._axis2_data, position)
    
    # 高亮当前活动轴的列头
    self._highlight_active_axis()

def _fill_axis_column(self, col: int, axis_data: dict, position: int):
    """填充指定轴的数据"""
    view_start = position
    view_end = position + 101 * self._global_interval
    
    for start in sorted(axis_data):
        delta, text = axis_data[start]
        if start >= view_end:
            break
        end = start + delta
        if end >= view_start:
            self._render_subtitle(col, start, delta, text, position)
```

---

## ASS 文件生成

```python
def generate_ass(self, output_path: str, include_axis1: bool = True, include_axis2: bool = True):
    """生成 ASS 文件
    
    Args:
        output_path: 输出文件路径
        include_axis1: 是否包含源轴
        include_axis2: 是否包含译文轴
    """
    ass_content = self._generate_ass_header()
    
    if include_axis1:
        ass_content += self._generate_ass_events(self._axis1_data, "Default")
    
    if include_axis2:
        ass_content += self._generate_ass_events(self._axis2_data, "Translation")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)

def _generate_ass_header(self) -> str:
    """生成 ASS 文件头"""
    return """[Script Info]
Title: Chestnut Studio Export
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1
Style: Translation,Arial,48,&H0000FFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,8,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def _generate_ass_events(self, axis_data: dict, style: str) -> str:
    """生成 ASS 事件行"""
    events = []
    for start_ms in sorted(axis_data):
        duration_ms, text = axis_data[start_ms]
        end_ms = start_ms + duration_ms
        
        start_str = self._ms_to_ass_time(start_ms)
        end_str = self._ms_to_ass_time(end_ms)
        
        events.append(f"Dialogue: 0,{start_str},{end_str},{style},,0,0,0,,{text}")
    
    return "\n".join(events) + "\n"

def _ms_to_ass_time(self, ms: int) -> str:
    """将毫秒转换为 ASS 时间格式 (H:MM:SS.CC)"""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    centiseconds = (ms % 1000) // 10
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtWidgets | QTableWidget, QDockWidget |
| src/core/subtitle.py | 字幕数据结构 |
| src/core/subtitle_io.py | 字幕导入/导出 |
| src/utils/time_utils.py | 时间格式转换 |

---

## 信号连接图

```
ToolBar                          MainWindow                         TimelineCard
  │ axis_selected ──────────────→ set_current_axis ──────────────→ 切换活动轴
  │ sync_toggled ───────────────→ toggle_sync ───────────────────→ 切换同步状态
  │ ←───────────────────────── axis_switched ←──────────────────── 轴切换完成
  │ ←───────────────────────── sync_state_changed ←────────────── 同步状态变化

PlayerCard                       MainWindow                         TimelineCard
  │ position_changed ───────────→ set_player_position ────────────→ 更新播放位置
  │ duration_changed ───────────→ set_duration ───────────────────→ 更新视频时长

TimelineCard                     MainWindow                         TranslateCard
  │ subtitle_selected ──────────→ show_subtitle ──────────────────→ 显示原文
  │ subtitle_changed ───────────→ refresh_waveform ───────────────→ 刷新波形覆盖
```

---

## UI 布局

```
┌─ ✂️ 时间轴 ────────────────────────────── [_][□][×] ┐
│  [源轴] [译文轴]    [🔒同步]    间隔 [33ms▾]          │  ← 轴选择 + 同步 + 间隔
├─────────────────────────────────────────────────────┤
│  时间        │  源轴              │  译文轴           │
│  00:15.200   │  ████████ 你好      │  ████████ Hello   │
│  00:18.400   │  ██████   谢谢      │  ██████ Thank you │
│  00:22.000   │  ████████████████   │  ████████████████ │
│  00:25.600   │                    │                   │
│  00:29.200   │  ██ 对             │  ██ sorry         │
│  00:32.800   │  ████████████ 不起  │  ████████████ about│
├─────────────────────────────────────────────────────┤
│  [合并] [切割] [拆分] [导入] [导出ASS]  [撤销] [重做] │  ← 操作按钮栏
└─────────────────────────────────────────────────────┘
```
