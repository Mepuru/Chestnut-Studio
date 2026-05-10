# Chestnut Studio — 性能优化与架构改进方案

> 针对字幕列表操作卡顿问题的根因分析、短期修复方案和长期架构改进规划

---

## 一、问题描述

当项目加载约 130 条字幕时，点击删除按钮会出现明显卡顿。字幕数量越多，卡顿越严重。

**复现路径**: 加载含 130+ 条字幕的项目 → 点击任意字幕的"删除"按钮 → 感受到可感知的延迟

---

## 二、瓶颈分析

### 2.1 删除操作的完整调用链

```
用户点击"删除"按钮
  │
  ├─► _push_undo()                           [timeline_card.py:698]
  │     ├─► copy.deepcopy(全部字幕数据)       ← 复制 130 条字幕的深拷贝
  │     └─► copy.deepcopy(锁定状态集合)       ← 可用浅拷贝替代
  │
  ├─► _subtitle_mgr.delete(col, start_ms)    [timeline_card.py:536]
  │     └─► dict.pop()                        ← O(1)，无问题
  │
  ├─► _update_table()                         [timeline_card.py:322]  ★ 主要瓶颈
  │     ├─► setRowCount(0)                     ← 销毁 130×9 = 1170 个 QTableWidgetItem
  │     ├─► 收集 + 排序全部字幕                ← O(n log n)
  │     └─► 重建 130 行，每行创建：
  │           ├─ 7 个 QTableWidgetItem         ← 编号/轨道/开始/结束/帧/时长/文本
  │           ├─ 1 个 QWidget + 4 个 QPushButton + 4 个信号连接  ← 操作按钮组
  │           └─ 9 次 setBackground            ← 行背景色
  │
  └─► subtitle_changed.emit()                 [timeline_card.py:539]
        └─► _sync_subtitle_overlay()           [main_window.py:768]
              └─► waveform_card._update_subtitle_overlay()  [waveform_card.py:1234]
                    ├─► removeItem() × 130      ← pyqtgraph 场景图更新
                    ├─► 重建 track_colors × 130  ← 每个字幕区域都重建 8 个 QColor
                    └─► addItem() × 130          ← 每个都查询 Y 轴范围 + 创建 PlotCurveItem
```

### 2.2 各环节耗时估算（130 条字幕）

| 环节 | 操作 | 预估耗时 | 占比 |
|------|------|----------|------|
| `_push_undo()` | deepcopy 全量字幕数据 | ~5ms | 5% |
| `_update_table()` — 销毁 | 1170 个 QTableWidgetItem 销毁 | ~10ms | 10% |
| `_update_table()` — 重建 | 1170 个 Item + 520 个 Button + 520 个信号连接 | ~50ms | 50% |
| 波形覆盖层重建 | 260 个 PlotCurveItem 移除/添加 + 场景图更新 | ~30ms | 30% |
| 其他 | 排序、颜色构建等 | ~5ms | 5% |
| **合计** | | **~100ms** | |

> 注：实际耗时因机器性能和字幕数量而异，130 条时约 80-150ms，可感知但不严重；500+ 条时会明显卡顿。

### 2.3 核心问题总结

| # | 问题 | 位置 | 严重度 |
|---|------|------|--------|
| 1 | 全量表格重建 | `_update_table()` 每次清空重建所有行 | **Critical** |
| 2 | 全量波形覆盖层重建 | `_update_subtitle_overlay()` 每次销毁重建所有 PlotCurveItem | **Critical** |
| 3 | 文本编辑触发波形重建 | `subtitle_changed` 信号不区分文本/时间变更 | **High** |
| 4 | 循环内重复构建 QColor | `_update_table()` 和 `_draw_subtitle_region()` 内循环 | **Medium** |
| 5 | locked_states 使用 deepcopy | tuple 组成的 set 可用浅拷贝 | **Medium** |
| 6 | get_next/get_prev 使用 sorted + index | 每次导航都排序 + 线性查找 | **Low** |
| 7 | 波形数据转为 Python list | numpy → list，14 倍内存开销 | **Low** |

---

