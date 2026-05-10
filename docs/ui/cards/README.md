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

### 1. 继承 BaseCard

所有卡片继承 `BaseCard`（而不是直接继承 `QDockWidget`）：

```python
from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.registry import register_card

@register_card
class PlayerCard(BaseCard):
    """视频播放卡片"""
    
    # BaseCard 必需属性
    card_id = "player"
    card_title = "视频预览"
    default_area = Qt.LeftDockWidgetArea
    default_ratio = 0.39
    
    # 信号定义
    position_changed = Signal(int)
    video_opened = Signal(str)
    
    def _setup_ui(self):
        """初始化 UI"""
        pass
    
    def listens_to(self):
        """声明订阅的信号"""
        return {
            "waveform.position_clicked": "set_position",
            "toolbar.play_clicked": "play_pause",
        }
```

### 2. 信号通信

卡片间通过信号通信，不直接引用：

```python
# ✅ 正确：通过 @subscribe 装饰器声明
@subscribe("player.position_changed")
def update_position(self, ms): ...

# ✅ 正确：通过 listens_to() 声明
def listens_to(self):
    return {"player.position_changed": "update_position"}

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

### BaseCard 类属性

```python
class BaseCard(QDockWidget):
    """所有卡片的基类"""
    
    # 子类必须声明
    card_id: str = ""           # 唯一标识符
    card_title: str = ""        # 卡片标题
    
    # 子类可选声明
    default_area = Qt.LeftDockWidgetArea  # 默认停靠区域
    default_ratio: float = 0.5            # 默认占比
    min_size: tuple = (200, 150)          # 最小尺寸
```

### 生命周期钩子

| 钩子 | 调用时机 | 用途 |
|------|----------|------|
| `on_init()` | `__init__` 末尾 | 自定义初始化 |
| `on_ready()` | 所有卡片创建完毕后 | 延迟初始化 |
| `on_save_state()` | 布局保存时 | 返回状态字典 |
| `on_load_state()` | 布局恢复时 | 恢复状态 |

### 信号声明

```python
# 方式 1：@subscribe 装饰器
@subscribe("player.position_changed")
def update_position(self, ms): ...

# 方式 2：listens_to() 方法
def listens_to(self):
    return {"player.position_changed": "update_position"}
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
