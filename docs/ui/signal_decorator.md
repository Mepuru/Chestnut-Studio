# 信号装饰器

> `chestnut_studio/ui/signal_decorator.py`
> 提供 @subscribe 和 @relay 装饰器，简化信号声明。

---

## 概述

装饰器提供：
- `@subscribe` — 卡片订阅信号
- `@relay` — MainWindow 中转处理
- `collect_subscriptions()` — 收集对象上所有 @subscribe 声明
- `collect_relays()` — 收集对象上所有 @relay 声明

---

## @subscribe 装饰器

声明方法订阅某个信号。

```python
from chestnut_studio.ui.signal_decorator import subscribe

class WaveformCard(BaseCard):
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

**参数：**
- `source_key`: 信号源，格式 `"card_id.signal_name"`

**使用方式：**
- 直接在方法上添加装饰器
- 方法名可以任意，不需要与信号名匹配
- 多个装饰器可以叠加

---

## @relay 装饰器

声明方法作为中转处理函数。

```python
from chestnut_studio.ui.signal_decorator import relay

class MainWindow:
    @relay("player.video_opened")
    def _on_video_opened(self, path: str):
        """视频打开后的处理"""
        self.status_bar.set_status(f"已打开: {path}")
        QTimer.singleShot(100, lambda: self._load_waveform(path))

    @relay("translate.jump_to_next")
    def _on_jump_to_next(self, col: int, start_ms: int):
        """跳转到下一条字幕"""
        next_sub = self.timeline_card.get_next_subtitle(col, start_ms)
        if next_sub:
            self.player_card.set_position(next_sub.start_ms)
```

**参数：**
- `source_key`: 信号源，格式 `"card_id.signal_name"`

**与 @subscribe 的区别：**
- `@subscribe` 用于卡片订阅其他卡片/组件的信号
- `@relay` 用于 MainWindow 中转处理信号

---

## collect_subscriptions(obj)

收集对象上所有 @subscribe 装饰器声明的订阅。

```python
from chestnut_studio.ui.signal_decorator import collect_subscriptions

card = WaveformCard()
subscriptions = collect_subscriptions(card)
# {"player.position_changed": "update_position", "player.duration_changed": "set_duration"}
```

**参数：**
- `obj`: 要收集订阅的对象

**返回：**
- `dict[str, str]`: {source_key: handler_name} 字典

---

## collect_relays(obj)

收集对象上所有 @relay 装饰器声明的中转处理。

```python
from chestnut_studio.ui.signal_decorator import collect_relays

main_window = MainWindow()
relays = collect_relays(main_window)
# {"player.video_opened": "_on_video_opened", "translate.jump_to_next": "_on_jump_to_next"}
```

**参数：**
- `obj`: 要收集中转处理的对象

**返回：**
- `dict[str, str]`: {source_key: handler_name} 字典

---

## 使用场景

### 卡片订阅信号

```python
@register_card
class WaveformCard(BaseCard):
    @subscribe("player.position_changed")
    def update_position(self, ms): ...

    @subscribe("player.duration_changed")
    def set_duration(self, ms): ...
```

### MainWindow 中转处理

```python
class MainWindow:
    @relay("player.video_opened")
    def _on_video_opened(self, path): ...

    @relay("translate.jump_to_next")
    def _on_jump_to_next(self, col, start_ms): ...
```

### 混合使用

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

## 注意事项

1. **装饰器在模块导入时执行** — 确保模块被正确导入
2. **方法名可以任意** — 不需要与信号名匹配
3. **可以叠加多个装饰器** — 一个方法可以订阅多个信号
4. **与 listens_to() 混合使用** — 装饰器声明会自动合并

---

## 依赖

- 无外部依赖
