"""时间格式转换工具"""


def ms_to_time_str(ms: int) -> str:
    """毫秒 → MM:SS.mm 格式（2位小数）

    示例: 15200 → "00:15.20", 3723000 → "62:03.00"
    """
    m, r = divmod(ms, 60000)
    s, ms = divmod(r, 1000)
    return f"{m:02d}:{s:02d}.{ms // 10:02d}"
