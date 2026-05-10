# 可扩展架构方案

> 针对卡片数量增长的可扩展性问题，提出系统性的架构改进方案。
> 核心思路：让 MainWindow 只做编排，不做具体知识。

---

## 一、问题描述

### 1.1 现状

当前架构中，`MainWindow` 是所有卡片的"上帝类"——它了解每张卡片的具体细节：

```python
# main_window.py 当前状态
class MainWindow(QMainWindow):
    def _create_cards(self):
        # 硬编码：知道有哪 4 张卡片
        self.player_card = PlayerCard(self)
        self.player_card.setObjectName("player_card")
        self.player_card.setFeatures(...)
        # ... 重复 4 次

    def _setup_default_layout(self):
        # 硬编码：知道每张卡片放在哪里
        self.addDockWidget(Qt.LeftDockWidgetArea, self.player_card)
        self.splitDockWidget(self.player_card, self.waveform_card, Qt.Vertical)
        # ...

    def _connect_signals(self):
        # 硬编码：知道每张卡片有哪些信号，连接到哪里（~70 行）
        self.toolbar.play_clicked.connect(self.player_card.play_pause)
        self.player_card.position_changed.connect(self.waveform_card.update_position)
        # ...
```

### 1.2 新增卡片的成本

新增一张卡片需要改动 **5+ 个位置**：

| 改动位置 | 文件 | 行数 |
|----------|------|------|
| 实例化 | `main_window.py:_create_cards()` | ~5 行 |
| 布局位置 | `main_window.py:_setup_default_layout()` | ~3 行 |
| 信号连线 | `main_window.py:_connect_signals()` | ~N 行 |
| 尺寸比例 | `main_window.py:_apply_layout_size()` | ~2 行 |
| 调试列表 | `main_window.py:_dump_layout_info()` | ~3 行 |
| 菜单显隐 | `menubar.py` | ~3 行 |

**总计：约 20+ 行代码改动，分散在 2-3 个文件中。**

### 1.3 可扩展性瓶颈

| 卡片数量 | `_connect_signals()` 行数 | MainWindow 总行数 | 维护难度 |
|----------|--------------------------|-------------------|----------|
| 4（当前） | ~70 行 | ~786 行 | 可接受 |
| 8 | ~180 行 | ~1200 行 | 困难 |
| 12 | ~300 行 | ~1700 行 | 灾难 |

---

## 二、目标架构

### 2.1 核心原则

> **MainWindow 不应该知道有哪些卡片、每张卡片的信号是什么——这些信息属于卡片自己。**

### 2.2 目标结构

```
MainWindow
  │
  ├─ 只负责编排
  │   ├─ 从注册表自动发现卡片
  │   ├─ 从配置文件自动布局
  │   ├─ 从声明式信号自动连接
  │   └─ 从注册表自动生成菜单
  │
  └─ 不包含任何卡片具体知识
      ├─ 不知道有 PlayerCard 类
      ├─ 不知道 position_changed 信号
      └─ 不知道 player 放在左上角
```

### 2.3 改造后的 MainWindow

```python
class MainWindow(QMainWindow):
    """主窗口 — 纯编排者，不包含卡片具体知识"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chestnut Studio v{get_version()}")
        self.resize(1280, 720)

        self._cards: dict[str, BaseCard] = {}

        # 1. 自动创建所有已注册的卡片
        self._create_cards()

        # 2. 从配置文件自动布局
        self._apply_default_layout()

        # 3. 自动连接信号
        self._connect_signals()

        # 4. 自动构建菜单
        self._create_menubar()

        # 5. 通知所有卡片就绪
        self._notify_ready()

    def _create_cards(self):
        """自动创建所有已注册的卡片"""
        for card_id in get_registry():
            card = create_card(card_id, parent=self)
            if card:
                self._cards[card_id] = card

    def _apply_default_layout(self):
        """从配置文件自动布局"""
        config = LayoutConfig.from_json(...)
        apply_layout(self, config, self._cards)

    def _connect_signals(self):
        """自动连接所有卡片声明的信号"""
        for card_id, card in self._cards.items():
            for source_key, handler in card.listens_to().items():
                self._auto_connect(card, source_key, handler)

    def _create_menubar(self):
        """自动构建菜单"""
        view_menu = build_view_menu(self._cards, ...)
        # ...

    def _notify_ready(self):
        """通知所有卡片就绪"""
        for card in self._cards.values():
            card.on_ready()
```

