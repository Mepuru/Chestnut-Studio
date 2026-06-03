"""轨道配置模块

集中管理轨道颜色、数量等配置，供 UI 层各组件统一使用。
"""

from __future__ import annotations

import json
from pathlib import Path

# 默认初始显示的轨道数
DEFAULT_TRACK_COUNT = 10

# 最大支持的轨道数
MAX_TRACK_COUNT = 10

# 轨道前景色（十六进制），按轨道号索引
# 轨道号从 1 开始，使用时需 -1 作为索引
TRACK_COLORS_HEX: list[str] = [
    "#3b82f6",  # 轨道1: 蓝色
    "#10b981",  # 轨道2: 绿色
    "#f59e0b",  # 轨道3: 橙色
    "#ec4899",  # 轨道4: 粉色
    "#8b5cf6",  # 轨道5: 紫色
    "#06b6d4",  # 轨道6: 青色
    "#f97316",  # 轨道7: 橙红色
    "#84cc16",  # 轨道8: 黄绿色
    "#ef4444",  # 轨道9: 红色
    "#a855f7",  # 轨道10: 紫罗兰
]

# 用户自定义轨道颜色覆盖（轨道号 → 十六进制）
_user_track_colors: dict[int, str] = {}
_config_path: Path | None = None


def set_config_path(path: str | Path):
    """设置轨道颜色配置文件的保存路径"""
    global _config_path
    _config_path = Path(path)


def get_track_color(track: int) -> str:
    """获取指定轨道的前景色（十六进制）

    优先返回用户自定义颜色，无自定义时使用默认颜色。

    Args:
        track: 轨道号（从 1 开始）

    Returns:
        十六进制颜色字符串，超出范围时循环使用
    """
    if track in _user_track_colors:
        return _user_track_colors[track]
    idx = max(0, track - 1) % len(TRACK_COLORS_HEX)
    return TRACK_COLORS_HEX[idx]


def set_track_color(track: int, hex_color: str):
    """设置用户自定义轨道颜色"""
    if not hex_color.startswith("#"):
        hex_color = "#" + hex_color
    _user_track_colors[track] = hex_color


def reset_track_color(track: int):
    """恢复指定轨道的默认颜色"""
    _user_track_colors.pop(track, None)


def get_all_track_colors() -> dict[int, str]:
    """获取所有轨道的当前颜色（自定义优先，默认兜底）"""
    return {i + 1: get_track_color(i + 1) for i in range(MAX_TRACK_COUNT)}


def get_track_bg_color_hex(track: int, alpha: int = 30) -> str:
    """获取指定轨道的背景色（十六进制，带透明度）

    Args:
        track: 轨道号（从 1 开始）
        alpha: 透明度 (0-255)

    Returns:
        带 Alpha 的十六进制颜色字符串 (AARRGGBB 格式)
    """
    hex_color = get_track_color(track)
    r, g, b = hex_color[1:3], hex_color[3:5], hex_color[5:7]
    return f"#{alpha:02x}{r}{g}{b}"


def save_track_colors(path: str | Path | None = None):
    """将用户自定义轨道颜色保存到 JSON 文件"""
    save_path = Path(path) if path else _config_path
    if not save_path:
        return
    save_path.parent.mkdir(parents=True, exist_ok=True)
    data = {str(k): v for k, v in _user_track_colors.items()}
    save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_track_colors(path: str | Path | None = None):
    """从 JSON 文件加载用户自定义轨道颜色"""
    load_path = Path(path) if path else _config_path
    if not load_path or not load_path.exists():
        return
    try:
        data = json.loads(load_path.read_text(encoding="utf-8"))
        _user_track_colors.clear()
        for k, v in data.items():
            try:
                _user_track_colors[int(k)] = v
            except (ValueError, TypeError):
                pass
    except (json.JSONDecodeError, OSError):
        pass


# 笔记类型列表，从 DEFAULT_TRACK_COUNT 自动生成
NOTE_TYPES: list[str] = [f"轨道{i}" for i in range(1, DEFAULT_TRACK_COUNT + 1)]


def get_effective_track_count(current_max: int) -> int:
    """获取有效的轨道显示数量

    保证至少显示 DEFAULT_TRACK_COUNT 个轨道，不超过 MAX_TRACK_COUNT。

    Args:
        current_max: 当前数据中的最大轨道号

    Returns:
        应显示的轨道数量
    """
    return max(DEFAULT_TRACK_COUNT, min(current_max, MAX_TRACK_COUNT))