## 三、架构层面的深层问题

性能问题只是表面症状。深入分析后发现以下架构债务：

### 3.1 数据变更没有通知机制

当前数据流是"手动同步"模式：

```
TimelineCard 持有 SubtitleManager
  ↓ 手动调用
_update_table()            ← 全量重建表格
  ↓ 手动信号
subtitle_changed           ← 粗粒度信号，不区分变更类型
  ↓ 手动调用
_update_subtitle_overlay() ← 全量重建波形覆盖层
```

每次数据变化，都要靠 UI 代码手动同步所有消费者。这导致了：
- 全量重建（性能问题）
- TranslateCard 通过隐式引用耦合数据
- 新增卡片需要改 8 处代码

### 3.2 撤销系统分裂为两套

| 系统 | 位置 | 状态 |
|------|------|------|
| 核心层撤销 | `SubtitleManager.push_undo/undo/redo` | **从未被调用（死代码）** |
| UI 层撤销 | `TimelineCard._push_undo/_undo/_redo` | 实际使用 |

UI 层撤销直接访问 `SubtitleManager._data`（私有属性），破坏封装：

```python
# timeline_card.py:719 — 直接替换私有属性
self._subtitle_mgr._data = data
```

### 3.3 数据类型缺乏类型安全

```python
# subtitle.py:8 — 内层 list 没有类型约束
SubtitleDict = dict[int, dict[int, list]]
# 实际结构: {col: {start_ms: [duration_ms, text]}}
# 但 subtitle[0] = "oops" 不会报错
```

### 3.4 代码重复

| 重复代码 | 出现次数 |
|----------|----------|
| 时间格式转换函数（`ms_to_srt_time` 等） | 2 处（`time_utils.py` 和 `subtitle_io.py` 各一份） |
| 轨道颜色 ComboBox 填充 | 7 处 |
| QPushButton 样式定义 | 17 处 |
| 轨道颜色索引钳制 `max(0, min(col-1, ...))` | 3 处 |

### 3.5 未声明的动态属性

| 属性 | 位置 | 问题 |
|------|------|------|
| `self._redo_state` | `subtitle.py:95` | 在 `undo()` 中赋值但 `__init__` 未声明 |
| `self._subtitle_full_data` | `waveform_card.py:1242` | 在 `update_subtitle_overlay_from_data()` 中赋值但 `__init__` 未声明 |

---

## 四、优化方案

### 方案 1：表格增量更新（P0）

**目标**: 删除操作只移除被删行，不重建整个表格。

**现状代码** (`timeline_card.py:526`):

```python
def _on_delete_single(self, col, start_ms):
    self._push_undo()
    self._subtitle_mgr.delete(col, start_ms)
    self._locked_states.discard((col, start_ms))
    self._update_table()          # ← 全量重建 130 行
    self.subtitle_changed.emit()
```

**优化思路**:

```
删除单条：
  1. 找到被删字幕对应的 table row（通过 UserRole 数据匹配）
  2. _table.removeRow(row)           ← 只删一行
  3. 更新后续行的编号（TableWidgetItem 重新 setText）
  4. subtitle_changed.emit()

删除多条：
  1. 收集所有要删除的 row index，从大到小排序
  2. 逐个 removeRow                  ← 避免索引偏移
  3. 重新编号剩余行
  4. subtitle_changed.emit()

编辑/锁定等其他操作：
  找到对应 row，只更新变化的单元格（setItem 替换而非全行重建）
```

**注意事项**:

- `QTableWidget.removeRow()` 会自动销毁该行的 Item 和 CellWidget，无需手动清理
- 删除行后需要更新后续行的编号列（第 0 列）
- 操作按钮的 lambda 捕获了 `col` 和 `start_ms`，行位置变化不影响功能（因为通过 `Qt.UserRole` 数据定位）
- 需要处理"选中行"和"滚动位置"的恢复逻辑

**预期收益**: 130 条字幕删除耗时从 ~100ms 降到 <10ms。

---

### 方案 2：波形覆盖层增量更新（P0）

