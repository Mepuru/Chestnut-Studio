# Issue #3: 拖动时会卡住

**状态**: ✅ 已解决  
**优先级**: 高  
**创建日期**: 2026-05-06  
**解决日期**: 2026-05-06  
**标签**: `bug` `performance` `timeline`

---

## 问题描述

Shift+左键/右键拖动时，偶尔会出现卡住不动的情况。

## 重现步骤

1. 打开视频
2. 在时间轴卡片中，按住 Shift+左键快速拖动
3. 观察拖动过程中的响应

## 预期行为

拖动过程应该流畅，不会出现卡住的情况。

## 实际行为

拖动过程中偶尔会出现卡住不动的情况。

## 根本原因

1. `_highlight_drag_selection` 的 O(n) 操作阻塞了事件循环
2. 防抖定时器 `_refresh_timer` (16ms) 与鼠标事件冲突
3. `_refresh_display` 被频繁调用，每次都要清空并重绘所有单元格

## 修复方案

### 方案A：拖动时禁用防抖（推荐）

```python
def _table_mouse_press(self, event):
    if modifiers & Qt.ShiftModifier:
        self._shift_left_dragging = True
        self._refresh_timer.stop()  # 拖动时禁用防抖
        ...

def _table_mouse_release(self, event):
    if self._shift_left_dragging:
        self._shift_left_dragging = False
        self._refresh_display()  # 拖动结束后统一刷新
        ...
```

### 方案B：拖动时不调用 _refresh_display

在 `_highlight_drag_selection` 中只更新高亮状态，不调用 `_refresh_display`。

## 相关文件

- `chestnut_studio/ui/cards/timeline_card.py` - `_table_mouse_press`, `_table_mouse_release` 方法

---

*最后更新: 2026-05-06*
