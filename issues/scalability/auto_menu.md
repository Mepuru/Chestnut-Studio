# 菜单自动生成

> 基于卡片注册表自动构建"视图"菜单，新增卡片零维护成本。

---

## 一、动机

### 1.1 现状问题

"视图"菜单中的显示/隐藏选项需要手动维护：

```python
# menubar.py — 当前需要手动添加每个 toggle action
self.toggle_player = QAction("显示视频播放", self, checkable=True)
self.toggle_player.setChecked(True)
self.toggle_player.triggered.connect(lambda checked: self._toggle_card("player", checked))
# ... 每张卡片重复
```

新增卡片时，必须同步修改 `menubar.py`。

### 1.2 设计目标

- "显示/隐藏卡片"菜单项从注册表自动生成
- "布局"子菜单从布局配置自动生成
- 新增卡片后菜单自动更新，无需改代码

---

## 二、自动生成机制

### 2.1 视图菜单结构

```
视图 ─┬─ 显示/隐藏 ─┬─ 视频播放      [✓]    ← 自动生成
      │              ├─ 音频波形      [✓]    ← 自动生成
      │              ├─ 时间轴        [✓]    ← 自动生成
      │              ├─ 翻译面板      [✓]    ← 自动生成
      │              └─ 字幕预览      [✓]    ← 新增卡片自动出现
      │
      ├─ 布局 ──────┬─ 默认布局              ← 从 layouts/ 自动生成
      │             ├─ 紧凑布局
      │             ├─ 宽屏布局
      │             ├─ ──────
      │             ├─ 保存当前布局...
      │             ├─ 加载布局...
      │             └─ 重置为默认
      │
      ├─ 工具栏      [✓]
      ├─ 状态栏      [✓]
      └─ 全屏
```

### 2.2 自动生成代码

```python
# chestnut_studio/ui/auto_menu.py

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenu

if TYPE_CHECKING:
    from chestnut_studio.ui.cards.base_card import BaseCard
    from chestnut_studio.ui.layout_config import LayoutConfig


def build_view_menu(
    parent,
    cards: dict[str, BaseCard],
    layouts: dict[str, LayoutConfig],
    on_toggle_card: callable,
    on_apply_layout: callable,
    on_reset_layout: callable,
) -> QMenu:
    """自动构建"视图"菜单。

    Args:
        parent: 菜单父对象
        cards: card_id → BaseCard 实例
        layouts: layout_name → LayoutConfig
        on_toggle_card: (card_id: str, visible: bool) -> None
        on_apply_layout: (layout_name: str) -> None
        on_reset_layout: () -> None

    Returns:
        构建好的 QMenu
    """
    menu = QMenu("视图(&V)", parent)

    # ── 显示/隐藏卡片子菜单 ──
    card_submenu = menu.addMenu("显示/隐藏卡片")
    card_actions: dict[str, QAction] = {}

    for card_id, card in cards.items():
        action = QAction(card.card_title or card_id, parent, checkable=True)
        action.setChecked(card.isVisible())
        action.triggered.connect(lambda checked, cid=card_id: on_toggle_card(cid, checked))
        card_submenu.addAction(action)
        card_actions[card_id] = action

    menu.addSeparator()

    # ── 布局子菜单 ──
    if layouts:
        layout_submenu = menu.addMenu("布局")
        layout_group = QActionGroup(parent)
        layout_group.setExclusive(True)

        for name, config in layouts.items():
            action = QAction(config.name or name, parent, checkable=True)
            action.setActionGroup(layout_group)
            action.triggered.connect(lambda checked, n=name: on_apply_layout(n))
            layout_submenu.addAction(action)

        layout_submenu.addSeparator()

        # 保存/加载/重置
        save_action = QAction("保存当前布局...", parent)
        save_action.triggered.connect(lambda: _on_save_layout(parent, cards))
        layout_submenu.addAction(save_action)

        reset_action = QAction("重置为默认", parent)
        reset_action.triggered.connect(on_reset_layout)
        layout_submenu.addAction(reset_action)

    menu.addSeparator()

    # ── 固定菜单项 ──
    # 工具栏、状态栏等由 MainWindow 手动添加
    # 留出占位

    return menu, card_actions


def _on_save_layout(parent, cards: dict[str, BaseCard]):
    """弹出对话框保存当前布局。"""
    from PySide6.QtWidgets import QInputDialog
    from chestnut_studio.ui.layout_engine import save_current_layout
    from chestnut_studio.ui.auto_menu import save_custom_layout

    name, ok = QInputDialog.getText(parent, "保存布局", "布局名称:")
    if ok and name:
        config = save_current_layout(parent, cards, name=name)
        save_custom_layout(config)
```