**对比**：改造后 MainWindow 约 100 行，且**不随卡片数量增长**。

---

## 三、方案组件

### 3.1 组件总览

| 组件 | 文件 | 职责 | 详细文档 |
|------|------|------|----------|
| **BaseCard** | `ui/cards/base_card.py` | 统一基类，生命周期钩子 | [base_card.md](ui/base_card.md) |
| **CardRegistry** | `ui/cards/registry.py` | 卡片自动发现与注册 | [card_registry.md](ui/card_registry.md) |
| **声明式信号** | `ui/cards/base_card.py` | 卡片自描述信号订阅 | [declarative_signals.md](ui/declarative_signals.md) |
| **布局引擎** | `ui/layout_engine.py` | JSON 配置驱动布局 | [layout_system.md](ui/layout_system.md) |
| **菜单生成** | `ui/auto_menu.py` | 注册表驱动菜单构建 | [auto_menu.md](ui/auto_menu.md) |

### 3.2 组件依赖关系

```
BaseCard
  │
  ├─► CardRegistry（装饰器注册）
  │
  ├─► 声明式信号（listens_to() 方法）
  │
  └─► 布局引擎（card_id / default_area / default_ratio）
        │
        └─► 菜单生成（遍历注册表）
```

---

## 四、新增卡片对比

### 4.1 改造前：新增一张卡片

需要改动 **3 个文件，~20 行代码**：

```python
# 1. 创建新文件 cards/subtitle_preview_card.py
class SubtitlePreviewCard(QDockWidget):  # 直接继承 QDockWidget
    ...

# 2. main_window.py — _create_cards()
self.subtitle_preview = SubtitlePreviewCard(self)
self.subtitle_preview.setObjectName("subtitle_preview")
self.subtitle_preview.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
self.subtitle_preview.setMinimumSize(200, 150)

# 3. main_window.py — _setup_default_layout()
self.addDockWidget(Qt.RightDockWidgetArea, self.subtitle_preview)
self.splitDockWidget(self.translate_card, self.subtitle_preview, Qt.Vertical)

# 4. main_window.py — _connect_signals()
self.timeline_card.subtitle_selected.connect(self.subtitle_preview.show_subtitle)
self.player_card.position_changed.connect(self.subtitle_preview.update_position)

# 5. main_window.py — _apply_layout_size()
# 添加到 resizeDocks 列表

# 6. main_window.py — _dump_layout_info()
# 添加到调试列表

# 7. menubar.py
self.toggle_subtitle_preview = QAction("显示字幕预览", self, checkable=True)
# ...
```

### 4.2 改造后：新增一张卡片

**只改 1 个文件（新文件），0 行现有代码改动**：

```python
# cards/subtitle_preview_card.py — 唯一需要创建/修改的文件

from chestnut_studio.ui.cards.base_card import BaseCard
from chestnut_studio.ui.cards.registry import register_card

@register_card
class SubtitlePreviewCard(BaseCard):
    card_id = "subtitle_preview"
    card_title = "字幕预览"
    default_area = Qt.RightDockWidgetArea
    default_ratio = 0.3

    def _setup_ui(self):
        # ...
        pass

    def listens_to(self):
        return {
            "timeline.subtitle_selected": "show_subtitle",
            "player.position_changed": "update_position",
        }
```

然后在 `cards/__init__.py` 加一行导入即可。

---

## 五、实施计划

### Phase 1：BaseCard 基类（1 天）

| 任务 | 说明 |
|------|------|
| 创建 `cards/base_card.py` | 基类定义、生命周期钩子 |
| 迁移 `TranslateCard` 作为试点 | 最简单的卡片，验证基类设计 |
| 运行测试确保无回归 | `uv run pytest tests/ -v` |

### Phase 2：注册表（0.5 天）

| 任务 | 说明 |
|------|------|
| 创建 `cards/registry.py` | 注册表模块 |
| 迁移所有 4 张卡片 | 添加 `@register_card` 装饰器 |
| 更新 `cards/__init__.py` | 确保导入顺序 |

### Phase 3：声明式信号（1 天）

