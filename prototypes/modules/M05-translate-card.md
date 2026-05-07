# M05 — 翻译面板卡片

> `chestnut_studio/ui/cards/translate_card.py`　｜　Phase 4　｜　填写源语言和目标语言

---

## 职责

- 显示当前选中的字幕时间点
- 提供源语言和目标语言两个输入区
- 保存翻译内容到字幕数据
- 无外部 API 依赖

---

## 设计理念

### 核心概念

翻译面板负责**填写内容**，不负责打轴。

- **时间轴卡片**：负责打轴（在音频波形区完成）
- **翻译面板**：负责填写源语言和目标语言内容

### 工作流程

```
1. 用户在时间轴卡片中选中一条字幕
2. 翻译面板显示该字幕的时间点
3. 用户在源语言区输入源语言文本
4. 用户在目标语言区输入目标语言文本
5. 点击保存，内容写入字幕数据
```

### 数据流

```
┌─────────────┐    subtitle_selected    ┌─────────────┐
│ TimelineCard │ ──────────────────────→ │ TranslateCard│
│ （时间轴）   │    (start_ms)           │ （翻译面板）  │
└─────────────┘                         └─────────────┘
                                              │
                                              ▼
┌─────────────┐    translation_saved    ┌─────────────┐
│  数据存储    │ ←───────────────────── │ TranslateCard│
│ subtitle_data│    (source, target)     │ （翻译面板）  │
└─────────────┘                         └─────────────┘
```

---

## 类设计

```python
class TranslateCard(QDockWidget):
    """翻译面板卡片"""
    
    # 信号
    translation_saved = Signal(int, str, str)  # (start_ms, source, target)
    
    def __init__(self, parent=None):
        super().__init__("翻译", parent)
        self._current_start_ms = 0
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
        self._current_start_ms = start_ms
        self._time_label.setText(f'时间点: {self._ms_to_time(start_ms)}')
        
        # 加载已有的源语言和目标语言文本
        self._load_existing_translation(start_ms)
        
        # 源语言输入框获焦
        self._source_edit.setFocus()
    
    def save_translation(self):
        """保存翻译"""
        source = self._source_edit.toPlainText().strip()
        target = self._target_edit.toPlainText().strip()
        
        if self._current_start_ms > 0 and (source or target):
            # 发射信号，保存到字幕数据
            self.translation_saved.emit(self._current_start_ms, source, target)
    
    def clear_input(self):
        """清空输入"""
        self._source_edit.clear()
        self._target_edit.clear()
```

---

## UI 布局

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

## 信号定义

```python
# 发射
translation_saved = Signal(int, str, str)  # (start_ms, source, target)
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

## 与时间轴卡片的联动

### 选中字幕

```python
# TimelineCard 发射选中信号
subtitle_selected = Signal(int)  # start_ms

# TranslateCard 接收并显示
def show_subtitle(self, start_ms: int):
    """显示选中的字幕时间点"""
    self._current_start_ms = start_ms
    self._time_label.setText(f'时间点: {self._ms_to_time(start_ms)}')
    self._load_existing_translation(start_ms)
    self._source_edit.setFocus()
```

### 保存翻译

```python
# TranslateCard 发射保存信号
translation_saved = Signal(int, str, str)  # (start_ms, source, target)

# 数据存储接收并保存
def save_translation(self, start_ms: int, source: str, target: str):
    """保存翻译到字幕数据"""
    if start_ms in self._subtitle_data:
        self._subtitle_data[start_ms]["source"] = source
        self._subtitle_data[start_ms]["target"] = target
```

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