**目标**: 维护 `(col, start_ms) → PlotCurveItem` 的映射，增删字幕时只操作对应的 item。

**现状代码** (`waveform_card.py:1234`):

```python
def _update_subtitle_overlay(self):
    # 销毁全部
    for item in self._subtitle_items:
        self._plot_widget.removeItem(item)
    self._subtitle_items.clear()
    # 重建全部
    for col in sorted(self._subtitle_full_data.keys(), reverse=True):
        for start_ms, subtitle in sub_dict.items():
            self._draw_subtitle_region(start_ms, end_ms, col)
```

**优化思路**:

新增增量方法，与全量重建共存：

```python
# 数据结构变更
self._subtitle_item_map: dict[tuple[int, int], pg.PlotCurveItem] = {}
# key = (col, start_ms), value = 对应的 PlotCurveItem

def add_subtitle_item(self, col, start_ms, end_ms):
    """增量添加单个字幕覆盖条"""
    item = self._create_subtitle_region_item(start_ms, end_ms, col)
    self._plot_widget.addItem(item)
    self._subtitle_item_map[(col, start_ms)] = item

def remove_subtitle_item(self, col, start_ms):
    """增量移除单个字幕覆盖条"""
    key = (col, start_ms)
    item = self._subtitle_item_map.pop(key, None)
    if item:
        self._plot_widget.removeItem(item)

def update_subtitle_item(self, col, old_start_ms, new_start_ms, new_end_ms):
    """更新单个字幕覆盖条（编辑场景）"""
    self.remove_subtitle_item(col, old_start_ms)
    self.add_subtitle_item(col, new_start_ms, new_end_ms)
```

**信号对接**:

```
TimelineCard 删除字幕 ──► MainWindow ──► waveform_card.remove_subtitle_item(col, start_ms)
TimelineCard 新增字幕 ──► MainWindow ──► waveform_card.add_subtitle_item(col, start_ms, end_ms)
TimelineCard 编辑字幕 ──► MainWindow ──► waveform_card.update_subtitle_item(...)
TimelineCard 批量操作 ──► MainWindow ──► waveform_card._update_subtitle_overlay()  # 全量重建兜底
```

**预期收益**: 删除操作的波形更新从 ~30ms 降到 <2ms。

---

### 方案 3：拆分 subtitle_changed 信号（P1）

**目标**: 文本编辑不触发波形覆盖层重建（波形区不显示文本）。

**现状**: 所有变更都走同一个 `subtitle_changed` 信号，导致纯文本修改也触发波形全量重建。

**优化思路**:

```python
# TimelineCard 中新增信号
class TimelineCard(QWidget):
    subtitle_changed = Signal()        # 保留，兼容旧逻辑（批量/兜底）
    subtitle_timing_changed = Signal(int, int, int, int, int)
    # 参数: (col, old_start, old_duration, new_start, new_duration)
    subtitle_text_changed = Signal(int, int)
    # 参数: (col, start_ms)
    subtitle_added = Signal(int, int, int)
    # 参数: (col, start_ms, duration_ms)
    subtitle_removed = Signal(int, int)
    # 参数: (col, start_ms)
```

**各操作的信号映射**:

| 操作 | 触发信号 | 波形层响应 | 表格响应 |
|------|----------|-----------|----------|
| 删除单条 | `subtitle_removed` | 移除对应 PlotCurveItem | removeRow |
| 新增字幕 | `subtitle_added` | 添加 PlotCurveItem | insertRow |
| 编辑区间 | `subtitle_timing_changed` | 更新 PlotCurveItem | 更新时间列 |
| 编辑文本 | `subtitle_text_changed` | **不触发** | 更新文本列 |
| 批量操作 | `subtitle_changed` | 全量重建 | 全量重建 |
| 撤销/重做 | `subtitle_changed` | 全量重建 | 全量重建 |

**预期收益**: 翻译面板中频繁的文本编辑不再触发波形重建，编辑体验更流畅。

---

### 方案 4：缓存 track_colors（P1）

**目标**: 将循环内重复构建的颜色列表提升为实例变量。

**现状问题**:

