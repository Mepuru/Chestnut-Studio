# 翻译面板卡片

> `chestnut_studio/ui/cards/translate_card.py`
> `TranslateCard(BaseCard)` — 翻译面板，编辑当前轨道的字幕文本。

---

## 职责

- 编辑当前轨道的字幕文本
- 支持快速跳转（Ctrl+Enter 保存并跳转下一条）
- 高亮时间轴对应行
- 支持多轨道切换

---

## 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `text_saved(col, start_ms, text)` | `int, int, str` | 文本保存时发射 |
| `jump_to_next(col, start_ms)` | `int, int` | 请求跳转到下一条 |
| `jump_to_prev(col, start_ms)` | `int, int` | 请求跳转到上一条 |
| `editing_subtitle(col, start_ms)` | `int, int` | 正在编辑的字幕（用于高亮时间轴） |

---

## 布局

```
┌─ 翻译 ─────────────────────────────────────────────┐
│ 0:01.00    轨道 2 (绿色)    Ctrl+Enter: 保存/下一条 │
│ ┌─────────────────────────────────────────────────┐│
│ │ ┌─────────────────────────────────────────────┐││
│ │ │ こんにちは世界                              │││
│ │ └─────────────────────────────────────────────┘││
│ └─────────────────────────────────────────────────┘│
│                           [清空] [上一条] [保存/下一条] │
└─────────────────────────────────────────────────────┘
```

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 保存并跳转到下一条字幕 |
| `Shift+Enter` | 跳转到上一条字幕 |
| `Enter` | 换行（文本框内） |

---

## 公有方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `show_subtitle(col, start_ms)` | `int, int` | 显示选中的字幕 |
| `save_text()` | 无 | 保存当前文本 |
| `clear_input()` | 无 | 清空输入框 |
| `set_subtitle_data(data)` | `dict` | 设置字幕数据引用 |

---

## 用法示例

```python
from chestnut_studio.ui.cards.translate_card import TranslateCard

# 创建卡片
translate_card = TranslateCard()

# 连接信号
translate_card.text_saved.connect(self.on_text_saved)
translate_card.jump_to_next.connect(self.on_jump_to_next)
translate_card.jump_to_prev.connect(self.on_jump_to_prev)
translate_card.editing_subtitle.connect(self.on_editing_subtitle)

# 设置字幕数据
translate_card.set_subtitle_data(subtitle_data)

# 显示字幕
translate_card.show_subtitle(1, 1000)  # 显示列1，起始1000ms的字幕

# 保存文本
translate_card.save_text()

# 清空输入框
translate_card.clear_input()
```

---

## 设计理念

### 轨道独立存储

- 每个轨道只存储一种语言（不是源语言+目标语言）
- 轨道 1：原文
- 轨道 2：翻译
- 轨道 3：其他语言
- 轨道 4：备注

### 翻译工作流

1. 轨道 1 打轴填写源语言
2. 复制到轨道 2
3. 在轨道 2 修改为目标语言
4. 导出多轨道 ASS 文件

### 高亮联动

- 选中字幕时，时间轴表格会高亮对应行
- 编辑字幕时，时间轴表格会高亮对应行
- 保存后自动跳转到下一条

---

## 轨道切换

### 轨道选择

- 顶部显示当前轨道号和颜色
- 轨道颜色：
  - 轨道 1：白色
  - 轨道 2：绿色
  - 轨道 3：黄色
  - 轨道 4：蓝色

### 切换方式

- 通过时间轴列表选中字幕自动切换
- 通过快捷键 `1`-`4` 切换轨道

---

## 文本编辑

### 编辑区域

- 多行文本框
- 支持换行
- 支持复制/粘贴

### 保存逻辑

- `Ctrl+Enter` 保存并跳转下一条
- `Shift+Enter` 跳转上一条（不保存）
- 点击保存按钮保存

### 跳转逻辑

- 保存后自动跳转到下一条字幕
- 跳转时自动更新时间轴高亮
- 跳转时自动更新播放位置

---

## 注意事项

### 数据同步

- 文本保存时发射 `text_saved` 信号
- 时间轴列表根据信号更新字幕文本
- 波形图根据信号更新字幕叠加

### 高亮联动

- 编辑字幕时发射 `editing_subtitle` 信号
- 时间轴列表根据信号高亮对应行
- 高亮行自动滚动到可见区域

### 性能考虑

- 大量字幕时避免频繁刷新
- 使用定时器节流更新
- 避免重复保存相同文本

---

## 依赖

- PySide6: `QDockWidget`, `QWidget`, `QTextEdit`, `QPushButton`
- chestnut_studio.utils.time_utils: `ms_to_time_str`
