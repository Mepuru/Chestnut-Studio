# 时间轴列表卡片

> `chestnut_studio/ui/cards/timeline_card.py`
> `TimelineCard(QDockWidget)` — 显示已打轴的字幕列表。

---

## 职责

- 显示已打轴的字幕列表
- 提供查看、编辑、锁定、删除功能
- 支持撤销/重做操作
- 支持复制轴功能

---

## 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `subtitle_selected(col, start_ms)` | `int, int` | 字幕被选中（用于翻译面板） |
| `subtitle_changed()` | 无 | 字幕数据变化 |
| `jump_to_position(ms)` | `int` | 跳转到指定位置 |
| `edit_subtitle_requested(col, start_ms, end_ms)` | `int, int, int` | 请求编辑字幕（发射到波形图） |

---

## 设计理念

- 时间轴卡片**不负责打轴**，只负责**显示和管理**已打轴的字幕条
- 打轴在音频波形区通过快捷键完成
- 时间轴区显示打好轴的列表，提供查看、编辑、锁定功能

---

## 布局

```
┌─────────────────────────────────────────────┐
│  #  │ 开始时间 │ 结束时间 │ 时长 │ 操作      │
│─────┼──────────┼──────────┼──────┼───────────│
│  1  │ 00:15.2  │ 00:18.4  │ 3.2s │ 👁 ✏️ 🔒 │
│  2  │ 00:22.0  │ 00:23.8  │ 1.8s │ 👁 ✏️ 🔒 │
│  3  │ 00:25.6  │ 00:29.2  │ 3.6s │ 👁 ✏️ 🔒 │
│ ...                                         │
├─────────────────────────────────────────────┤
│  共 3 条  │  [撤销] [重做]  │  [全部锁定]     │
└─────────────────────────────────────────────┘
```

---

## 公有方法

### 字幕操作

| 方法 | 参数 | 说明 |
|------|------|------|
| `add_subtitle(start_ms, end_ms)` | `int, int` | 添加新字幕条 |
| `remove_subtitle(subtitle_id)` | `int` | 删除字幕条 |
| `get_subtitles()` | 无 | 获取所有字幕列表 |
| `jump_to_subtitle(subtitle_id)` | `int` | 跳转到指定字幕起始点 |

### 字幕编辑

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_subtitle_text(col, start_ms, text)` | `int, int, str` | 设置字幕文本 |
| `highlight_subtitle(col, start_ms)` | `int, int` | 高亮指定字幕行（翻译面板调用） |
| `apply_subtitle_edit(col, old_start, new_start, new_end)` | `int, int, int, int` | 应用字幕编辑结果 |

### 字幕导航

| 方法 | 参数 | 说明 |
|------|------|------|
| `get_next_subtitle(col, start_ms)` | `int, int` | 获取下一条字幕 |
| `get_prev_subtitle(col, start_ms)` | `int, int` | 获取上一条字幕 |

### 撤销/重做

| 方法 | 参数 | 说明 |
|------|------|------|
| `undo()` | 无 | 撤销操作 |
| `redo()` | 无 | 重做操作 |

---

## 用法示例

```python
from chestnut_studio.ui.cards.timeline_card import TimelineCard

# 创建卡片
timeline_card = TimelineCard()

# 连接信号
timeline_card.subtitle_selected.connect(self.on_subtitle_selected)
timeline_card.subtitle_changed.connect(self.on_subtitle_changed)
timeline_card.jump_to_position.connect(self.on_jump_to_position)
timeline_card.edit_subtitle_requested.connect(self.on_edit_subtitle_requested)

# 添加字幕
timeline_card.add_subtitle(1000, 3000)  # 1秒到3秒
timeline_card.add_subtitle(5000, 7000)  # 5秒到7秒

# 删除字幕
timeline_card.remove_subtitle(1)  # 删除ID为1的字幕

# 获取所有字幕
subtitles = timeline_card.get_subtitles()

# 跳转到字幕
timeline_card.jump_to_subtitle(1)  # 跳转到ID为1的字幕

# 设置字幕文本
timeline_card.set_subtitle_text(1, 1000, "你好")

# 高亮字幕
timeline_card.highlight_subtitle(1, 1000)

# 撤销/重做
timeline_card.undo()
timeline_card.redo()
```

---

## 复制轴功能

### 功能说明

底部工具栏提供复制轴功能：
- 源轨道选择（下拉框）
- 目标轨道选择（下拉框）
- 复制按钮

### 使用流程

1. 选择源轨道（如轨道 1）
2. 选择目标轨道（如轨道 2）
3. 点击复制按钮
4. 确认覆盖提示
5. 完成复制

### 注意事项

- 复制时会覆盖目标轨道的现有数据
- 需要用户确认后才执行复制
- 复制后自动刷新显示

---

## 交互操作

| 操作 | 功能 |
|------|------|
| `点击查看` | 跳转到字幕起始点 |
| `点击编辑` | 进入编辑模式，可视化调整区间 |
| `点击锁定` | 切换锁定状态 |
| `点击删除` | 删除字幕 |
| `双击行` | 跳转到起始点 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Delete` | 删除选中字幕 |

---

## 字幕颜色

| 颜色 | 条件 |
|------|------|
| 绿色 `#35545d` | 正常持续时间 |
| 粉色 `#FA8072` | 持续时间 > 4.5s |
| 红色 `#B22222` | 持续时间异常（< 100ms 或 > 8s） |
| 灰色 `#52525b` | 已锁定 |

---

## 字幕状态

### 锁定状态

- 锁定后字幕不可编辑
- 锁定后字幕颜色变灰
- 锁定状态保存在字幕数据中

### 编辑状态

- 点击编辑按钮进入编辑模式
- 编辑模式下可可视化调整区间
- 编辑完成后自动保存

---

## 注意事项

### 数据同步

- 字幕数据变化时发射 `subtitle_changed` 信号
- 波形图根据信号更新字幕叠加
- 翻译面板根据信号更新显示

### 性能考虑

- 大量字幕时使用虚拟滚动
- 避免频繁刷新表格
- 使用定时器节流更新

### 撤销/重做

- 撤销栈最多 100 步
- 使用浅拷贝隔离状态（SubtitleEntry 是不可变 NamedTuple）
- 每次操作前调用 `_push_undo()` 保存快照

---

## 依赖

- PySide6: `QDockWidget`, `QWidget`, `QTableWidget`, `QPushButton`
- chestnut_studio.core.subtitle: `SubtitleManager`
- chestnut_studio.utils.time_utils: `ms_to_time_str`
