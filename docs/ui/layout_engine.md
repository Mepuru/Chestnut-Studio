# 布局引擎

> `chestnut_studio/ui/layout_engine.py`
> 根据 LayoutConfig 将卡片应用到 MainWindow 的布局。

---

## 概述

布局引擎提供：
- `apply_layout()` — 将布局配置应用到 MainWindow
- `save_current_layout()` — 将当前布局导出为配置字典

---

## API 参考

### apply_layout(window, config, cards)

将布局配置应用到 MainWindow。

```python
from chestnut_studio.ui.layout_engine import apply_layout
from chestnut_studio.ui.layout_config import LayoutConfig

config = LayoutConfig.from_json("resources/layouts/default.json")
apply_layout(self, config, self._cards)
```

**参数：**
- `window`: QMainWindow 实例
- `config`: LayoutConfig 实例
- `cards`: `dict[str, QDockWidget]` — card_id → QDockWidget 实例映射

**执行流程：**
1. 移除所有现有卡片
2. 按列布局（第一行直接添加，后续行垂直分割）
3. 确保所有卡片可见
4. 应用尺寸比例

---

### save_current_layout(window, cards, name)

将当前窗口布局导出为配置字典。

```python
from chestnut_studio.ui.layout_engine import save_current_layout

config = save_current_layout(self, self._cards, name="自定义布局")
```

**参数：**
- `window`: QMainWindow 实例
- `cards`: `dict[str, QDockWidget]` — card_id → QDockWidget 实例映射
- `name`: 布局名称

**返回：**
- 布局配置字典

---

## 使用示例

### 应用默认布局

```python
from chestnut_studio.ui.layout_config import LayoutConfig
from chestnut_studio.ui.layout_engine import apply_layout

class MainWindow(QMainWindow):
    def _apply_default_layout(self):
        config = LayoutConfig.from_json(
            importlib.resources.files("chestnut_studio") / "resources" / "layouts" / "default.json"
        )
        apply_layout(self, config, self._cards)
```

### 切换布局

```python
def _on_apply_layout(self, layout_name: str):
    layouts = get_builtin_layouts()
    config = layouts.get(layout_name)
    if config:
        apply_layout(self, config, self._cards)
        self._current_layout = config
```

### 保存当前布局

```python
def _on_save_layout(self):
    config = save_current_layout(self, self._cards, name="自定义布局")
    save_custom_layout(config)
```

---

## 布局实现细节

### 列布局

- 第一列：添加到 `Qt.LeftDockWidgetArea`
- 其他列：添加到 `Qt.RightDockWidgetArea`

### 行布局

- 每列第一行：直接添加到区域
- 后续行：与列首垂直分割（`splitDockWidget`）

### 尺寸比例

- 水平比例：按列宽比例调整
- 垂直比例：按行高比例调整

---

## 注意事项

1. **卡片 ID 必须与注册表一致** — 配置中的 `card` 字段对应 `BaseCard.card_id`
2. **缺失的卡片会被跳过** — 不会报错，只打印警告
3. **比例之和不必为 1.0** — 引擎会按实际比例归一化
4. **resizeEvent 中只更新尺寸比例** — 不重新排列卡片位置

---

## 依赖

- PySide6: `QMainWindow`, `QDockWidget`, `Qt`
- `chestnut_studio.ui.layout_config`: LayoutConfig