---

## 三、MainWindow 集成

### 3.1 改造后的菜单创建

```python
# main_window.py

def _create_menubar(self):
    """创建菜单栏"""
    self.menu_bar = QMenuBar(self)
    self.setMenuBar(self.menu_bar)

    # 文件菜单（手动，因为不依赖注册表）
    self._build_file_menu()

    # 视图菜单（自动生成）
    from chestnut_studio.ui.auto_menu import build_view_menu
    from chestnut_studio.ui.layout_config import get_builtin_layouts

    view_menu, self._card_actions = build_view_menu(
        parent=self.menu_bar,
        cards=self._cards,
        layouts=get_builtin_layouts(),
        on_toggle_card=self._on_toggle_card,
        on_apply_layout=self._on_apply_layout,
        on_reset_layout=self._setup_default_layout,
    )
    self.menu_bar.addMenu(view_menu)

    # 帮助菜单（手动）
    self._build_help_menu()
```

### 3.2 卡片显隐控制

```python
def _on_toggle_card(self, card_id: str, visible: bool):
    """切换卡片显示/隐藏"""
    card = self._cards.get(card_id)
    if card:
        card.setVisible(visible)
```

---

## 四、新增卡片的完整流程

新增一张卡片后，菜单自动更新的完整流程：

```
1. 创建新卡片文件
   │
   ├─► cards/subtitle_preview_card.py
   │     @register_card
   │     class SubtitlePreviewCard(BaseCard):
   │         card_id = "subtitle_preview"
   │         card_title = "字幕预览"
   │
2. 在 cards/__init__.py 中添加导入
   │
   ├─► from chestnut_studio.ui.cards.subtitle_preview_card import SubtitlePreviewCard
   │
3. （可选）在布局 JSON 中添加位置
   │
   ├─► resources/layouts/default.json 中添加:
   │     { "card": "subtitle_preview", "height_ratio": 0.3 }
   │
4. 启动应用
   │
   ├─► 注册表自动包含 "subtitle_preview"
   ├─► 布局引擎自动放置卡片
   └─► 视图菜单自动出现 "字幕预览 [✓]"
```

**全程不需要改 `MainWindow`、`MenuBar` 或任何现有代码。**

---

## 五、扩展：右键上下文菜单

卡片标题栏右键菜单也可以自动生成：

```python
def build_card_context_menu(card: BaseCard) -> QMenu:
    """为卡片生成右键上下文菜单。"""
    menu = QMenu()

    # 浮动/停靠
    float_action = QAction("浮动" if not card.isFloating() else "停靠", menu)
    float_action.triggered.connect(lambda: card.setFloating(not card.isFloating()))
    menu.addAction(float_action)

    menu.addSeparator()

    # 关闭
    close_action = QAction("隐藏", menu)
    close_action.triggered.connect(lambda: card.setVisible(False))
    menu.addAction(close_action)

    return menu
```

---

## 六、依赖

- PySide6: `QMenu`, `QAction`, `QActionGroup`
- `chestnut_studio.ui.cards.registry`: 卡片注册表
- `chestnut_studio.ui.layout_config`: 布局配置

---

## 七、注意事项

1. **卡片标题支持 i18n** — `card_title` 可以是 i18n key，显示时通过 `t()` 翻译
2. **菜单顺序由注册表顺序决定** — 通过卡片的 `order` 属性控制
3. **布局菜单中的勾选状态** — 需要在布局切换时同步更新
4. **快捷键** — 显隐快捷键可以注册到 `MainWindow.keyPressEvent`
