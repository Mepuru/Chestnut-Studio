# 配置驱动布局系统

> `chestnut_studio/ui/layout_config.py` + `chestnut_studio/ui/layouts/default.json`
> 用 JSON 配置文件替代硬编码的布局逻辑，支持多套布局方案和用户自定义。

---

## 一、动机

### 1.1 现状问题

布局完全硬编码在 `MainWindow` 中：

```python
# main_window.py — 布局相关代码约 80 行
def _create_cards(self):           # 实例化 4 张卡片
def _setup_default_layout(self):   # addDockWidget + splitDockWidget
def _apply_layout_size(self):      # resizeDocks 计算比例
def resizeEvent(self, event):      # 维护比例
def _dump_layout_info(self):       # 调试输出
```

**问题**：

- 改布局需要改 Python 代码
- 不支持用户自定义布局
- 不支持多套布局方案切换
- 新增卡片需要修改布局方法

### 1.2 设计目标

- 布局配置外置为 JSON 文件
- 支持多套内置布局（如默认、紧凑、宽屏）
- 支持用户自定义布局并持久化
- 新增卡片只需在配置中添加条目

---

## 二、配置格式

### 2.1 JSON Schema

```json
{
  "name": "默认布局",
  "description": "左 39% 右 61%，上 56% 下 44%",
  "version": 1,
  "columns": [
    {
      "width_ratio": 0.39,
      "rows": [
        { "card": "player", "height_ratio": 0.56 },
        { "card": "waveform", "height_ratio": 0.44 }
      ]
    },
    {
      "width_ratio": 0.61,
      "rows": [
        { "card": "timeline", "height_ratio": 0.56 },
        { "card": "translate", "height_ratio": 0.44 }
      ]
    }
  ]
}
```

### 2.2 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 布局名称，显示在菜单中 |
| `description` | `str` | 布局描述 |
| `version` | `int` | 配置格式版本号，用于迁移 |
| `columns` | `list` | 列定义，从左到右 |
| `columns[].width_ratio` | `float` | 列宽占比 (0.0 ~ 1.0) |
| `columns[].rows` | `list` | 行定义，从上到下 |
| `columns[].rows[].card` | `str` | 卡片 ID（对应 `BaseCard.card_id`） |
| `columns[].rows[].height_ratio` | `float` | 行高在列内的占比 (0.0 ~ 1.0) |

### 2.3 高级布局

支持不规则布局（如三列、嵌套分割）：

```json
{
  "name": "宽屏布局",
  "columns": [
    {
      "width_ratio": 0.25,
      "rows": [
        { "card": "player", "height_ratio": 1.0 }
      ]
    },
    {
      "width_ratio": 0.50,
      "rows": [
        { "card": "waveform", "height_ratio": 0.6 },
        { "card": "timeline", "height_ratio": 0.4 }
      ]
    },
    {
      "width_ratio": 0.25,
      "rows": [
        { "card": "translate", "height_ratio": 1.0 }
      ]
    }
  ]
}
```

---

## 三、布局引擎

### 3.1 配置加载

```python
# chestnut_studio/ui/layout_config.py

from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RowConfig:
    card: str
    height_ratio: float = 0.5


@dataclass
class ColumnConfig:
    width_ratio: float = 0.5
    rows: list[RowConfig] = field(default_factory=list)


@dataclass
class LayoutConfig:
    name: str = ""
    description: str = ""
    version: int = 1
    columns: list[ColumnConfig] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: str | Path) -> LayoutConfig:
        """从 JSON 文件加载布局配置。"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls._from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> LayoutConfig:
        """从字典加载布局配置。"""
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> LayoutConfig:
        config = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", 1),
        )
        for col_data in data.get("columns", []):
            col = ColumnConfig(width_ratio=col_data.get("width_ratio", 0.5))
            for row_data in col_data.get("rows", []):
                row = RowConfig(
                    card=row_data.get("card", ""),
                    height_ratio=row_data.get("height_ratio", 0.5),
                )
                col.rows.append(row)
            config.columns.append(col)
        return config
```

