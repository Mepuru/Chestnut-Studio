# 信号管理器

> `chestnut_studio/ui/signal_manager.py`
> 集中管理所有卡片和组件间的信号连接，让 MainWindow 不需要关心信号细节。

---

## 概述

SignalManager 负责：
- 收集所有卡片的信号声明（@subscribe 装饰器 + listens_to() 方法）
- 管理中转处理函数（@relay 装饰器）
- 管理动态订阅（状态栏等）
- 自动连接所有信号

---

## 使用方式

```python
# MainWindow 中使用
class MainWindow(QMainWindow):
    def __init__(self):
        self._signal_manager = SignalManager(self)
        # ...
        self._connect_signals()

    def _connect_signals(self):
        # 注册主窗口（收集 @relay 装饰器声明）
        self._signal_manager.register_main_window(self)

        # 注册卡片和特殊组件
        self._signal_manager.register_cards(self._cards)
        self._signal_manager.register_special("toolbar", self.toolbar)
        self._signal_manager.register_special("statusbar", self.status_bar)

        # 注册状态栏动态订阅
        self._signal_manager.register_dynamic_relay(
            "player.position_changed", self._on_position_changed
        )

        # 自动连接所有信号
        self._signal_manager.connect_all()
```

---

## API 参考

### __init__(main_window)

初始化信号管理器。

**参数：**
- `main_window`: 主窗口实例

### register_main_window(main_window)

注册主窗口，自动收集 @relay 装饰器声明。

```python
signal_mgr.register_main_window(self)
```

### register_cards(cards)

注册所有卡片。

```python
signal_mgr.register_cards(self._cards)
```

**参数：**
- `cards`: `dict[str, BaseCard]` — card_id → BaseCard 实例

### register_special(component_id, component)

注册特殊组件（toolbar、statusbar 等）。

```python
signal_mgr.register_special("toolbar", self.toolbar)
signal_mgr.register_special("statusbar", self.status_bar)
```

**参数：**
- `component_id`: 组件标识符
- `component`: 组件实例

### register_relay(source_key, handler)

注册中转处理函数。

```python
signal_mgr.register_relay("player.video_opened", self._on_video_opened)
```

**参数：**
- `source_key`: 格式 `"card_id.signal_name"`
- `handler`: 处理函数

### register_relays(relays)

批量注册中转处理函数。

```python
signal_mgr.register_relays({
    "player.video_opened": self._on_video_opened,
    "translate.jump_to_next": self._on_jump_to_next,
})
```

### register_dynamic_relay(source_key, handler)

注册动态中转处理函数（可多个）。

用于非卡片组件订阅信号，如状态栏订阅播放位置。

```python
signal_mgr.register_dynamic_relay(
    "player.position_changed", self._on_position_changed
)
```

### connect_all()

自动连接所有信号。

**连接顺序：**
1. 中转处理函数（@relay 装饰器）
2. 动态中转处理函数
3. 卡片间声明式信号（@subscribe + listens_to()）
4. 特殊组件声明式信号（listens_to()）

### get_component(component_id)

获取组件（卡片或特殊组件）。

```python
card = signal_mgr.get_component("player")
toolbar = signal_mgr.get_component("toolbar")
```

---

## 信号来源分类

| 来源 | 声明方式 | 收集方法 | 示例 |
|------|----------|----------|------|
| **卡片订阅** | `@subscribe` 或 `listens_to()` | `register_cards()` | WaveformCard 订阅 player 信号 |
| **MainWindow 中转** | `@relay` | `register_main_window()` | video_opened → 加载波形 |
| **特殊组件订阅** | `listens_to()` | `register_special()` | Toolbar 订阅 player 信号 |
| **动态订阅** | 手动调用 | `register_dynamic_relay()` | 状态栏订阅播放位置 |

---

## 注意事项

1. **信号源必须已注册或在特殊组件中** — 否则解析失败
2. **处理函数必须是卡片的公开方法** — 私有方法也可，但建议用公开方法
3. **避免循环订阅** — A 订阅 B 的信号，B 又订阅 A 的同一信号可能导致无限循环
4. **中转处理优先** — 如果 MainWindow 的 @relay 匹配了某个信号，卡片的 listens_to() 中对应条目会被跳过

---

## 依赖

- `chestnut_studio.ui.cards.base_card`: BaseCard 基类
- `chestnut_studio.ui.cards.registry`: 卡片注册表
- `chestnut_studio.ui.signal_decorator`: 信号装饰器
- `chestnut_studio.utils.log_manager`: LogManager（用于日志输出）