```python
# timeline_card.py:353 — 每次 _update_table() 都重建
track_colors_fg = [QColor(c) for c in TRACK_COLORS_HEX]  # 8 个 QColor

# timeline_card.py:407-411 — 每行循环内都重建
track_colors_bg = []
for c in TRACK_COLORS_HEX:
    qc = QColor(c)
    qc.setAlpha(30)
    track_colors_bg.append(qc)

# waveform_card.py:1271-1276 — 每个字幕区域都重建
track_colors = []
for hex_color in TRACK_COLORS_HEX:
    border = QColor(hex_color)
    fill = QColor(hex_color)
    fill.setAlpha(40)
    track_colors.append((border, fill))
```

**优化**:

```python
# 在 __init__ 或 showEvent 中计算一次
self._track_colors_fg = [QColor(c) for c in TRACK_COLORS_HEX]

self._track_colors_bg = []
for c in TRACK_COLORS_HEX:
    qc = QColor(c)
    qc.setAlpha(30)
    self._track_colors_bg.append(qc)

# waveform_card 中同理
self._track_overlay_colors = []
for hex_color in TRACK_COLORS_HEX:
    border = QColor(hex_color)
    fill = QColor(hex_color)
    fill.setAlpha(40)
    self._track_overlay_colors.append((border, fill))
```

**预期收益**: 减少 ~1040 次 QColor 对象创建（130 条 × 8 色），虽然单次开销小，但累积可观。

---

### 方案 5：优化 locked_states 拷贝（P1）

**目标**: `_locked_states` 是 `set[tuple[int, int]]`，tuple 不可变，可用浅拷贝。

**现状** (`timeline_card.py:700`):

```python
state = (
    copy.deepcopy(self._subtitle_mgr.data),   # 字典需要深拷贝
    copy.deepcopy(self._locked_states),        # ← set of tuple，浅拷贝即可
)
```

**优化**:

```python
state = (
    copy.deepcopy(self._subtitle_mgr.data),
    self._locked_states.copy(),  # 浅拷贝足够，tuple 是不可变的
)
```

**预期收益**: `_push_undo()` 耗时减少约 10-20%。

---

### 方案 6：get_next/get_prev 使用 bisect（P2）

**目标**: 替代 `sorted()` + `.index()` 的 O(n log n) + O(n) 组合。

**现状** (`timeline_card.py:877`):

```python
sorted_starts = sorted(sub_data.keys())     # O(n log n)
idx = sorted_starts.index(current_start_ms) # O(n)
```

**优化**:

```python
import bisect

def get_next_subtitle(self, col, current_start_ms):
    sub_data = self._subtitle_mgr.data.get(col, {})
    if not sub_data:
        return None
    keys = sorted(sub_data.keys())  # 如果数据已排序可缓存
    idx = bisect.bisect_left(keys, current_start_ms)
    if idx < len(keys) and keys[idx] == current_start_ms:
        if idx + 1 < len(keys):
            return (col, keys[idx + 1])
    return None
```

**更进一步**: 如果 `_subtitle_mgr` 内部维护每个轨道的排序键列表（在 add/delete 时通过 `bisect.insort` / `bisect` 删除维护），则 `get_next/get_prev` 可以直接查表，无需每次排序。

**预期收益**: 导航操作从 O(n log n) 降到 O(log n)，在字幕数量大时有明显改善。

---

### 方案 7：波形数据保持 numpy（P2）

**目标**: 避免 numpy → Python list 的转换，减少内存开销。

**现状** (`audio.py:46-57`):

```python
amplitude_list = list(map(int, vocal))      # 600K 个 Python int (~17MB)
time_list = [x * 1000 / framerate for x in range(nframes)]  # 600K 个 Python float (~17MB)
return time_list, amplitude_list
```

**优化**:

```python
# 直接返回 numpy 数组
amplitude = vocal.astype(np.int16)          # 600K 个 int16 (~1.2MB)
time = np.arange(nframes) * 1000 / framerate  # 600K 个 float64 (~4.8MB)
return time, amplitude
```

