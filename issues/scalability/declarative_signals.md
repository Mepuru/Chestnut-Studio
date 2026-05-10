# 声明式信号系统

> `chestnut_studio/ui/cards/base_card.py` (扩展)
> 卡片自描述信号订阅，消除 `MainWindow._connect_signals()` 中的手动连线代码。

---

## 一、动机

### 1.1 现状问题

`MainWindow._connect_signals()` 当前约 70 行，手动连接每一对信号-槽：

```python
# main_window.py — 当前 4 张卡片的连线（摘录）
self.toolbar.play_clicked.connect(self.player_card.play_pause)
self.toolbar.rate_changed.connect(self.player_card.set_playback_rate)
self.player_card.position_changed.connect(self.toolbar.update_position)
self.player_card.position_changed.connect(self.waveform_card.update_position)
self.player_card.duration_changed.connect(self.waveform_card.set_duration)
self.player_card.duration_changed.connect(self.timeline_card.set_duration)
self.player_card.ab_loop_changed.connect(self.toolbar.update_ab_loop_state)
self.player_card.ab_loop_changed.connect(self.waveform_card.set_ab_loop_region)
self.waveform_card.position_clicked.connect(self.player_card.set_position)
self.waveform_card.subtitle_created.connect(self._on_subtitle_created)
self.timeline_card.jump_to_position.connect(self.player_card.set_position)
self.timeline_card.subtitle_changed.connect(self._sync_subtitle_overlay)
self.timeline_card.edit_subtitle_requested.connect(self.waveform_card.enter_edit_mode)
self.waveform_card.subtitle_edited.connect(self.timeline_card.apply_subtitle_edit)
self.timeline_card.subtitle_selected.connect(self._on_subtitle_selected)
self.translate_card.text_saved.connect(self._on_text_saved)
self.translate_card.jump_to_next.connect(self._on_jump_to_next)
self.translate_card.jump_to_prev.connect(self._on_jump_to_prev)
self.translate_card.editing_subtitle.connect(self.timeline_card.highlight_subtitle)
```

**问题**：

- 每新增一张卡片，需要在此方法中添加 N 条 `connect` 语句
- MainWindow 必须知道每张卡片有哪些信号、需要连接到哪里
- 信号关系散落在代码中，难以全局审视

### 1.2 设计目标

- 卡片**自己声明**它关心哪些外部信号
- MainWindow 只负责**自动解析和连接**
- 新增卡片不改 MainWindow 的连线代码

---

## 二、声明式信号订阅

### 2.1 核心接口

在 `BaseCard` 中新增 `listens_to()` 方法：

```python
class BaseCard(QDockWidget):
    def listens_to(self) -> dict[str, str | Callable]:
        """声明本卡片关心的外部信号。

        返回格式:
            {
                "<source_card_id>.<signal_name>": "<handler_method_name>",
                # 或
                "<source_card_id>.<signal_name>": self._handler_method,
            }

        示例:
            return {
                "player.position_changed": "update_position",
                "player.duration_changed": "set_duration",
                "toolbar.play_clicked": self._on_play,
            }
        """
        return {}
```

### 2.2 声明示例

**WaveformCard**:
```python
class WaveformCard(BaseCard):
    card_id = "waveform"

    def listens_to(self) -> dict[str, str | Callable]:
        return {
            "player.position_changed": "update_position",
            "player.duration_changed": "set_duration",
            "player.ab_loop_changed": "set_ab_loop_region",
        }
```

**TimelineCard**:
```python
class TimelineCard(BaseCard):
    card_id = "timeline"

    def listens_to(self) -> dict[str, str | Callable]:
        return {
            "player.duration_changed": "set_duration",
        }
```

**TranslateCard**:
```python
class TranslateCard(BaseCard):
    card_id = "translate"

    def listens_to(self) -> dict[str, str | Callable]:
        return {
            "timeline.subtitle_selected": "_on_subtitle_selected",
        }
```

---

## 三、自动连接机制

### 3.1 MainWindow 统一解析

```python
# main_window.py

def _connect_signals(self):
    """自动连接所有卡片声明的信号"""
    # 1. 连接卡片间信号
    for card_id, card in self._cards.items():
        subscriptions = card.listens_to()
        for source_key, handler in subscriptions.items():
            # 解析 "player.position_changed"
            parts = source_key.split(".", 1)
            if len(parts) != 2:
                continue
            src_id, signal_name = parts

            # 获取源卡片
            source = self._cards.get(src_id)
            if source is None:
                # 也支持 toolbar、statusbar 等非卡片组件
                source = self._get_special_component(src_id)
            if source is None:
                print(f"[Signal] 未知源: {src_id}")
                continue

            # 获取信号
            signal = getattr(source, signal_name, None)
            if signal is None:
                print(f"[Signal] {src_id} 没有信号 {signal_name}")
                continue

            # 获取处理函数
            if callable(handler):
                slot = handler
            else:
                slot = getattr(card, handler, None)
            if slot is None:
                print(f"[Signal] {card_id} 没有方法 {handler}")
                continue

            # 连接
            signal.connect(slot)

    # 2. 连接特殊组件（toolbar、statusbar 等）
    self._connect_special_signals()
```

### 3.2 特殊组件支持

