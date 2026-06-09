"""应用配置 — 轨道颜色/数量等不可变常量

本模块提供所有层共用的配置常量，不依赖 core/ 下任何其他模块。
"""

# 默认初始显示的轨道数
DEFAULT_TRACK_COUNT = 10

# 最大支持的轨道数
MAX_TRACK_COUNT = 10

# 轨道前景色（十六进制），按轨道号索引
TRACK_COLORS_HEX: tuple[str, ...] = (
    "#3b82f6",  # 轨道1: 蓝色
    "#10b981",  # 轨道2: 绿色
    "#f59e0b",  # 轨道3: 橙色
    "#ec4899",  # 轨道4: 粉色
    "#6366f1",  # 轨道5: 靛蓝
    "#06b6d4",  # 轨道6: 青色
    "#f97316",  # 轨道7: 橙红色
    "#84cc16",  # 轨道8: 黄绿色
    "#ef4444",  # 轨道9: 红色
    "#a855f7",  # 轨道10: 紫罗兰
)


def get_track_color(track: int) -> str:
    """获取指定轨道的前景色（十六进制）

    Args:
        track: 轨道号（从 1 开始）

    Returns:
        十六进制颜色字符串，超出范围时循环使用
    """
    idx = max(0, track - 1) % len(TRACK_COLORS_HEX)
    return TRACK_COLORS_HEX[idx]


def get_track_bg_color_hex(track: int, alpha: int = 30) -> str:
    """获取指定轨道的背景色（十六进制，带透明度）"""
    hex_color = get_track_color(track)
    r, g, b = hex_color[1:3], hex_color[3:5], hex_color[5:7]
    return f"#{alpha:02x}{r}{g}{b}"


# 笔记类型列表，从 DEFAULT_TRACK_COUNT 自动生成
NOTE_TYPES: tuple[str, ...] = tuple(f"轨道{i}" for i in range(1, DEFAULT_TRACK_COUNT + 1))
