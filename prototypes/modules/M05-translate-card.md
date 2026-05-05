# M05 — 翻译面板卡片

> `src/ui/cards/translate_card.py`　｜　Phase 4　｜　手动翻译文本面板

---

## 职责

- 显示当前选中的原始字幕文本
- 提供文本输入框供手动翻译
- 翻译结果保存到指定字幕轨道
- 无外部 API 依赖

---

## 类设计

```python
class TranslateCard(QDockWidget):
    """翻译面板卡片"""
    
    def __init__(self, parent=None):
        super().__init__("翻译", parent)
        self._current_col = 0
        self._current_time = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """初始化 UI"""
        # 原文显示区
        # 翻译输入区
        # 目标轨道选择
        # 操作按钮
        ...
    
    def show_subtitle(self, index: int, text: str):
        """显示选中的字幕原文
        
        Args:
            index: 字幕索引（时间点）
            text: 原始字幕文本
        """
        self._current_time = index
        self._original_label.setText(f'原文: "{text}"')
        self._translate_edit.setFocus()
    
    def save_translation(self):
        """保存翻译到指定轨道"""
        text = self._translate_edit.toPlainText().strip()
        if text and self._current_time > 0:
            target_col = self._target_combo.currentIndex()
            # 发射信号，由 MainWindow 转发给 TimelineCard
            self.translation_saved.emit(self._current_time, target_col, text)
    
    def clear_input(self):
        """清空输入"""
        self._translate_edit.clear()
```

---

## 内部组件

| 组件 | 类型 | 说明 |
|------|------|------|
| `_original_label` | QLabel | 显示原文 |
| `_translate_edit` | QTextEdit | 翻译输入框 |
| `_target_combo` | QComboBox | 目标轨道选择 (1~5) |
| `_save_btn` | QPushButton | 保存按钮 |
| `_clear_btn` | QPushButton | 清空按钮 |

---

## 布局

```
┌─ 🌐 翻译 ───────────────────────────────── [_][□][×] ┐
│  原文: "你好世界"                                      │
│ ┌─────────────────────────────────────────────────────┐│
│ │                                                     ││
│ │  请输入翻译...                                       ││
│ │                                                     ││
│ └─────────────────────────────────────────────────────┘│
│  保存至轨道 [3▾]              [清空] [保存]             │
└─────────────────────────────────────────────────────────┘
```

---

## 信号定义

```python
# 发射
translation_saved = Signal(int, int, str)  # (time_ms, target_col, text)
```

---

## 交互流程

```
1. 用户在 TimelineCard 选中字幕条
2. TimelineCard 发射 subtitle_selected(index, text)
3. MainWindow 转发给 TranslateCard
4. TranslateCard 显示原文，输入框获焦
5. 用户输入翻译文本
6. 点击保存 → 发射 translation_saved
7. MainWindow 转发给 TimelineCard
8. TimelineCard 写入 subtitleDict[target_col]
9. 刷新表格 + 波形覆盖
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtWidgets | QDockWidget, QTextEdit, QComboBox |
