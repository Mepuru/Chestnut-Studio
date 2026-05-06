# Issue #2: 滚动时轴颜色跟着跑

**状态**: ✅ 已解决  
**优先级**: 高  
**创建日期**: 2026-05-06  
**解决日期**: 2026-05-06  
**标签**: `bug` `rendering` `timeline`

---

## 问题描述

鼠标滚轮滚动后，轴的颜色位置会发生偏移，视觉上像是"跟着跑"。

## 重现步骤

1. 打开视频
2. 创建一个轴（Shift+左键拖动）
3. 用鼠标滚轮上下滚动
4. 观察轴的颜色位置

## 预期行为

滚动时，轴的颜色应该保持在原来的时间位置不变。

## 实际行为

滚动后，轴的颜色位置会发生偏移，视觉上像是"跟着跑"。

## 根本原因

`_render_subtitle` 和 `_render_axes` 的渲染顺序问题：

```python
def _refresh_display(self):
    # 1. 清空所有单元格
    for row in range(VISIBLE_ROWS):
        for col in range(NUM_COLUMNS):
            item = self._table.item(row, col)
            if item:
                item.setText("")
                item.setBackground(QBrush(QColor("#0f0f14")))
    
    # 2. 渲染字幕条（会使用 setSpan 合并单元格）
    for col, sub_data in self._subtitle_mgr.data.items():
        for start in sorted(sub_data):
            self._render_subtitle(col, start, delta, text)  # 调用 setSpan
    
    # 3. 渲染轴（在字幕条之上）
    self._render_axes()  # 问题：setSpan 后的单元格状态不确定
```

**问题分析**：
1. `_render_subtitle` 使用 `setSpan` 合并单元格
2. 合并后的单元格，只有左上角的 item 有效
3. `_render_axes` 尝试在合并区域的其他行设置颜色，但这些行的 item 可能是无效的
4. 滚动时 `clearSpans` 没有被正确调用，导致合并状态残留

## 修复方案

### 方案A：添加 clearSpans（推荐）
在 `_refresh_display` 开始时调用 `self._table.clearSpans()`：

```python
def _refresh_display(self):
    self._table.blockSignals(True)
    
    # 清除所有合并状态
    self._table.clearSpans()  # 新增
    
    # 清空所有单元格
    for row in range(VISIBLE_ROWS):
        for col in range(NUM_COLUMNS):
            item = self._table.item(row, col)
            if item:
                item.setText("")
                item.setBackground(QBrush(QColor("#0f0f14")))
    ...
```

### 方案B：重构渲染顺序
先渲染轴，再渲染字幕条，避免 `setSpan` 影响轴的渲染。

## 相关文件

- `chestnut_studio/ui/cards/timeline_card.py` - `_refresh_display` 方法

---

*最后更新: 2026-05-06*
