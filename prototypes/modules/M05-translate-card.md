# M05 — 翻译面板卡片

> `src/ui/cards/translate_card.py`　｜　Phase 4　｜　手动翻译文本面板

---

## 职责

- 显示当前选中的字幕时间点
- 提供源语言和目标语言两个输入区
- 翻译结果保存到字幕数据
- 无外部 API 依赖

---

## 与时间轴系统的集成

### 数据流

```
┌─────────────┐    subtitle_selected    ┌─────────────┐    translation_saved    ┌─────────────┐
│  TimelineCard│ ──────────────────────→ │ TranslateCard│ ──────────────────────→ │  数据存储    │
│  （打轴）     │    (start_ms)           │ （翻译面板）  │    (source, target)     │  subtitle_data│
└─────────────┘                         └─────────────┘                         └─────────────┘
```

### 工作流程

1. 用户在 TimelineCard 中选中一个字幕时间点
2. TimelineCard 发射 `subtitle_selected(start_ms)` 信号
3. MainWindow 转发给 TranslateCard
4. TranslateCard 显示该时间点，输入框获焦
5. 用户在源语言区输入源语言文本
6. 用户在目标语言区输入目标语言文本
7. 点击保存 → 发射 `translation_saved(source, target)` 信号
8. MainWindow 转发给 TimelineCard
9. TimelineCard 写入 subtitle_data 对应时间点
10. 刷新波形覆盖

---

## 类设计

```python
class TranslateCard(QDockWidget):
    """翻译面板卡片"""
    
    # 信号
    translation_saved = Signal(str, str)  # 源语言文本, 目标语言文本
    
    def __init__(self, parent=None):
        super().__init__("翻译", parent)
        self._current_time = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """初始化 UI"""
        # 时间点显示区
        # 源语言输入区
        # 目标语言输入区
        # 操作按钮
        ...
    
    def show_subtitle(self, start_ms: int):
        """显示选中的字幕时间点
        
        Args:
            start_ms: 字幕开始时间 (ms)
        """
        self._current_time = start_ms
        self._time_label.setText(f'时间点: {self._ms_to_time(start_ms)}')
        
        # 加载已有的源语言和目标语言文本
        self._load_existing_translation(start_ms)
        
        # 源语言输入框获焦
        self._source_edit.setFocus()
    
    def save_translation(self):
        """保存翻译"""
        source = self._source_edit.toPlainText().strip()
        target = self._target_edit.toPlainText().strip()
        
        if self._current_time > 0 and (source or target):
            # 发射信号，由 MainWindow 转发给 TimelineCard
            self.translation_saved.emit(source, target)
    
    def clear_input(self):
        """清空输入"""
        self._source_edit.clear()
        self._target_edit.clear()
    
    def _load_existing_translation(self, start_ms: int):
        """加载已有的翻译"""
        # 从 subtitle_data 中加载已有的源语言和目标语言文本
        # 如果已有翻译，显示在输入框中
        pass
```

---

## 内部组件

| 组件 | 类型 | 说明 |
|------|------|------|
| `_time_label` | QLabel | 显示当前时间点 |
| `_source_label` | QLabel | "源语言" 标签 |
| `_source_edit` | QTextEdit | 源语言输入框 |
| `_target_label` | QLabel | "目标语言" 标签 |
| `_target_edit` | QTextEdit | 目标语言输入框 |
| `_save_btn` | QPushButton | 保存按钮 |
| `_clear_btn` | QPushButton | 清空按钮 |

---

## 布局

```
┌─ 🌐 翻译 ───────────────────────────────── [_][□][×] ┐
│  时间点: 00:15.200                                    │
│ ┌─────────────────────────────────────────────────────┐│
│ │  源语言                                             ││
│ │  ┌─────────────────────────────────────────────────┐││
│ │ │                                                 │││
│ │ │  请输入源语言...                                  │││
│ │ │                                                 │││
│ │ └─────────────────────────────────────────────────┘││
│ └─────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────┐│
│ │  目标语言                                           ││
│ │  ┌─────────────────────────────────────────────────┐││
│ │ │                                                 │││
│ │ │  请输入目标语言...                                │││
│ │ │                                                 │││
│ │ └─────────────────────────────────────────────────┘││
│ └─────────────────────────────────────────────────────┘│
│                                    [清空] [保存]       │
└─────────────────────────────────────────────────────────┘
```

---

## 信号定义

```python
# 发射
translation_saved = Signal(str, str)  # 源语言文本, 目标语言文本
```

---

## 交互流程

```
1. 用户在 TimelineCard 选中字幕时间点
2. TimelineCard 发射 subtitle_selected(start_ms)
3. MainWindow 转发给 TranslateCard
4. TranslateCard 显示时间点，加载已有翻译
5. 用户在源语言区输入源语言文本
6. 用户在目标语言区输入目标语言文本
7. 点击保存 → 发射 translation_saved(source, target)
8. MainWindow 转发给 TimelineCard
9. TimelineCard 写入 subtitle_data 对应时间点
10. 刷新波形覆盖
```

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 保存翻译并跳转到下一条 |
| `Ctrl+Shift+Enter` | 保存翻译并跳转到上一条 |
| `Tab` | 在源语言和目标语言输入框间切换 |
| `Escape` | 清空输入框 |

---

## 智能功能

### 自动填充

```python
def _load_existing_translation(self, start_ms: int):
    """自动填充已有的翻译"""
    if start_ms in self._subtitle_data:
        data = self._subtitle_data[start_ms]
        self._source_edit.setText(data.get("source", ""))
        self._target_edit.setText(data.get("target", ""))
    else:
        self._source_edit.clear()
        self._target_edit.clear()
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
