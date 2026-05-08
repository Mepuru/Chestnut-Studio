# 卡片组件

> `chestnut_studio/ui/cards/` 下各卡片组件的接口、信号和设计说明。
> 所有卡片继承 `QDockWidget`，支持拖拽、停靠、浮动。

---

## 模块概览

| 模块 | 文件 | 职责 |
|------|------|------|
| [视频播放卡片](player_card.md) | `player_card.py` | 视频渲染、播放控制、AB 循环 |
| [音频波形卡片](waveform_card.md) | `waveform_card.py` | 波形显示、打轴操作、缩放平移 |
| [时间轴列表卡片](timeline_card.md) | `timeline_card.py` | 字幕列表显示、编辑、锁定 |
| [翻译面板卡片](translate_card.md) | `translate_card.py` | 字幕文本编辑、快速跳转 |

---

## 设计原则

### 1. 继承 QDockWidget

所有卡片继承 `QDockWidget`：

```python
class PlayerCard(QDockWidget):
    """视频播放卡片"""
    
    # 信号定义
    position_changed = Signal(int)  # 播放位置变化
    video_opened = Signal(str)      # 视频已打开
    
    # 默认停靠区域
    default_area = Qt.LeftDockWidgetArea
    
    def __init__(self, parent=None):
        super().__init__("视频预览", parent)
        self._setup_ui()
```

### 2. 信号通信

卡片间通过信号通信，不直接引用：

```python
# ✅ 正确：通过信号通信
self.player_card.position_changed.connect(self.waveform_card.update_position)

# ❌ 错误：直接调用其他卡片的方法
self.player_card._player.setPosition(1000)
```

### 3. 职责分离

每个卡片只负责自己的功能：
- **PlayerCard**：视频渲染（不包含播放按钮）
- **WaveformCard**：波形显示和打轴操作
- **TimelineCard**：字幕列表显示和管理
- **TranslateCard**：字幕文本编辑

---

## 基类规范

### 信号定义

```python
class PlayerCard(QDockWidget):
    """视频播放卡片"""
    
    # 信号定义
    position_changed = Signal(int)  # 播放位置变化
    video_opened = Signal(str)      # 视频已打开
    
    # 默认停靠区域
    default_area = Qt.LeftDockWidgetArea
```

### 初始化

```python
def __init__(self, parent=None):
    super().__init__("视频预览", parent)
    self._setup_ui()
    self._connect_signals()
```

### UI 初始化

```python
def _setup_ui(self):
    """初始化 UI"""
    # 创建主容器
    main_widget = QWidget()
    self.setWidget(main_widget)
    
    # 创建布局
    layout = QVBoxLayout(main_widget)
    
    # 添加组件
    # ...
```

---

## 信号通信图

```
PlayerCard
  │ position_changed ──────────→ MainWindow
  │ duration_changed ──────────→ MainWindow
  │ video_opened ──────────────→ MainWindow
  │ playback_state_changed ────→ MainWindow
  │ ab_loop_changed ───────────→ MainWindow

WaveformCard
  │ position_clicked ──────────→ PlayerCard.set_position
  │ subtitle_created ──────────→ TimelineCard.add_subtitle
  │ subtitle_edited ───────────→ TimelineCard.apply_subtitle_edit

TimelineCard
  │ subtitle_selected ─────────→ TranslateCard.show_subtitle
  │ subtitle_changed ───────────→ WaveformCard.update_subtitle_overlay_from_data
  │ jump_to_position ──────────→ PlayerCard.set_position
  │ edit_subtitle_requested ───→ WaveformCard.enter_edit_mode

TranslateCard
  │ text_saved ────────────────→ TimelineCard.set_subtitle_text
  │ jump_to_next ──────────────→ MainWindow._on_jump_to_next
  │ jump_to_prev ──────────────→ MainWindow._on_jump_to_prev
  │ editing_subtitle ──────────→ TimelineCard.highlight_subtitle
```

---

## 布局位置

### 默认布局

```
┌──────────────────┬───────────────────────────────┐
│                  │                               │
│  PlayerCard      │  TimelineCard                 │
│  (左上)          │  (右上)                       │
│                  │                               │
├──────────────────┼───────────────────────────────┤
│                  │                               │
│  WaveformCard    │  TranslateCard                │
│  (左下)          │  (右下)                       │
│                  │                               │
└──────────────────┴───────────────────────────────┘
```

### 比例

- 左 39% 右 61%
- 上 56% 下 44%
- 窗口缩放时保持比例不变

---

## 测试要求

| 模块 | 测试要求 |
|------|---------|
| `player_card.py` | 可选，优先测试核心逻辑 |
| `waveform_card.py` | 可选 |
| `timeline_card.py` | 可选 |
| `translate_card.py` | 可选 |

卡片测试需要 PySide6 环境，建议优先测试核心层。

---

## 依赖

- PySide6: `QDockWidget`, `QWidget`, `QVBoxLayout`
- chestnut_studio.core: 核心层模块
- chestnut_studio.utils: 工具层模块
