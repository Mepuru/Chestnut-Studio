# BaseCard 基类

> `chestnut_studio/ui/cards/base_card.py`
> `BaseCard(QDockWidget)` — 所有卡片组件的统一基类，提供生命周期钩子、状态持久化接口和标准化初始化流程。

---

## 一、动机

### 1.1 现状问题

当前四张卡片各自直接继承 `QDockWidget`，存在大量重复代码：

| 重复内容 | 出现位置 | 次数 |
|----------|----------|------|
| `setFeatures(Movable \| Closable)` | `main_window.py:_create_cards()` | 4 次 |
| `setMinimumSize(200, 150)` | `main_window.py:_create_cards()` + `_setup_default_layout()` | 8 次 |
| `setObjectName(...)` | `main_window.py:_create_cards()` | 4 次 |
| `save_state()` / `load_state()` 模式 | 各卡片（如果实现） | 4 处 |
| `default_area` 类属性 | 各卡片 | 4 处 |

新增一张卡片需要在 `MainWindow` 中手动添加 5+ 处代码。

### 1.2 设计目标

- 新卡片只需继承 `BaseCard`，声明 `card_id` 和 `default_area` 即可
- `MainWindow` 通过注册表自动发现和管理卡片（见 [card_registry.md](card_registry.md)）
- 统一的生命周期钩子，消除 `MainWindow` 对卡片内部细节的了解
- 内置状态持久化接口

---

## 二、类定义

### 2.1 类属性

```python
class BaseCard(QDockWidget):
    """所有卡片组件的基类"""

    # ── 子类必须声明 ──
    card_id: str = ""
    """唯一标识符，用于注册表查找和布局配置。"""

    card_title: str = ""
    """卡片标题，显示在标题栏。支持 i18n key。"""

    default_area: Qt.DockWidgetArea = Qt.LeftDockWidgetArea
    """默认停靠区域。"""

    # ── 子类可选声明 ──
    default_ratio: float = 0.5
    """在所属区域内的默认占比 (0.0 ~ 1.0)。"""

    min_size: tuple[int, int] = (200, 150)
    """最小尺寸 (width, height)。"""

    features: QDockWidget.DockWidgetFeatures = (
        QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
    )
    """DockWidget 特性标志。"""
```

### 2.2 初始化流程

```python
def __init__(self, parent=None):
    super().__init__(self.card_title, parent)

    # 应用标准属性
    self.setObjectName(self.card_id)
    self.setFeatures(self.features)
    self.setMinimumSize(*self.min_size)

    # 子类初始化
    self._setup_ui()
    self._connect_internal_signals()

    # 生命周期钩子
    self.on_init()
```

**子类不应重写 `__init__`**，而是通过 `_setup_ui()` 和钩子方法完成初始化。

---

## 三、生命周期钩子

| 钩子 | 调用时机 | 用途 |
|------|----------|------|
| `on_init()` | `__init__` 末尾 | 子类自定义初始化（替代重写 `__init__`） |
| `on_ready()` | 所有卡片创建完毕、信号连接完成后 | 依赖其他卡片的延迟初始化 |
| `on_save_state() -> dict` | 布局保存时 | 返回需要持久化的状态字典 |
| `on_load_state(data: dict)` | 布局恢复时 | 从字典恢复状态 |
| `on_theme_changed()` | 主题切换时 | 刷新自定义样式 |

### 3.1 默认实现

```python
def on_init(self) -> None:
    """子类自定义初始化，替代重写 __init__。"""
    pass

def on_ready(self) -> None:
    """所有卡片就绪后的回调，可安全引用其他卡片。"""
    pass

def on_save_state(self) -> dict:
    """返回需要持久化的状态字典。默认返回空字典。"""
    return {}

def on_load_state(self, data: dict) -> None:
    """从字典恢复状态。默认空实现。"""
    pass

def on_theme_changed(self) -> None:
    """主题切换时的回调。默认空实现。"""
    pass
```

---

## 四、子类实现模板

```python
from chestnut_studio.ui.cards.base_card import BaseCard

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

    def on_save_state(self) -> dict:
        return {"scroll_position": self._scrollbar.value()}

    def on_load_state(self, data: dict) -> None:
        if "scroll_position" in data:
            self._scrollbar.setValue(data["scroll_position"])
```

---

## 五、与现有卡片的迁移路径

### 5.1 迁移步骤

以 `PlayerCard` 为例：

**迁移前** (`player_card.py`):
```python
class PlayerCard(QDockWidget):
    position_changed = Signal(int)
    default_area = Qt.LeftDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("视频预览", parent)
        self._setup_ui()
        self._setup_player()
        self._connect_signals()
```

**迁移后**:
```python
class PlayerCard(BaseCard):
    card_id = "player"
    card_title = "视频预览"
    default_area = Qt.LeftDockWidgetArea
    default_ratio = 0.39

    position_changed = Signal(int)

    def _setup_ui(self):
        # 原有 _setup_ui 内容不变
        ...

    def _connect_internal_signals(self):
        # 原有 _connect_signals 内容（仅卡片内部信号）
        ...
```

### 5.2 MainWindow 对应改动

**迁移前** (`main_window.py:_create_cards()`):
```python
self.player_card = PlayerCard(self)
self.player_card.setObjectName("player_card")
self.player_card.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
# ... 对每张卡片重复
```

**迁移后**:
```python
# 注册表自动处理（见 card_registry.md）
for card_id, card in self._cards.items():
    self.addDockWidget(card.default_area, card)
```

---

## 六、状态持久化协议

### 6.1 保存格式

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

### 6.2 自动持久化

基类提供自动收集简单字段的能力（参考 Infernux 的 `EditorPanel` 设计）：

```python
def on_save_state(self) -> dict:
    """默认实现：自动收集可序列化的实例属性。"""
    auto = {}
    for key, value in self.__dict__.items():
        if key.startswith("_"):
            continue
        if isinstance(value, (bool, int, float, str)):
            auto[key] = value
    return {"__auto_state__": auto} if auto else {}
```

子类可以重写此方法以提供自定义持久化逻辑。

---

## 七、依赖

- PySide6: `QDockWidget`, `Qt`, `Signal`
- 无外部模块依赖

---

## 八、注意事项

1. **不要重写 `__init__`** — 使用 `_setup_ui()` 和 `on_init()` 钩子
2. **`card_id` 必须全局唯一** — 重复 ID 会导致注册表冲突
3. **`on_ready()` 中才能访问其他卡片** — 此时所有卡片已创建完毕
4. **`on_save_state()` 返回值必须是 JSON 可序列化的** — 不要包含 QObject 引用