### 3.2 布局应用引擎

```python
# chestnut_studio/ui/layout_engine.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QDockWidget

from chestnut_studio.ui.layout_config import LayoutConfig


def apply_layout(
    window: QMainWindow,
    config: LayoutConfig,
    cards: dict[str, QDockWidget],
) -> None:
    """将布局配置应用到 MainWindow。

    Args:
        window: 主窗口实例
        config: 布局配置
        cards: card_id → QDockWidget 实例映射
    """
    # 1. 移除所有现有卡片
    for card in cards.values():
        window.removeDockWidget(card)

    # 2. 按列布局
    first_in_row = []
    for col_idx, col_config in enumerate(config.columns):
        first_in_row.append(None)

        for row_idx, row_config in enumerate(col_config.rows):
            card = cards.get(row_config.card)
            if card is None:
                continue

            area = Qt.LeftDockWidgetArea if col_idx == 0 else Qt.RightDockWidgetArea

            if row_idx == 0:
                # 列的第一行：直接添加到区域
                window.addDockWidget(area, card)
                first_in_row[col_idx] = card
            else:
                # 后续行：与列首垂直分割
                window.splitDockWidget(first_in_row[col_idx], card, Qt.Vertical)

    # 3. 应用尺寸比例
    _apply_sizes(window, config, cards)


def _apply_sizes(
    window: QMainWindow,
    config: LayoutConfig,
    cards: dict[str, QDockWidget],
) -> None:
    """按配置比例调整各卡片尺寸。"""
    win_w = window.width()
    win_h = window.height() - 45  # 减去工具栏/菜单栏

    # 水平比例
    h_docks = []
    h_sizes = []
    for col_config in config.columns:
        for row_config in col_config.rows:
            card = cards.get(row_config.card)
            if card:
                h_docks.append(card)
                h_sizes.append(int(win_w * col_config.width_ratio))

    if h_docks:
        window.resizeDocks(h_docks, h_sizes, Qt.Horizontal)

    # 垂直比例
    v_docks = []
    v_sizes = []
    for col_config in config.columns:
        col_h = int(win_h)  # 整列高度
        for row_config in col_config.rows:
            card = cards.get(row_config.card)
            if card:
                v_docks.append(card)
                v_sizes.append(int(col_h * row_config.height_ratio))

    if v_docks:
        window.resizeDocks(v_docks, v_sizes, Qt.Vertical)
```

---

## 四、内置布局

### 4.1 布局文件目录

```
chestnut_studio/
  resources/
    layouts/
      default.json      # 默认布局
      compact.json       # 紧凑布局（适合小屏幕）
      wide.json          # 宽屏布局（三列）
      translation.json   # 翻译工作流（翻译面板最大化）
```

### 4.2 加载内置布局

```python
# chestnut_studio/ui/layout_config.py

import importlib.resources

def get_builtin_layouts() -> dict[str, LayoutConfig]:
    """加载所有内置布局。"""
    layouts = {}
    layouts_dir = importlib.resources.files("chestnut_studio") / "resources" / "layouts"

    for path in layouts_dir.glob("*.json"):
        try:
            config = LayoutConfig.from_json(path)
            layouts[path.stem] = config
        except Exception as e:
            print(f"[Layout] 加载 {path.name} 失败: {e}")

    return layouts
```

---

## 五、用户自定义布局

### 5.1 保存当前布局为配置

