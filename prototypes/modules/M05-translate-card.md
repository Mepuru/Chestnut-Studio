# M05 — 翻译面板卡片

> `src/ui/cards/translate_card.py`　｜　Phase 4　｜　手动翻译文本面板

---

## 职责

- 显示当前选中的源轴字幕文本
- 提供文本输入框供手动翻译
- 翻译结果保存到译文轴（轴2）
- 无外部 API 依赖

---

## 与双轴系统的集成

### 数据流

```
┌─────────────┐    subtitle_selected    ┌─────────────┐    translation_saved    ┌─────────────┐
│  TimelineCard│ ──────────────────────→ │ TranslateCard│ ──────────────────────→ │  TimelineCard│
│  (源轴)      │    (col=1, text)        │             │    (text)               │  (译文轴)    │
└─────────────┘                         └─────────────┘                         └─────────────┘
```

### 工作流程

1. 用户在 TimelineCard 中选中源轴（轴1）的字幕条
2. TimelineCard 发射 `subtitle_selected(col=1, text)` 信号
3. MainWindow 转发给 TranslateCard
4. TranslateCard 显示原文，输入框获焦
5. 用户输入翻译文本
6. 点击保存 → 发射 `translation_saved(text)` 信号
7. MainWindow 转发给 TimelineCard
8. TimelineCard 写入译文轴（轴2）的对应时间点
9. 刷新表格 + 波形覆盖

---

## 类设计

```python
class TranslateCard(QDockWidget):
    """翻译面板卡片"""
    
    # 信号
    translation_saved = Signal(str)  # 翻译文本保存
    
    def __init__(self, parent=None):
        super().__init__("翻译", parent)
        self._current_time = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """初始化 UI"""
        # 原文显示区
        # 翻译输入区
        # 操作按钮
        ...
    
    def show_subtitle(self, col: int, text: str):
        """显示选中的字幕原文
        
        Args:
            col: 字幕列（1=源轴，2=译文轴）
            text: 字幕文本
        """
        # 只显示源轴的字幕
        if col == 1:
            self._current_time = self._get_current_time()
            self._original_label.setText(f'原文: "{text}"')
            self._translate_edit.setFocus()
            # 如果译文轴已有翻译，显示在输入框中
            existing = self._get_translation(self._current_time)
            if existing:
                self._translate_edit.setText(existing)
            else:
                self._translate_edit.clear()
    
    def save_translation(self):
        """保存翻译到译文轴"""
        text = self._translate_edit.toPlainText().strip()
        if text and self._current_time > 0:
            # 发射信号，由 MainWindow 转发给 TimelineCard
            self.translation_saved.emit(text)
    
    def clear_input(self):
        """清空输入"""
        self._translate_edit.clear()
```

---

## 内部组件

| 组件 | 类型 | 说明 |
|------|------|------|
| `_original_label` | QLabel | 显示源轴原文 |
| `_translate_edit` | QTextEdit | 翻译输入框 |
| `_save_btn` | QPushButton | 保存按钮 |
| `_clear_btn` | QPushButton | 清空按钮 |
| `_sync_indicator` | QLabel | 显示同步状态 |

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
│  保存至译文轴 (轴2)            [清空] [保存]             │
└─────────────────────────────────────────────────────────┘
```

---

## 信号定义

```python
# 发射
translation_saved = Signal(str)  # 翻译文本
```

---

## 交互流程

```
1. 用户在 TimelineCard 选中源轴（轴1）字幕条
2. TimelineCard 发射 subtitle_selected(1, text)
3. MainWindow 转发给 TranslateCard
4. TranslateCard 显示原文，输入框获焦
5. 用户输入翻译文本
6. 点击保存 → 发射 translation_saved(text)
7. MainWindow 转发给 TimelineCard
8. TimelineCard 写入译文轴（轴2）对应时间点
9. 刷新表格 + 波形覆盖
```

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 保存翻译并跳转到下一条 |
| `Ctrl+Shift+Enter` | 保存翻译并跳转到上一条 |
| `Escape` | 清空输入框 |

---

## 智能功能

### 自动填充

```python
def _auto_fill_existing_translation(self, time_ms: int):
    """自动填充已有的翻译"""
    if time_ms in self._axis2_data:
        _, text = self._axis2_data[time_ms]
        self._translate_edit.setText(text)
    else:
        self._translate_edit.clear()
```

### 翻译记忆

```python
def _load_translation_memory(self):
    """加载翻译记忆（常用翻译）"""
    # 从历史翻译中提取常用翻译对
    # 用于自动补全建议
    pass
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtWidgets | QDockWidget, QTextEdit |
| PySide6.QtCore | Signal |
