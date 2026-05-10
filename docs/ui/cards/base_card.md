# BaseCard 基类

> `chestnut_studio/ui/cards/base_card.py`
> `BaseCard(QDockWidget)` — 所有卡片组件的统一基类，提供生命周期钩子和声明式信号订阅。

---

## 概述

BaseCard 是所有卡片的基类，提供：
- 标准化初始化流程
- 生命周期钩子
- 声明式属性（card_id, card_title, default_area 等）
- 声明式信号订阅（@subscribe 装饰器 + listens_to() 方法）

---

## 类属性

| 属性 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `card_id` | `str` | ✅ | 唯一标识符，用于注册表查找和布局配置 |
| `card_title` | `str` | ✅ | 卡片标题，显示在标题栏 |
| `default_area` | `Qt.DockWidgetArea` | ❌ | 默认停靠区域（默认：LeftDockWidgetArea） |
| `default_ratio` | `float` | ❌ | 在所属区域内的默认占比（默认：0.5） |
| `min_size` | `tuple[int, int]` | ❌ | 最小尺寸（默认：(200, 150)） |
| `features` | `QDockWidget.DockWidgetFeatures` | ❌ | DockWidget 特性标志 |

---

## 生命周期钩子

| 钩子 | 调用时机 | 用途 |
|------|----------|------|
| `on_init()` | `__init__` 末尾 | 子类自定义初始化（替代重写 `__init__`） |
| `on_ready()` | 所有卡片创建完毕、信号连接完成后 | 依赖其他卡片的延迟初始化 |
| `on_save_state() -> dict` | 布局保存时 | 返回需要持久化的状态字典 |
| `on_load_state(data: dict)` | 布局恢复时 | 从字典恢复状态 |
| `on_theme_changed()` | 主题切换时 | 刷新自定义样式 |

---

## 声明式信号订阅

### 方式 1：@subscribe 装饰器

```python
from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.registry import register_card
from chestnut_studio.ui.signal_decorator import subscribe

@register_card
class WaveformCard(BaseCard):
    card_id = "waveform"
    card_title = "波形图"

    @subscribe("player.position_changed")
    def update_position(self, ms: int):
        """接收播放位置更新"""
        self._current_position_ms = ms
        self._red_line.setPos(ms)

    @subscribe("player.duration_changed")
    def set_duration(self, duration_ms: int):
        """接收视频时长更新"""
        self._duration_ms = duration_ms
```

### 方式 2：listens_to() 方法

```python
@register_card
class WaveformCard(BaseCard):
    card_id = "waveform"
    card_title = "波形图"

    def listens_to(self) -> dict[str, str]:
        """声明订阅的信号"""
        return {
            "player.position_changed": "update_position",
            "player.duration_changed": "set_duration",
        }

    def update_position(self, ms: int):
        self._current_position_ms = ms

    def set_duration(self, duration_ms: int):
        self._duration_ms = duration_ms
```

### 混合使用

两种方式可以混合使用，装饰器声明会自动合并：

```python
@register_card
class SomeCard(BaseCard):
    @subscribe("player.position_changed")
    def update_position(self, ms): ...

    def listens_to(self):
        # 可以返回额外的订阅
        return {"toolbar.play_clicked": "on_play"}
```

---

## 子类实现模板

```python
from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.registry import register_card
from chestnut_studio.ui.signal_decorator import subscribe

@register_card
class ExampleCard(BaseCard):
    """示例卡片"""

    card_id = "example"
    card_title = "示例面板"
    default_area = Qt.RightDockWidgetArea
    default_ratio = 0.3

    # 信号定义
    data_changed = Signal(str)

    def _setup_ui(self):
        """初始化 UI 布局"""
        main_widget = QWidget()
        self.setWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        # ...

    def _connect_internal_signals(self):
        """连接卡片内部信号"""
        # ...

    @subscribe("player.position_changed")
    def update_position(self, ms: int):
        """接收播放位置更新"""
        pass

    def on_save_state(self) -> dict:
        return {"scroll_position": self._scrollbar.value()}

    def on_load_state(self, data: dict) -> None:
        if "scroll_position" in data:
            self._scrollbar.setValue(data["scroll_position"])
```

---

## 状态持久化

### 保存格式

`on_save_state()` 返回的字典会被序列化为 JSON，存储在 `QSettings` 中：

```json
{
  "player": {
    "__auto_state__": {
      "volume": 80,
      "playback_rate": 1.0
    }
  },
  "timeline": {
    "__auto_state__": {
      "scroll_position": 0,
      "selected_row": 5
    }
  }
}
```

---

## 注意事项

1. **不要重写 `__init__`** — 使用 `_setup_ui()` 和 `on_init()` 钩子
2. **`card_id` 必须全局唯一** — 重复 ID 会导致注册表冲突
3. **`on_ready()` 中才能访问其他卡片** — 此时所有卡片已创建完毕
4. **`on_save_state()` 返回值必须是 JSON 可序列化的** — 不要包含 QObject 引用

---

## 依赖

- PySide6: `QDockWidget`, `Qt`, `Signal`
- 无外部模块依赖