**注意**: pyqtgraph 的 `setData()` 原生支持 numpy 数组，无需额外转换。需要检查 `downsample_waveform()` 和 `compute_envelope_fast()` 等下游函数是否兼容 numpy 输入。

**预期收益**: 内存从 ~34MB 降到 ~6MB，加载速度提升，但对删除卡顿无直接影响。

---

### 方案 8：引入 SubtitleModel（长期架构改进）

**目标**: 在 UI 层创建 `SubtitleModel(QObject)` 作为数据和视图之间的桥梁，解决"数据变更没有通知机制"的根本问题。

**目标架构**:

```
SubtitleManager (core, 纯数据, 无 PySide6)
  ↓ 包装
SubtitleModel (ui, QObject, 信号源)
  ├─► TimelineCard    (表格视图)
  ├─► WaveformCard    (波形覆盖层)
  ├─► TranslateCard   (翻译面板)
  └─► 未来的新卡片...
```

**SubtitleModel 设计**:

```python
class SubtitleModel(QObject):
    """字幕数据的唯一信号源，管理数据变更和撤销"""

    # 细粒度变更信号
    entry_added = Signal(int, int, int)           # col, start_ms, duration_ms
    entry_removed = Signal(int, int)              # col, start_ms
    entry_moved = Signal(int, int, int, int, int) # col, old_start, old_dur, new_start, new_dur
    entry_text_changed = Signal(int, int, str)    # col, start_ms, text
    entry_timing_changed = Signal(int, int, int, int)  # col, start_ms, old_dur, new_dur
    batch_changed = Signal()                      # 批量操作后（撤销/重做/导入）

    # 查询接口
    def get_entry(self, col, start_ms) -> SubtitleEntry | None
    def get_all_entries(self) -> SubtitleDict
    def get_entries_in_range(self, col, start_ms, end_ms) -> list

    # 变更接口（内部管理撤销栈）
    def add_entry(self, col, start_ms, duration_ms, text) -> None
    def remove_entry(self, col, start_ms) -> None
    def update_text(self, col, start_ms, text) -> None
    def update_timing(self, col, start_ms, new_start, new_end) -> None

    # 撤销/重做（统一管理，包含 locked_states）
    def undo(self) -> bool
    def redo(self) -> bool
```

**这个方案能同时解决的问题**:

| 问题 | 怎么解决 |
|------|----------|
| 删除卡顿 | `entry_removed` 信号只携带一个 (col, start_ms)，各视图增量更新 |
| 文本编辑触发波形重建 | `entry_text_changed` 信号独立，波形层不连接它 |
| TranslateCard 隐式耦合 | 不再需要直接数据引用，通过信号同步 |
| 撤销系统分裂 | 统一到 SubtitleModel 内部 |
| 新增卡片要改 8 处 | 新卡片只需连接 Model 的信号 |
| FPS 散落多处 | 可扩展到 Model 或单独的 ProjectState |

**工作量**: 新增 `subtitle_model.py` + 重写信号连接，预计 2-3 天。

**建议**: 在 Phase A（小优化）完成后实施，作为 Phase B 的核心任务。

---

### 方案 9：QAbstractTableModel 重构（远期）

**目标**: 用 Qt Model/View 架构替代 item-based 的 QTableWidget。

**优势**:

- Qt 自动管理视图刷新，天然支持增量更新
- `dataChanged` 信号可以精确到单个单元格
- `beginRemoveRows/endRemoveRows` 让 Qt 优化渲染
- 分离数据和展示，代码更清晰

**工作量**:

- 新增 `SubtitleTableModel(QAbstractTableModel)` 类
- 重写 `TimelineCard` 的表格交互逻辑
- 确保排序、筛选、选择等功能正常
- 预计 2-3 天工作量

**建议**: 与方案 8（SubtitleModel）配合实施，SubtitleModel 负责数据和信号，SubtitleTableModel 负责表格视图适配。

---

## 五、实施计划

### Phase A：数据类型 + 小优化（1 天）

改动小，立竿见影，无风险：