toolbar、statusbar 等不是 `BaseCard` 子类，但也需要参与信号连接。通过 `_get_special_component()` 统一管理：

```python
def _get_special_component(self, component_id: str):
    """获取非卡片组件"""
    special = {
        "toolbar": self.toolbar,
        "statusbar": self.status_bar,
        "menubar": self.menu_bar,
    }
    return special.get(component_id)
```

### 3.3 双向信号

有些信号是双向的——卡片 A 订阅卡片 B 的信号，同时卡片 B 也订阅卡片 A 的信号。声明式系统天然支持：

```python
# WaveformCard 声明订阅 player 的信号
class WaveformCard(BaseCard):
    def listens_to(self):
        return {
            "player.position_changed": "update_position",
        }

# PlayerCard 声明订阅 waveform 的信号
class PlayerCard(BaseCard):
    def listens_to(self):
        return {
            "waveform.position_clicked": "set_position",
        }
```

MainWindow 自动完成双向连接。

---

## 四、MainWindow 中间层信号

### 4.1 问题

部分信号需要 MainWindow 做中间处理（如 `_on_subtitle_created`、`_sync_subtitle_overlay`），不能直接连接到目标卡片。

### 4.2 解决方案

在 MainWindow 中声明这些"中转信号"：

```python
class MainWindow(QMainWindow):
    # ── 中转处理声明 ──
    def _get_relay_handlers(self) -> dict[str, Callable]:
        """声明需要 MainWindow 中转处理的信号。

        格式: "<source_card_id>.<signal_name>": handler_method
        """
        return {
            "waveform.subtitle_created": self._on_subtitle_created,
            "timeline.subtitle_changed": self._sync_subtitle_overlay,
            "timeline.subtitle_selected": self._on_subtitle_selected,
            "translate.text_saved": self._on_text_saved,
            "translate.jump_to_next": self._on_jump_to_next,
            "translate.jump_to_prev": self._on_jump_to_prev,
        }
```

自动连接时，优先检查 `_get_relay_handlers()`，如果匹配则走中转逻辑。

---

## 五、信号命名规范

### 5.1 命名约定

| 类型 | 格式 | 示例 |
|------|------|------|
| 状态变化 | `<名词>_changed` | `position_changed`, `duration_changed` |
| 用户操作 | `<动作>_clicked` / `<动作>_requested` | `play_clicked`, `edit_subtitle_requested` |
| 数据事件 | `<名词>_created` / `<名词>_saved` | `subtitle_created`, `text_saved` |
| 导航事件 | `jump_to_<目标>` | `jump_to_position`, `jump_to_next` |

### 5.2 声明格式

```python
# 格式: "<card_id>.<signal_name>"
"player.position_changed"
"waveform.subtitle_created"
"timeline.edit_subtitle_requested"
"translate.text_saved"

# 特殊组件使用组件 ID
"toolbar.play_clicked"
```

---

## 六、完整示例

### 6.1 一张新卡片的完整声明

```python
@register_card
class SubtitlePreviewCard(BaseCard):
    """字幕预览卡片 — 实时显示当前字幕的渲染效果"""

    card_id = "subtitle_preview"
    card_title = "字幕预览"
    default_area = Qt.RightDockWidgetArea
    default_ratio = 0.3

    def _setup_ui(self):
        # ...
        pass

    def listens_to(self) -> dict[str, str | Callable]:
        return {
            # 从 timeline 获取当前字幕数据
            "timeline.subtitle_selected": "_on_subtitle_selected",
            # 从 player 同步播放位置（用于高亮当前行）
            "player.position_changed": "_on_position_changed",
        }

    def _on_subtitle_selected(self, col: int, start_ms: int):
        """显示选中的字幕"""
        # ...

    def _on_position_changed(self, position_ms: int):
        """高亮当前播放时间对应的字幕"""
        # ...
```

**MainWindow 零改动**。只需在 `cards/__init__.py` 中导入新模块即可。

---

## 七、迁移策略

### 7.1 渐进式迁移

| 阶段 | 改动 | 影响 |
|------|------|------|
| 阶段 1 | 实现 `listens_to()` 接口 | 无影响，旧代码继续工作 |
| 阶段 2 | 迁移 1-2 张卡片到声明式 | 对应的 `connect` 语句从 `_connect_signals()` 删除 |
| 阶段 3 | 迁移所有卡片 | `_connect_signals()` 只剩自动连接逻辑 |
| 阶段 4 | 删除手动代码 | 清理完毕 |

### 7.2 兼容性

迁移期间可以混合使用：已迁移的卡片用声明式，未迁移的继续手动连接。

---

## 八、依赖

- `chestnut_studio.ui.cards.base_card`: BaseCard 基类
- `chestnut_studio.ui.cards.registry`: 卡片注册表

---

## 九、注意事项

1. **信号源必须已注册或在特殊组件中** — 否则解析失败
2. **处理函数必须是卡片的公开方法** — 私有方法也可，但建议用公开方法
3. **避免循环订阅** — A 订阅 B 的信号，B 又订阅 A 的同一信号可能导致无限循环
4. **中转处理优先** — 如果 MainWindow 的 `_get_relay_handlers()` 匹配了某个信号，卡片的 `listens_to()` 中对应条目会被跳过
