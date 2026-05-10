# 菜单自动生成

> `chestnut_studio/ui/auto_menu.py`
> 基于卡片注册表自动构建"视图"菜单，新增卡片零维护成本。

---

## 概述

菜单自动生成提供：
- `build_card_submenu()` — 自动生成"显示/隐藏卡片"子菜单
- `build_layout_submenu()` — 自动生成"布局"子菜单

---

## API 参考

### build_card_submenu(parent, cards, on_toggle_card)

自动构建"显示/隐藏卡片"子菜单。

```python
from chestnut_studio.ui.auto_menu import build_card_submenu

card_submenu = build_card_submenu(
    parent=self.menu_bar,
    cards=self._cards,
    on_toggle_card=self._on_toggle_card,
)
```

**参数：**
- `parent`: 菜单父对象
- `cards`: `dict[str, BaseCard]` — card_id → BaseCard 实例
- `on_toggle_card`: `(card_id: str, visible: bool) -> None`

**返回：**
- 构建好的 QMenu

---

### build_layout_submenu(parent, layouts, on_apply_layout, on_reset_layout)

自动构建"布局"子菜单。

```python
from chestnut_studio.ui.auto_menu import build_layout_submenu
from chestnut_studio.ui.layout_config import get_builtin_layouts

layout_submenu = build_layout_submenu(
    parent=self.menu_bar,
    layouts=get_builtin_layouts(),
    on_apply_layout=self._on_apply_layout,
    on_reset_layout=self._setup_default_layout,
)
```

**参数：**
- `parent`: 菜单父对象
- `layouts`: `dict[str, LayoutConfig]` — layout_name → LayoutConfig
- `on_apply_layout`: `(layout_name: str) -> None`
- `on_reset_layout`: `() -> None`

**返回：**
- 构建好的 QMenu

---

## 使用示例

### MainWindow 集成

```python
from chestnut_studio.ui.auto_menu import build_card_submenu, build_layout_submenu
from chestnut_studio.ui.layout_config import get_builtin_layouts

class MainWindow(QMainWindow):
    def _create_menubar(self):
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        # 自动生成卡片子菜单
        card_submenu = build_card_submenu(
            parent=self.menu_bar,
            cards=self._cards,
            on_toggle_card=self._on_toggle_card,
        )
        self.menu_bar.set_card_submenu(card_submenu)

        # 自动生成布局子菜单
        layouts = get_builtin_layouts()
        layout_submenu = build_layout_submenu(
            parent=self.menu_bar,
            layouts=layouts,
            on_apply_layout=self._on_apply_layout,
            on_reset_layout=self._setup_default_layout,
        )
        self.menu_bar.set_layout_submenu(layout_submenu)

    def _on_toggle_card(self, card_id: str, visible: bool):
        card = self._cards.get(card_id)
        if card:
            card.setVisible(visible)

    def _on_apply_layout(self, layout_name: str):
        layouts = get_builtin_layouts()
        config = layouts.get(layout_name)
        if config:
            apply_layout(self, config, self._cards)
```

---

## 菜单结构

```
视图 ─┬─ 显示/隐藏卡片 ─┬─ 视频播放      [✓]
      │                 ├─ 音频波形      [✓]
      │                 ├─ 时间轴        [✓]
      │                 ├─ 翻译面板      [✓]
      │                 └─ 字幕预览      [✓]  ← 新增卡片自动出现
      │
      ├─ 布局 ─────────┬─ 默认布局
      │                ├─ 紧凑布局
      │                ├─ 宽屏布局
      │                ├─ ──────
      │                ├─ 保存当前布局...
      │                └─ 重置为默认
      │
      ├─ 工具栏         [✓]
      ├─ 状态栏         [✓]
      └─ 全屏
```

---

## 新增卡片的完整流程

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

**全程不需要改 MainWindow、MenuBar 或任何现有代码。**

---

## 注意事项

1. **卡片标题支持 i18n** — `card_title` 可以是 i18n key，显示时通过 `t()` 翻译
2. **菜单顺序由注册表顺序决定** — 通过卡片的 `order` 属性控制
3. **布局菜单中的勾选状态** — 需要在布局切换时同步更新
4. **快捷键** — 显隐快捷键可以注册到 `MainWindow.keyPressEvent`

---

## 依赖

- PySide6: `QMenu`, `QAction`, `QActionGroup`
- `chestnut_studio.ui.cards.registry`: 卡片注册表
- `chestnut_studio.ui.layout_config`: 布局配置