```python
def save_current_layout(
    window: QMainWindow,
    cards: dict[str, QDockWidget],
    name: str = "自定义布局",
) -> dict:
    """将当前窗口布局导出为配置字典。

    通过查询各卡片的 dockWidgetArea 和相对尺寸生成配置。
    """
    config = {"name": name, "version": 1, "columns": []}

    # 按区域分组
    left_cards = []
    right_cards = []
    for card_id, card in cards.items():
        area = window.dockWidgetArea(card)
        if area == Qt.LeftDockWidgetArea:
            left_cards.append(card_id)
        elif area == Qt.RightDockWidgetArea:
            right_cards.append(card_id)

    # 生成列配置
    if left_cards:
        config["columns"].append({
            "width_ratio": 0.39,
            "rows": [{"card": cid, "height_ratio": 1.0 / len(left_cards)} for cid in left_cards],
        })
    if right_cards:
        config["columns"].append({
            "width_ratio": 0.61,
            "rows": [{"card": cid, "height_ratio": 1.0 / len(right_cards)} for cid in right_cards],
        })

    return config
```

### 5.2 持久化用户布局

```python
from PySide6.QtCore import QSettings

def save_custom_layout(config: dict) -> None:
    """保存用户自定义布局到 QSettings。"""
    settings = QSettings("ChestnutStudio", "KaoRouTool")
    settings.setValue("custom_layout", json.dumps(config, ensure_ascii=False))

def load_custom_layout() -> dict | None:
    """加载用户自定义布局。"""
    settings = QSettings("ChestnutStudio", "KaoRouTool")
    data = settings.value("custom_layout")
    if data:
        return json.loads(data)
    return None
```

---

## 六、菜单集成

布局切换菜单自动生成（详见 [auto_menu.md](auto_menu.md)）：

```
视图 ─┬─ 布局 ─┬─ 默认布局
      │        ├─ 紧凑布局
      │        ├─ 宽屏布局
      │        ├─ 翻译工作流
      │        ├─ ──────
      │        ├─ 保存当前布局...
      │        └─ 重置为默认
      │
      ├─ 显示/隐藏卡片 ─┬─ 视频播放 [✓]
      │                 ├─ 音频波形 [✓]
      │                 ├─ 时间轴   [✓]
      │                 └─ 翻译面板 [✓]
      ...
```

---

## 七、MainWindow 集成

### 7.1 改造后的 MainWindow

```python
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ...
        self._cards: dict[str, BaseCard] = {}
        self._create_cards()
        self._apply_default_layout()

    def _apply_default_layout(self):
        """应用默认布局"""
        config = LayoutConfig.from_json(
            importlib.resources.files("chestnut_studio") / "resources" / "layouts" / "default.json"
        )
        apply_layout(self, config, self._cards)

    def _apply_layout(self, config: LayoutConfig):
        """应用指定布局"""
        apply_layout(self, config, self._cards)

    def resizeEvent(self, event):
        """窗口大小变化时重新应用比例"""
        super().resizeEvent(event)
        if hasattr(self, "_current_layout"):
            _apply_sizes(self, self._current_layout, self._cards)
```

### 7.2 对比

| 方面 | 改造前 | 改造后 |
|------|--------|--------|
| 新增卡片 | 改 5 个方法 | 改 JSON 配置文件 |
| 调整布局 | 改 Python 代码 | 改 JSON 配置文件 |
| 用户自定义 | 不支持 | 支持保存/加载 |
| 多套布局 | 不支持 | 多个 JSON 文件 |

---

## 八、依赖

- PySide6: `QMainWindow`, `QDockWidget`, `Qt`
- Python: `json`, `dataclasses`, `importlib.resources`
- `chestnut_studio.ui.cards.base_card`: BaseCard 基类
- `chestnut_studio.ui.cards.registry`: 卡片注册表

---

## 九、注意事项

1. **卡片 ID 必须与注册表一致** — JSON 中的 `card` 字段对应 `BaseCard.card_id`
2. **比例之和不必为 1.0** — 引擎会按实际比例归一化
3. **缺失的卡片 ID 会被跳过** — 不会报错，只打印警告
4. **`resizeEvent` 中只更新尺寸比例** — 不重新排列卡片位置
5. **版本号用于配置迁移** — 未来格式变更时可通过版本号自动升级旧配置