| 任务 | 说明 |
|------|------|
| 在 `BaseCard` 中实现 `listens_to()` | 接口定义 |
| 在所有卡片中实现 `listens_to()` | 声明信号订阅 |
| 改造 `_connect_signals()` | 从手动改为自动 |
| 保留中转处理 | `_get_relay_handlers()` |

### Phase 4：布局引擎（1 天）

| 任务 | 说明 |
|------|------|
| 创建 `layout_config.py` | 配置数据类 |
| 创建 `layout_engine.py` | 布局应用引擎 |
| 创建 `resources/layouts/default.json` | 默认布局配置 |
| 改造 `_setup_default_layout()` | 从硬编码改为配置驱动 |

### Phase 5：菜单自动生成（0.5 天）

| 任务 | 说明 |
|------|------|
| 创建 `auto_menu.py` | 菜单生成模块 |
| 改造 `_create_menubar()` | 视图菜单自动生成 |

### Phase 6：清理（0.5 天）

| 任务 | 说明 |
|------|------|
| 删除 `MainWindow` 中的硬编码 | 清理残留代码 |
| 更新文档 | 同步更新 `docs/architecture.md` |
| 补充测试 | 注册表、布局引擎的单元测试 |

---

## 六、总工作量

| 阶段 | 工作量 | 风险 |
|------|--------|------|
| Phase 1: BaseCard | 1 天 | 低 |
| Phase 2: 注册表 | 0.5 天 | 低 |
| Phase 3: 声明式信号 | 1 天 | 中（需要确保所有连线正确） |
| Phase 4: 布局引擎 | 1 天 | 低 |
| Phase 5: 菜单生成 | 0.5 天 | 低 |
| Phase 6: 清理 | 0.5 天 | 低 |
| **合计** | **4.5 天** | |

---

## 七、收益

### 7.1 新增卡片成本

| 方面 | 改造前 | 改造后 |
|------|--------|--------|
| 改动文件数 | 2-3 个 | 1 个（新文件） |
| 改动现有代码行数 | ~20 行 | 0 行 |
| 需要了解的框架知识 | MainWindow 内部细节 | BaseCard 接口 |
| 菜单自动更新 | 否 | 是 |
| 布局自动更新 | 否 | 是 |

### 7.2 MainWindow 复杂度

| 指标 | 改造前 | 改造后 |
|------|--------|--------|
| MainWindow 总行数 | ~786 行 | ~100 行 |
| 随卡片增长 | 线性增长 | **不增长** |
| `_connect_signals()` 行数 | ~70 行 | ~10 行 |

### 7.3 可维护性

- **单一职责**：每张卡片自包含（ID、信号、布局声明都在卡片自身）
- **关注点分离**：MainWindow 只做编排，不做具体知识
- **开闭原则**：新增卡片不需要修改现有代码
- **可测试性**：注册表、布局引擎可以独立测试

---

## 八、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 迁移期间新旧代码混合 | 混乱 | 渐进式迁移，每阶段独立可运行 |
| 声明式信号连线错误 | 功能异常 | 自动连接时打印日志，便于调试 |
| 布局配置 JSON 格式错误 | 启动失败 | 加载失败时回退到默认布局 |
| 卡片间复杂依赖 | 无法声明式表达 | 中转处理兜底，复杂逻辑留在 MainWindow |

---

## 九、与现有架构的关系

本方案**不改变**现有架构的分层原则：

```
UI 层 (ui/)          → 依赖核心层和工具层，依赖 PySide6
核心层 (core/)        → 只依赖工具层，不依赖 PySide6
工具层 (utils/)       → 无外部依赖
```

改动范围**仅限 UI 层内部**的卡片管理机制：

| 改动 | 不改动 |
|------|--------|
| `ui/cards/base_card.py` (新增) | `core/` 目录 |
| `ui/cards/registry.py` (新增) | `utils/` 目录 |
| `ui/layout_config.py` (新增) | 各卡片的 `_setup_ui()` 内部逻辑 |
| `ui/layout_engine.py` (新增) | 信号定义（信号本身不变） |
| `ui/auto_menu.py` (新增) | 核心层数据结构 |
| `ui/main_window.py` (简化) | 工具栏、状态栏、拖放覆盖层 |
