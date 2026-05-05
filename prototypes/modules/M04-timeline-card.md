# M04 — 打轴编辑卡片

> `src/ui/cards/timeline_card.py`　｜　Phase 3　｜　核心模块，最复杂

---

## 职责

- 动态时间轴表格（101行×5列）
- 字幕条的创建、编辑、合并、拆分、切割
- 快捷键微调轴端
- 撤销/重做
- 右键菜单
- 字幕导入/导出联动

---

## 类设计

```python
class TimelineCard(QDockWidget):
    """打轴编辑卡片"""
    
    # 信号
    subtitle_selected = Signal(int, str)  # 字幕被选中 (index, text)
    subtitle_changed = Signal()           # 字幕数据变化（用于刷新波形覆盖）
    
    def __init__(self, parent=None):
        super().__init__("时间轴", parent)
        self._subtitle_dict = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}}
        self._global_interval = 33.33  # ms
        self._current_row = 0
        self._style_names = ["1", "2", "3", "4", "5"]
        self._undo_stack = []
        self._undo_index = -1
        self._clipboard = []
        self._setup_ui()
        self._connect_signals()
```

---

## 数据结构

```python
# 核心数据结构
subtitle_dict = {
    0: {                           # 第1列
        start_ms: [duration_ms, "text"],
        15200: [3200, "你好"],
        22000: [1800, "谢谢"],
    },
    1: {},   # 第2列
    2: {},   # 第3列
    3: {},   # 第4列
    4: {},   # 第5列
}
```

---

## 表格设计

| 属性 | 值 | 说明 |
|------|-----|------|
| 行数 | 101 | 固定可视窗口 |
| 列数 | 5 | 5条字幕轨道 |
| 行高 | 15px | |
| 行头 | 动态时间戳 | `m:s.ms` 格式 |
| 列头 | 样式名 | 默认 "1"~"5"，双击可编辑 |
| 间隔 | 可选 | 10ms ~ 1s |

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
        for col in selected.columns:
            # 取第一个非空文本
            text = self._find_first_text(col, selected.y_start, selected.y_end)
            # 合并时间范围
            start = int((selected.y_start + self._current_row) * self._global_interval)
            end = int((selected.y_end + self._current_row + 1) * self._global_interval)
            # 删除旧数据
            self._remove_range(col, start, end)
            # 写入合并后的数据
            self._subtitle_dict[col][start] = [end - start, text]
            # 设置表格合并
            self._table.setSpan(selected.y_start, col, selected.y_end - selected.y_start + 1, 1)
        self._push_undo()
        self._refresh_table()
```

### 切割 (Split)

```python
def split_at_cursor(self):
    """在光标位置切割字幕条"""
    selected = self._get_selected_range()
    split_time = int((selected.y_start + self._current_row) * self._global_interval)
    for col in self._subtitle_dict:
        for start, (delta, text) in list(self._subtitle_dict[col].items()):
            end = start + delta
            if start < split_time < end:
                # 切割为两段
                self._subtitle_dict[col][start] = [split_time - start, text]
                self._subtitle_dict[col][split_time] = [end - split_time, text]
    self._push_undo()
    self._refresh_table()
```

### 拆分 (Break)

```python
def break_selected(self):
    """将跨行字幕条拆成每行一条"""
    selected = self._get_selected_range()
    for col in selected.columns:
        for y in range(selected.y_start, selected.y_end + 1):
            time_point = int((y + self._current_row) * self._global_interval)
            # 查找包含此时间点的字幕条
            for start, (delta, text) in list(self._subtitle_dict[col].items()):
                if start <= time_point < start + delta:
                    # 拆分为独立的每行
                    self._subtitle_dict[col][time_point] = [int(self._global_interval), text]
    self._push_undo()
    self._refresh_table()
```

### 撤销/重做

```python
def _push_undo(self):
    """保存当前状态到撤销栈"""
    import copy
    state = {
        'subtitle_dict': copy.deepcopy(self._subtitle_dict),
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
def _check_overlap(self, col: int, start: int, end: int) -> int:
    """检测叠轴
    
    Returns:
        0: 有重叠，阻止操作
        1: 安全，可操作
        2: 有重叠但可调整
    """
    for s, (d, _) in self._subtitle_dict[col].items():
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
    for col, sub_data in self._subtitle_dict.items():
        for start in sorted(sub_data):
            delta, text = sub_data[start]
            if start >= view_end:
                break
            end = start + delta
            if end >= view_start:
                self._render_subtitle(col, start, delta, text, position)
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtWidgets | QTableWidget, QDockWidget |
| src/core/subtitle.py | 字幕数据结构 |
| src/core/subtitle_io.py | 字幕导入/导出 |
| src/utils/time_utils.py | 时间格式转换 |
