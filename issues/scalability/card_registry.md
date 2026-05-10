# 卡片注册表

> `chestnut_studio/ui/cards/registry.py`
> 卡片自动发现与注册系统，消除 `MainWindow` 对具体卡片类的硬编码依赖。

---

## 一、动机

### 1.1 现状问题

新增一张卡片需要修改 `MainWindow` 的 **5 个方法**：

```python
# main_window.py 中需要改动的位置
def _create_cards(self):          # 1. 实例化
def _setup_default_layout(self):  # 2. 布局位置
def _connect_signals(self):       # 3. 信号连线
def _apply_layout_size(self):     # 4. 尺寸比例
def _dump_layout_info(self):      # 5. 调试列表
```

随着卡片数量增长，`MainWindow` 会变成一个"上帝类"——了解所有卡片的具体细节。

### 1.2 设计目标

- 新增卡片**只改卡片自己的文件**，不改 `MainWindow`
- `MainWindow` 通过注册表自动发现所有卡片
- 卡片自描述（ID、默认区域、信号声明等信息都在卡片自身）

---

## 二、注册表设计

### 2.1 注册表模块

```python
# chestnut_studio/ui/cards/registry.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chestnut_studio.ui.cards.base_card import BaseCard

_CARD_REGISTRY: dict[str, type[BaseCard]] = {}


def register_card(cls: type[BaseCard]) -> type[BaseCard]:
    """类装饰器：将卡片类注册到全局注册表。

    用法：
        @register_card
        class MyCard(BaseCard):
            card_id = "my_card"
    """
    card_id = getattr(cls, "card_id", None)
    if not card_id:
        raise ValueError(f"{cls.__name__} 必须声明 card_id 类属性")
    if card_id in _CARD_REGISTRY:
        raise ValueError(f"card_id '{card_id}' 已被 {_CARD_REGISTRY[card_id].__name__} 注册")
    _CARD_REGISTRY[card_id] = cls
    return cls


def get_registry() -> dict[str, type[BaseCard]]:
    """返回注册表的只读副本。"""
    return _CARD_REGISTRY.copy()


def get_card_class(card_id: str) -> type[BaseCard] | None:
    """根据 card_id 获取卡片类。"""
    return _CARD_REGISTRY.get(card_id)


def create_card(card_id: str, parent=None) -> BaseCard | None:
    """根据 card_id 创建卡片实例。"""
    cls = _CARD_REGISTRY.get(card_id)
    if cls is None:
        return None
    return cls(parent)
```

### 2.2 注册机制

使用 **类装饰器** 注册。每张卡片文件顶部加 `@register_card`：

```python
# chestnut_studio/ui/cards/player_card.py

from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.registry import register_card

@register_card
class PlayerCard(BaseCard):
    card_id = "player"
    card_title = "视频预览"
    default_area = Qt.LeftDockWidgetArea
    # ...
```

### 2.3 自动发现

装饰器在 **模块导入时** 自动执行注册。确保 `cards/__init__.py` 导入所有卡片模块：

```python
# chestnut_studio/ui/cards/__init__.py

from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.player_card import PlayerCard
from chestnut_studio.ui.cards.waveform_card import WaveformCard
from chestnut_studio.ui.cards.timeline_card import TimelineCard
from chestnut_studio.ui.cards.translate_card import TranslateCard

__all__ = [
    "BaseCard",
    "PlayerCard",
    "WaveformCard",
    "TimelineCard",
    "TranslateCard",
]
```

只要 `cards` 包被导入，所有卡片自动注册。

---

## 三、MainWindow 使用方式

### 3.1 卡片创建

```python
# main_window.py

from chestnut_studio.ui.cards.registry import get_registry, create_card

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ...
        self._cards: dict[str, BaseCard] = {}
        self._create_cards()

    def _create_cards(self):
        """自动创建所有已注册的卡片"""
        for card_id in get_registry():
            card = create_card(card_id, parent=self)
            if card:
                self._cards[card_id] = card
```

### 3.2 卡片访问

```python
# 通过 card_id 访问
player = self._cards.get("player")
timeline = self._cards.get("timeline")

# 类型安全的访问方法（可选）
def get_card(self, card_id: str) -> BaseCard | None:
    return self._cards.get(card_id)
```

### 3.3 生命周期管理

```python
def _on_all_cards_created(self):
    """所有卡片创建完毕后调用"""
    for card in self._cards.values():
        card.on_ready()
```

---

## 四、卡片顺序控制

### 4.1 问题

注册表使用 `dict`，Python 3.7+ 保证插入顺序。但装饰器的执行顺序取决于模块导入顺序，而 `__all__` 列表的顺序决定了导入顺序。

### 4.2 解决方案

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

注册表按 `order` 排序：

```python
def get_ordered_cards() -> list[tuple[str, type[BaseCard]]]:
    """按 order 属性排序返回注册表。"""
    return sorted(
        _CARD_REGISTRY.items(),
        key=lambda item: getattr(item[1], "order", 999)
    )
```

---

## 五、完整工作流

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

## 六、迁移步骤

### 6.1 渐进式迁移

不需要一次性改完所有卡片。可以分步迁移：

**步骤 1**：创建 `BaseCard` 和 `registry.py`

**步骤 2**：迁移一张卡片（如 `TranslateCard`，最简单）作为试点

**步骤 3**：验证注册表工作正常后，逐步迁移其余卡片

**步骤 4**：清理 `MainWindow` 中的硬编码

### 6.2 兼容性

迁移期间，未迁移的卡片可以继续使用旧方式在 `MainWindow` 中手动创建。注册表只管理已注册的卡片。

---

## 七、依赖

- `chestnut_studio.ui.cards.base_card`: BaseCard 基类
- Python 3.12+: `dict` 保持插入顺序

---

## 八、注意事项

1. **`card_id` 必须全局唯一** — 重复注册会抛出 `ValueError`
2. **模块导入顺序决定注册顺序** — 通过 `__all__` 控制
3. **注册发生在模块导入时** — 如果卡片模块未被导入，不会注册
4. **不要在注册表中存储实例** — 注册表只存类，实例由 `MainWindow` 管理
5. **类型提示** — 使用 `TYPE_CHECKING` 避免循环导入
