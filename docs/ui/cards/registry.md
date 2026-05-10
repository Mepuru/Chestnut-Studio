# 卡片注册表

> `chestnut_studio/ui/cards/registry.py`
> 卡片自动发现与注册系统，消除 MainWindow 对具体卡片类的硬编码依赖。

---

## 概述

注册表提供：
- @register_card 装饰器自动注册卡片
- get_registry() 获取所有注册卡片
- create_card() 根据 card_id 创建实例
- 新增卡片无需修改 MainWindow

---

## 注册机制

### @register_card 装饰器

```python
from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.registry import register_card

@register_card
class PlayerCard(BaseCard):
    card_id = "player"
    card_title = "视频预览"
    default_area = Qt.LeftDockWidgetArea
    # ...
```

### 自动发现

装饰器在 **模块导入时** 自动执行注册。确保 `cards/__init__.py` 导入所有卡片模块：

```python
# chestnut_studio/ui/cards/__init__.py

from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.registry import (
    create_card,
    get_card_class,
    get_ordered_cards,
    get_registry,
    register_card,
)

# 导入所有卡片模块以触发 @register_card 装饰器注册
from chestnut_studio.ui.cards.player_card import PlayerCard
from chestnut_studio.ui.cards.waveform_card import WaveformCard
from chestnut_studio.ui.cards.timeline_card import TimelineCard
from chestnut_studio.ui.cards.translate_card import TranslateCard

__all__ = [
    "BaseCard",
    "register_card",
    "get_registry",
    "get_ordered_cards",
    "get_card_class",
    "create_card",
    "PlayerCard",
    "WaveformCard",
    "TimelineCard",
    "TranslateCard",
]
```

---

## API 参考

### register_card(cls)

类装饰器：将卡片类注册到全局注册表。

```python
@register_card
class MyCard(BaseCard):
    card_id = "my_card"
```

**参数：**
- `cls`: 要注册的卡片类，必须声明 `card_id` 类属性

**返回：**
- 原始类（不修改）

**异常：**
- `ValueError`: 如果 `card_id` 未声明或已被注册

### get_registry()

返回注册表的只读副本。

```python
registry = get_registry()
# {"player": PlayerCard, "waveform": WaveformCard, ...}
```

**返回：**
- `dict[str, type[BaseCard]]`: card_id → 卡片类 的字典

### get_ordered_cards()

按 `order` 属性排序返回注册表。

```python
ordered = get_ordered_cards()
# [("player", PlayerCard), ("waveform", WaveformCard), ...]
```

**返回：**
- `list[tuple[str, type[BaseCard]]]`: (card_id, 卡片类) 的列表

### get_card_class(card_id)

根据 card_id 获取卡片类。

```python
cls = get_card_class("player")  # PlayerCard
cls = get_card_class("unknown")  # None
```

**参数：**
- `card_id`: 卡片的唯一标识符

**返回：**
- 卡片类，如果未注册则返回 None

### create_card(card_id, parent)

根据 card_id 创建卡片实例。

```python
card = create_card("player", parent=self)
```

**参数：**
- `card_id`: 卡片的唯一标识符
- `parent`: 父组件

**返回：**
- 卡片实例，如果未注册则返回 None

---

## 卡片顺序控制

在卡片类中声明 `order` 属性控制布局顺序：

```python
@register_card
class PlayerCard(BaseCard):
    card_id = "player"
    order = 1  # 布局顺序，数字越小越先布局

@register_card
class WaveformCard(BaseCard):
    card_id = "waveform"
    order = 2
```

---

## 完整工作流

```
1. 应用启动
   │
   ├─► import chestnut_studio.ui.cards
   │     │
   │     ├─► @register_card PlayerCard    → 注册 "player"
   │     ├─► @register_card WaveformCard  → 注册 "waveform"
   │     ├─► @register_card TimelineCard  → 注册 "timeline"
   │     └─► @register_card TranslateCard → 注册 "translate"
   │
   ├─► MainWindow.__init__()
   │     │
   │     ├─► _create_cards()
   │     │     └─► 遍历 get_registry()，create_card() 每张卡片
   │     │
   │     ├─► _setup_layout()
   │     │     └─► 根据布局配置（layout_system.md）自动排列
   │     │
   │     ├─► _connect_signals()
   │     │     └─► 根据声明式信号（declarative_signals.md）自动连接
   │     │
   │     └─► _on_all_cards_created()
   │           └─► 调用每张卡片的 on_ready()
   │
   └─► 应用就绪
```

---

## 新增卡片流程

1. 创建新文件 `cards/new_card.py`
2. 使用 `@register_card` 装饰器
3. 在 `cards/__init__.py` 中添加导入
4. （可选）在布局 JSON 中添加位置

**无需修改 MainWindow！**

---

## 注意事项

1. **`card_id` 必须全局唯一** — 重复注册会抛出 `ValueError`
2. **模块导入顺序决定注册顺序** — 通过 `__all__` 控制
3. **注册发生在模块导入时** — 如果卡片模块未被导入，不会注册
4. **不要在注册表中存储实例** — 注册表只存类，实例由 MainWindow 管理

---

## 依赖

- `chestnut_studio.ui.cards.base_card`: BaseCard 基类
- Python 3.12+: `dict` 保持插入顺序
