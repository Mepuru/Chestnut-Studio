# Chestnut Studio — 待办事项

> 已知问题和待优化项

---

## Phase 3 — 打轴核心 已知问题

### 🔴 高优先级

#### 1. 选轴拖动跟手不顺畅

**问题描述**：Shift+左键拖动创建轴时，鼠标移动会有明显卡顿，跟不上鼠标移动。

**根本原因**：`_highlight_drag_selection` 方法性能问题

```python
def _highlight_drag_selection(self):
    """高亮拖动选择的单元格"""
    # 问题：每次鼠标移动都遍历所有 200×4 = 800 个单元格
    for row in range(VISIBLE_ROWS):
        for col in range(NUM_COLUMNS):
            item = self._table.item(row, col)
            if item:
                item.setSelected(False)  # O(n) 操作
```

**影响范围**：每次 `mouseMoveEvent` 触发时执行，鼠标移动越快触发越频繁

**修复方案**：
- 方案A：只清除上一次高亮的单元格，而不是全部清除
- 方案B：使用独立的高亮层，不依赖 `setSelected`
- 方案C：使用 `QPainter` 自定义绘制选区

---

#### 2. 拖动时会卡住

**问题描述**：Shift+左键/右键拖动时，偶尔会出现卡住不动的情况。

**根本原因**：
1. `_highlight_drag_selection` 的 O(n) 操作阻塞了事件循环
2. 防抖定时器 `_refresh_timer` (16ms) 与鼠标事件冲突
3. `_refresh_display` 被频繁调用，每次都要清空并重绘所有单元格

**影响范围**：拖动操作时

**修复方案**：
- 拖动时禁用防抖定时器
- 拖动时不调用 `_refresh_display`，只更新高亮状态
- 拖动结束后再统一刷新

---

#### 3. 滚动时轴颜色跟着跑

**问题描述**：鼠标滚轮滚动后，轴的颜色位置会发生偏移，视觉上像是"跟着跑"。

**根本原因**：`_render_subtitle` 和 `_render_axes` 的渲染顺序问题

```python
def _refresh_display(self):
    # 1. 清空所有单元格
    # 2. 渲染字幕条（会使用 setSpan 合并单元格）
    for col, sub_data in self._subtitle_mgr.data.items():
        self._render_subtitle(col, start, delta, text)
    
    # 3. 渲染轴（在字幕条之上）
    self._render_axes()  # 问题：setSpan 后的单元格状态不确定
```

**具体问题**：
1. `_render_subtitle` 使用 `setSpan` 合并单元格
2. 合并后的单元格，只有左上角的 item 有效
3. `_render_axes` 尝试在合并区域的其他行设置颜色，但这些行的 item 可能是无效的
4. 滚动时 `clearSpans` 没有被正确调用，导致合并状态残留

**修复方案**：
- 在 `_refresh_display` 开始时调用 `self._table.clearSpans()`
- 或者重构渲染逻辑，先渲染轴，再渲染字幕条

---

### 🟡 中优先级

#### 4. 轴创建后无法立即看到效果

**问题描述**：Shift+左键拖动创建轴后，需要滚动一下才能看到轴的颜色。

**根本原因**：`_create_axis_from_selection` 调用后没有立即刷新显示

**修复方案**：在 `_table_mouse_release` 中创建轴后调用 `_refresh_display()`

---

#### 5. 轴名称显示不完整

**问题描述**：轴名称（如"轴1-1"）只在第一行显示，但如果第一行被字幕条覆盖，名称就看不到。

**根本原因**：`_render_axes` 中轴名称的显示逻辑

```python
if logical_row == min_row:
    item.setText(name)  # 问题：可能被字幕条覆盖
```

**修复方案**：
- 轴名称应该显示在轴区域的第一个空白行
- 或者使用 tooltip 显示轴名称

---

### 🟢 低优先级

#### 6. 多列轴的颜色不一致

**问题描述**：当轴跨越多列时，每一列的轴颜色是独立的，没有视觉关联。

**根本原因**：当前实现中，每个轴只属于一列

**修复方案**：支持跨列轴，使用相同的颜色和名称

---

## 待办清单

- [ ] 优化 `_highlight_drag_selection` 性能
- [ ] 修复滚动时轴颜色偏移问题
- [ ] 添加 `clearSpans()` 到 `_refresh_display`
- [ ] 拖动时禁用防抖定时器
- [ ] 轴名称显示优化
- [ ] 支持跨列轴

---

*最后更新：2026-05-06*
