# 布局配置

> `chestnut_studio/ui/layout_config.py`
> 布局配置数据类，支持从 JSON 文件加载布局配置。

---

## 概述

布局配置提供：
- LayoutConfig 数据类
- 从 JSON 文件加载布局
- 支持多列多行布局
- 支持比例配置

---

## 配置格式

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

---

## 字段说明

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

---

## 数据类

### RowConfig

```python
@dataclass
class RowConfig:
    card: str           # 卡片 ID
    height_ratio: float = 0.5  # 行高占比
```

### ColumnConfig

```python
@dataclass
class ColumnConfig:
    width_ratio: float = 0.5   # 列宽占比
    rows: list[RowConfig] = field(default_factory=list)
```

### LayoutConfig

```python
@dataclass
class LayoutConfig:
    name: str = ""           # 布局名称
    description: str = ""    # 布局描述
    version: int = 1         # 配置格式版本号
    columns: list[ColumnConfig] = field(default_factory=list)
```

---

## API 参考

### LayoutConfig.from_json(path)

从 JSON 文件加载布局配置。

```python
config = LayoutConfig.from_json("resources/layouts/default.json")
```

**参数：**
- `path`: JSON 文件路径

**返回：**
- `LayoutConfig` 实例

### LayoutConfig.from_dict(data)

从字典加载布局配置。

```python
config = LayoutConfig.from_dict({
    "name": "默认布局",
    "columns": [...]
})
```

**参数：**
- `data`: 配置字典

**返回：**
- `LayoutConfig` 实例

### get_builtin_layouts()

加载所有内置布局。

```python
layouts = get_builtin_layouts()
# {"default": LayoutConfig, "compact": LayoutConfig, ...}
```

**返回：**
- `dict[str, LayoutConfig]`: 布局名称 → LayoutConfig 的字典

---

## 内置布局

布局文件目录：

```
chestnut_studio/
  resources/
    layouts/
      default.json      # 默认布局
      compact.json       # 紧凑布局（适合小屏幕）
      wide.json          # 宽屏布局（三列）
      translation.json   # 翻译工作流（翻译面板最大化）
```

---

## 高级布局

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

## 注意事项

1. **卡片 ID 必须与注册表一致** — JSON 中的 `card` 字段对应 `BaseCard.card_id`
2. **比例之和不必为 1.0** — 引擎会按实际比例归一化
3. **缺失的卡片 ID 会被跳过** — 不会报错，只打印警告
4. **版本号用于配置迁移** — 未来格式变更时可通过版本号自动升级旧配置

---

## 依赖

- Python: `json`, `dataclasses`, `importlib.resources`
- chestnut_studio.utils.log_manager: `LogManager`（用于日志输出）
