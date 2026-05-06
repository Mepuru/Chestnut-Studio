# M04 — 打轴编辑卡片

> `src/ui/cards/timeline_card.py`　｜　Phase 3　｜　核心模块，最复杂

---

## 职责

- 时间轴表格（101行×1列）
- 字幕条的创建、编辑、合并、拆分、切割
- 快捷键微调轴端
- 撤销/重做
- 右键菜单
- 字幕导入/导出联动

---

## 设计理念

### 核心概念

时间轴卡片只负责**打轴**（设置字幕的开始/结束时间），不负责填写内容。

- **时间轴区域**：只显示一个轴，用户在这里打轴
- **翻译面板**：分为源语言区和目标语言区，用户在这里填写内容
- **数据同步**：打轴时，源语言和目标语言共享相同的时间点

### 数据流

```
┌─────────────┐    打轴（设置时间）    ┌─────────────┐
│  TimelineCard│ ────────────────────→ │  数据存储    │
│  （时间轴）   │                       │  axis_data  │
└─────────────┘                       └─────────────┘
                                            │
                                            ▼
┌─────────────┐    填写内容            ┌─────────────┐
│ TranslateCard│ ←──────────────────── │  数据存储    │
│ （翻译面板）  │    源语言 + 目标语言   │  axis_data  │
└─────────────┘                       └─────────────┘
```

---

## 类设计

```python
class TimelineCard(QDockWidget):
    """打轴编辑卡片"""
    
    # 信号
    subtitle_selected = Signal(int)  # 字幕被选中 (start_ms)
    subtitle_changed = Signal()      # 字幕数据变化（用于刷新波形覆盖）
    
    def __init__(self, parent=None):
        super().__init__("时间轴", parent)
        self._axis_data = {}  # 字幕数据 {start_ms: [duration_ms, ""]}
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
# 字幕数据结构
axis_data = {
    start_ms: [duration_ms, ""],  # 文本字段留空，由翻译面板填写
    15200: [3200, ""],
    22000: [1800, ""],
}

# 完整数据结构（包含源语言和目标语言）
subtitle_data = {
    15200: {
        "duration": 3200,
        "source": "你好",      # 源语言（由翻译面板填写）
        "target": "Hello",     # 目标语言（由翻译面板填写）
    },
    22000: {
        "duration": 1800,
        "source": "谢谢",
        "target": "Thank you",
    },
}
```

---

## 表格设计

| 属性 | 值 | 说明 |
|------|-----|------|
| 行数 | 101 | 固定可视窗口 |
| 列数 | 1 | 只显示时间轴 |
| 行高 | 15px | |
| 行头 | 动态时间戳 | `m:s.ms` 格式 |
| 列头 | "时间轴" | 固定 |
| 间隔 | 可选 | 10ms ~ 1s |

### 表格布局

```
┌─────────────────────────────────────────┐
│  时间轴                                 │
├─────────────────────────────────────────┤
│  00:15.200   │  ████████████████████    │
│  00:18.400   │  ██████████████████      │
│  00:22.000   │  ████████████████████████│
│  00:25.600   │                          │
│  00:29.200   │  ████                    │
│  00:32.800   │  ██████████████████████  │
└──────────────┴──────────────────────────┘
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

### 合并 (Merge)

```python
def merge_selected(self):
    """合并选中的多行为一条字幕"""
    selected = self._get_selected_range()
    if selected.y_start < selected.y_end:
        # 取第一个非空文本
        text = self._find_first_text(selected.y_start, selected.y_end)
        # 合并时间范围
        start = int((selected.y_start + self._current_row) * self._global_interval)
        end = int((selected.y_end + self._current_row + 1) * self._global_interval)
        # 删除旧数据
        self._remove_range(start, end)
        # 写入合并后的数据
        self._axis_data[start] = [end - start, ""]
        # 设置表格合并
        self._table.setSpan(selected.y_start, 0, selected.y_end - selected.y_start + 1, 1)
        self._push_undo()
        self._refresh_table()
```

### 切割 (Split)

```python
def split_at_cursor(self):
    """在光标位置切割字幕条"""
    selected = self._get_selected_range()
    split_time = int((selected.y_start + self._current_row) * self._global_interval)
    for start, (delta, text) in list(self._axis_data.items()):
        end = start + delta
        if start < split_time < end:
            # 切割为两段
            self._axis_data[start] = [split_time - start, text]
            self._axis_data[split_time] = [end - split_time, text]
    self._push_undo()
    self._refresh_table()
```

### 撤销/重做

```python
def _push_undo(self):
    """保存当前状态到撤销栈"""
    import copy
    state = {
        'axis_data': copy.deepcopy(self._axis_data),
        'position': self._current_row,
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
    None,
    ("循环播放", "loop_selection"),
    ("取消循环", "cancel_loop"),
]
```

---

## 叠轴检测

```python
def _check_overlap(self, start: int, end: int) -> int:
    """检测叠轴
    
    Returns:
        0: 有重叠，阻止操作
        1: 安全，可操作
        2: 有重叠但可调整
    """
    for s, (d, _) in self._axis_data.items():
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
    
    # 填充字幕条
    view_start = position
    view_end = position + 101 * self._global_interval
    for start in sorted(self._axis_data):
        delta, text = self._axis_data[start]
        if start >= view_end:
            break
        end = start + delta
        if end >= view_start:
            self._render_subtitle(start, delta, text, position)
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
  │ play_clicked ──────────────→ play_pause ───────────────────→ QMediaPlayer
  │ skip_forward ──────────────→ _on_skip_forward ──────────────→ set_position
  │ ab_loop_a_clicked ─────────→ _on_ab_loop_set_a ────────────→ set_ab_loop_a
  │ ab_loop_b_clicked ─────────→ _on_ab_loop_set_b ────────────→ set_ab_loop_b
  │ ab_loop_clear_clicked ─────→ _on_ab_loop_clear ────────────→ clear_ab_loop
  │ ←───────────────────────── update_position ←──────────────── position_changed
  │ ←───────────────────────── set_duration ←─────────────────── duration_changed
  │ ←───────────────────── update_ab_loop_state ←─────────────── ab_loop_changed
                              │
                              ├──→ WaveformCard.update_position
                              ├──→ WaveformCard.set_ab_loop_region
                              └──→ StatusBar.set_time

TimelineCard                     MainWindow                         TranslateCard
  │ subtitle_selected ──────────→ show_subtitle ──────────────────→ 显示源语言和目标语言
  │ subtitle_changed ───────────→ refresh_waveform ───────────────→ 刷新波形覆盖
```

---

## UI 布局

```
┌─ ✂️ 时间轴 ────────────────────────────── [_][□][×] ┐
│  间隔 [33ms▾]                                        │  ← 间隔设置
├─────────────────────────────────────────────────────┤
│  时间轴                                              │
│  00:15.200   │  ████████████████████                 │
│  00:18.400   │  ██████████████████                   │
│  00:22.000   │  ████████████████████████████████████ │
│  00:25.600   │                                      │
│  00:29.200   │  ████                                │
│  00:32.800   │  ██████████████████████████████       │
├─────────────────────────────────────────────────────┤
│  [合并] [切割] [拆分] [导入]         [撤销] [重做]    │  ← 操作按钮栏
└─────────────────────────────────────────────────────┘
```
