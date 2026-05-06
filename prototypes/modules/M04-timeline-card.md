# M04 — 时间轴列表卡片

> `src/ui/cards/timeline_card.py`　｜　Phase 3　｜　显示已打轴的字幕列表

---

## 职责

- 显示已打轴的字幕列表（编号 + 起止时间）
- 提供查看、编辑、锁定功能
- 支持撤销/重做
- 与音频波形区联动

---

## 设计理念

### 核心概念

时间轴卡片**不负责打轴**，只负责**显示和管理**已打轴的字幕条。

- **打轴**：在音频波形区通过快捷键完成
- **时间轴区**：显示打好轴的列表，提供查看、编辑、锁定功能
- **翻译面板**：填写源语言和目标语言内容

### 工作流程

```
1. 用户在音频波形区听音频
2. 通过快捷键标记字幕的开始和结束点（打轴）
3. 时间轴卡片显示所有标记好的字幕条
4. 用户可以：
   - 查看：跳转到字幕条的起始点
   - 编辑：调整字幕条的前后区间
   - 锁定：锁定字幕条，防止误操作
```

### 数据流

```
┌─────────────┐    打轴（标记时间点）    ┌─────────────┐
│ WaveformCard │ ──────────────────────→ │  数据存储    │
│ （音频波形）  │    快捷键操作           │ subtitle_data│
└─────────────┘                         └─────────────┘
                                              │
                                              ▼
┌─────────────┐    显示列表              ┌─────────────┐
│ TimelineCard │ ←───────────────────── │  数据存储    │
│ （时间轴）   │    编号+起止时间        │ subtitle_data│
└─────────────┘                         └─────────────┘
```

---

## 类设计

```python
class TimelineCard(QDockWidget):
    """时间轴列表卡片"""
    
    # 信号
    subtitle_selected = Signal(int)  # 字幕被选中 (start_ms)
    subtitle_changed = Signal()      # 字幕数据变化
    jump_to_position = Signal(int)   # 跳转到指定位置 (ms)
    
    def __init__(self, parent=None):
        super().__init__("时间轴", parent)
        self._subtitles = []  # 字幕列表 [{start, end, locked}, ...]
        self._setup_ui()
```

---

## 数据结构

```python
# 字幕列表数据结构
subtitles = [
    {
        "id": 1,              # 编号
        "start_ms": 15200,    # 开始时间 (ms)
        "end_ms": 18400,      # 结束时间 (ms)
        "locked": False,      # 是否锁定
    },
    {
        "id": 2,
        "start_ms": 22000,
        "end_ms": 23800,
        "locked": False,
    },
    # ...
]
```

---

## UI 布局

```
┌─ 📋 时间轴 ────────────────────────────── [_][□][×] ┐
│                                                      │
│  #  │ 开始时间 │ 结束时间 │ 时长   │ 操作            │
│─────┼──────────┼──────────┼────────┼─────────────────│
│  1  │ 00:15.2  │ 00:18.4  │ 3.2s   │ 👁 ✏️ 🔒       │
│  2  │ 00:22.0  │ 00:23.8  │ 1.8s   │ 👁 ✏️ 🔒       │
│  3  │ 00:25.6  │ 00:29.2  │ 3.6s   │ 👁 ✏️ 🔒       │
│  4  │ 00:32.8  │ 00:36.4  │ 3.6s   │ 👁 ✏️ 🔒       │
│  ...                                                  │
│                                                      │
├──────────────────────────────────────────────────────┤
│  共 4 条  │  [撤销] [重做]  │  [全部锁定] [全部解锁]  │
└──────────────────────────────────────────────────────┘
```

---

## 表格设计

| 列 | 内容 | 宽度 | 说明 |
|----|------|------|------|
| # | 编号 | 40px | 自动编号 |
| 开始时间 | `m:s.ms` | 80px | 字幕开始时间 |
| 结束时间 | `m:s.ms` | 80px | 字幕结束时间 |
| 时长 | `x.xs` | 60px | 持续时间 |
| 操作 | 按钮组 | 120px | 👁 ✏️ 🔒 |

---

## 操作按钮

### 👁 查看按钮

```python
def _on_view_clicked(self, subtitle_id: int):
    """跳转到字幕条的起始点"""
    subtitle = self._get_subtitle_by_id(subtitle_id)
    if subtitle:
        self.jump_to_position.emit(subtitle["start_ms"])
```

### ✏️ 编辑按钮

```python
def _on_edit_clicked(self, subtitle_id: int):
    """进入编辑模式，调整字幕条的前后区间"""
    # 弹出编辑对话框，允许调整开始时间和结束时间
    pass
```

### 🔒 锁定按钮

```python
def _on_lock_clicked(self, subtitle_id: int):
    """切换锁定状态"""
    subtitle = self._get_subtitle_by_id(subtitle_id)
    if subtitle:
        subtitle["locked"] = not subtitle["locked"]
        self._update_table()
```

---

## 编辑对话框

```
┌─ 编辑字幕 #1 ─────────────────────────────────────┐
│                                                     │
│  开始时间: [00:15.200]  [← 100ms] [100ms →]        │
│  结束时间: [00:18.400]  [← 100ms] [100ms →]        │
│                                                     │
│  时长: 3.2s                                         │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  [预览]  [取消]  [确定]                              │
└─────────────────────────────────────────────────────┘
```

---

## 信号定义

```python
# 发射
subtitle_selected = Signal(int)  # 字幕被选中 (start_ms)
subtitle_changed = Signal()      # 字幕数据变化
jump_to_position = Signal(int)   # 跳转到指定位置 (ms)
```

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `↑` | 选择上一条字幕 |
| `↓` | 选择下一条字幕 |
| `Enter` | 跳转到选中字幕的起始点 |
| `Delete` | 删除选中字幕（需确认） |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |

---

## 与音频波形区的联动

### 打轴信号

```python
# WaveformCard 发射打轴信号
subtitle_created = Signal(int, int)  # (start_ms, end_ms)

# TimelineCard 接收并添加到列表
def add_subtitle(self, start_ms: int, end_ms: int):
    """添加新字幕条"""
    subtitle = {
        "id": len(self._subtitles) + 1,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "locked": False,
    }
    self._subtitles.append(subtitle)
    self._update_table()
    self.subtitle_changed.emit()
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtWidgets | QTableWidget, QDockWidget, QDialog |
| PySide6.QtCore | Signal |
| chestnut_studio.utils.time_utils | 时间格式转换 |
