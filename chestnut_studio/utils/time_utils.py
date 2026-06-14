"""时间格式转换工具"""


def ms_to_time_str(ms: int) -> str:
    """毫秒 → HH:MM:SS.mm 格式（2位小数）

    示例: 15200 → "00:00:15.20", 3723000 → "01:02:03.00"
    """
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms // 10:02d}"