| 任务 | 改动文件 | 说明 |
|------|----------|------|
| `SubtitleEntry` NamedTuple 替代 bare list | `subtitle.py` 及所有调用方 | 类型安全 |
| 缓存 track_colors 到实例变量 | `timeline_card.py`, `waveform_card.py` | 减少重复分配 |
| `locked_states` 用 `set.copy()` 替代 `deepcopy` | `timeline_card.py` | undo 快 10-20% |
| 删除 SubtitleManager 中未使用的 undo 代码 | `subtitle.py` | 消除死代码陷阱 |
| 修复 `_redo_state` 和 `_subtitle_full_data` 未声明 | `subtitle.py`, `waveform_card.py` | 消除隐患 |
| `subtitle_io.py` 改为从 `time_utils.py` 导入 | `subtitle_io.py` | 消除代码重复 |

### Phase B：引入 SubtitleModel（2-3 天）

核心架构改进：

| 任务 | 改动文件 | 说明 |
|------|----------|------|
| 新建 SubtitleModel | 新增 `ui/subtitle_model.py` | 数据和信号的唯一来源 |
| 统一撤销系统 | `subtitle_model.py` | 替代 TimelineCard 中的撤销逻辑 |
| 替换 TimelineCard 直接操作 | `timeline_card.py` | 通过 Model 接口操作数据 |
| 替换 TranslateCard 直接引用 | `translate_card.py`, `main_window.py` | 通过 Model 信号同步 |
| MainWindow 信号重新连接 | `main_window.py` | 从 Model 接信号 |

### Phase C：增量更新（1-2 天）

在 Model 信号基础上实现：

| 任务 | 改动文件 | 说明 |
|------|----------|------|
| 表格增量更新 | `timeline_card.py` | 基于 `entry_removed` / `entry_added` 信号 |
| 波形覆盖层增量更新 | `waveform_card.py` | 基于 Model 的细粒度信号 |
| 文本编辑不触发波形重建 | `main_window.py` | `entry_text_changed` 不连接波形层 |

### Phase D：代码整理（1 天）

| 任务 | 改动文件 | 说明 |
|------|----------|------|
| 提取 ComboBox 填充工具函数 | `track_config.py` | 7 处重复 → 1 个函数 |
| 统一按钮样式 | 各 card 文件 | 17 处重复 → 共享常量 |
| 补充测试 | `tests/` | SubtitleIO、undo、time_utils |

---

## 六、验证方法

### 6.1 性能测试

```python
import time

# 在 _on_delete_single 中计时
start = time.perf_counter()
self._update_table()
elapsed = time.perf_counter() - start
print(f"_update_table: {elapsed*1000:.1f}ms")
```

### 6.2 测试矩阵

| 场景 | 字幕数量 | 目标耗时 |
|------|----------|----------|
| 删除单条 | 130 条 | < 20ms |
| 删除单条 | 500 条 | < 50ms |
| 批量删除 10 条 | 130 条 | < 30ms |
| 文本编辑 | 130 条 | < 10ms（不触发波形重建） |
| 撤销/重做 | 130 条 | < 50ms |

### 6.3 回归测试

```bash
# 运行所有测试确保无回归
uv run pytest tests/ -v

# 代码检查
uv run ruff check chestnut_studio/
```

---

## 七、附录：相关代码文件

| 文件 | 职责 |
|------|------|
| `chestnut_studio/ui/cards/timeline_card.py` | 时间轴列表，表格管理，删除/撤销逻辑 |
| `chestnut_studio/ui/cards/waveform_card.py` | 波形显示，字幕覆盖层绘制 |
| `chestnut_studio/ui/cards/translate_card.py` | 翻译面板，字幕文本编辑 |
| `chestnut_studio/ui/main_window.py` | 信号连接中心 |
| `chestnut_studio/core/subtitle.py` | 字幕数据模型 |
| `chestnut_studio/core/audio.py` | 波形数据加载 |
| `chestnut_studio/core/track_config.py` | 轨道颜色配置 |
| `chestnut_studio/utils/time_utils.py` | 时间格式转换（权威来源） |
| `chestnut_studio/core/subtitle_io.py` | 字幕导入导出（应引用 time_utils） |
