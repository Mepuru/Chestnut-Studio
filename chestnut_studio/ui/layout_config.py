"""布局配置模块

定义布局配置的数据类，支持从 JSON 文件加载布局配置。

配置格式示例：
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
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RowConfig:
    """行配置"""
    card: str
    """卡片 ID（对应 BaseCard.card_id）"""
    height_ratio: float = 0.5
    """行高在列内的占比 (0.0 ~ 1.0)"""


@dataclass
class ColumnConfig:
    """列配置"""
    width_ratio: float = 0.5
    """列宽占比 (0.0 ~ 1.0)"""
    rows: list[RowConfig] = field(default_factory=list)
    """行配置列表"""


@dataclass
class LayoutConfig:
    """布局配置"""
    name: str = ""
    """布局名称，显示在菜单中"""
    description: str = ""
    """布局描述"""
    version: int = 1
    """配置格式版本号，用于迁移"""
    columns: list[ColumnConfig] = field(default_factory=list)
    """列配置列表"""

    @classmethod
    def from_json(cls, path: str | Path) -> LayoutConfig:
        """从 JSON 文件加载布局配置。

        Args:
            path: JSON 文件路径

        Returns:
            LayoutConfig 实例
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls._from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> LayoutConfig:
        """从字典加载布局配置。

        Args:
            data: 配置字典

        Returns:
            LayoutConfig 实例
        """
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> LayoutConfig:
        """从字典解析配置。"""
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


def get_builtin_layouts() -> dict[str, LayoutConfig]:
    """加载所有内置布局。

    Returns:
        布局名称 -> LayoutConfig 的字典
    """
    import importlib.resources

    layouts = {}
    try:
        layouts_dir = importlib.resources.files("chestnut_studio") / "resources" / "layouts"
        if layouts_dir.is_dir():
            for path in layouts_dir.glob("*.json"):
                try:
                    config = LayoutConfig.from_json(path)
                    layouts[path.stem] = config
                except Exception as e:
                    print(f"[Layout] 加载 {path.name} 失败: {e}")
    except Exception:
        pass

    return layouts
