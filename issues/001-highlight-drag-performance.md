# Issue #1: 选轴拖动跟手不顺畅

**状态**: 🔴 待解决  
**优先级**: 高  
**创建日期**: 2026-05-06  
**标签**: `bug` `performance` `timeline`

---

## 问题描述

Shift+左键拖动创建轴时，鼠标移动会有明显卡顿，跟不上鼠标移动。

## 重现步骤

1. 打开视频
2. 在时间轴卡片中，按住 Shift+左键拖动
3. 观察鼠标移动时的响应

## 预期行为

鼠标移动时，选区应该实时跟随，流畅无卡顿。

## 实际行为

鼠标移动时，选区更新有明显延迟，拖动不顺畅。

## 根本原因

`_highlight_drag_selection` 方法性能问题：

```python
def _highlight_drag_selection(self):
    """高亮拖动选择的单元格"""
    # 问题：每次鼠标移动都遍历所有 200×4 = 800 个单元格
    for row in range(VISIBLE_ROWS):
        for col in range(NUM_COLUMNS):
            item = self._table.item(row, col)
            if item:
                item.setSelected(False)  # O(n) 操作，每次鼠标移动都执行
```

**影响范围**：每次 `mouseMoveEvent` 触发时执行，鼠标移动越快触发越频繁

## 修复方案

### 方案A：增量更新（推荐）
只清除上一次高亮的单元格，而不是全部清除：

```python
def __init__(self):
    self._last_highlighted_cells = set()  # 记录上次高亮的单元格

def _highlight_drag_selection(self):
    # 只清除上次高亮的单元格
    for row, col in self._last_highlighted_cells:
        item = self._table.item(row - self._scroll_offset, col)
        if item:
            item.setSelected(False)
    
    # 高亮当前选中的单元格
    self._last_highlighted_cells = set()
    for logical_row, col in self._drag_selected_cells:
        vis_row = logical_row - self._scroll_offset
        if 0 <= vis_row < VISIBLE_ROWS:
            item = self._table.item(vis_row, col)
            if item:
                item.setSelected(True)
                self._last_highlighted_cells.add((logical_row, col))
```

### 方案B：自定义绘制
使用 `QPainter` 自定义绘制选区，不依赖 `setSelected`。

## 相关文件

- `chestnut_studio/ui/cards/timeline_card.py` - `_highlight_drag_selection` 方法

---

*最后更新: 2026-05-06*
