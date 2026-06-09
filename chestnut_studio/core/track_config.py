"""轨道配置（向后兼容重导出）

实际定义位于 core/model/config.py。
新代码应从 core.model.config 导入。
"""

from chestnut_studio.core.model.config import (
    DEFAULT_TRACK_COUNT,
    MAX_TRACK_COUNT,
    NOTE_TYPES,
    TRACK_COLORS_HEX,
    get_track_bg_color_hex,
    get_track_color,
)

__all__ = [
    "DEFAULT_TRACK_COUNT",
    "MAX_TRACK_COUNT",
    "NOTE_TYPES",
    "TRACK_COLORS_HEX",
    "get_track_color",
    "get_track_bg_color_hex",
]
