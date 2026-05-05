"""时间格式转换工具"""


def ms_to_time_str(ms: int) -> str:
    """毫秒 → m:s.ms 格式 (用于行头显示)

    示例: 15200 → "0:15.2"
    """
    m, r = divmod(ms, 60000)
    s, ms = divmod(r, 1000)
    return f"{m}:{s:02d}.{ms // 100}"


def ms_to_srt_time(ms: int) -> str:
    """毫秒 → h:m:s,ms 格式 (SRT)

    示例: 3723000 → "1:02:03,000"
    """
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h}:{m:02d}:{s:02d},{ms:03d}"


def ms_to_ass_time(ms: int) -> str:
    """毫秒 → h:m:s.ms 格式 (ASS)

    示例: 3723000 → "1:02:03.00"
    """
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h}:{m:02d}:{s:02d}.{ms // 10:02d}"


def ms_to_vtt_time(ms: int) -> str:
    """毫秒 → m:s.ms 格式 (VTT)

    示例: 15200 → "0:15.200"
    """
    m, r = divmod(ms, 60000)
    s, ms = divmod(r, 1000)
    return f"{m}:{s:02d}.{ms:03d}"


def ms_to_lrc_time(ms: int) -> str:
    """毫秒 → m:s.xx 格式 (LRC)

    示例: 15200 → "00:15.20"
    """
    m, r = divmod(ms, 60000)
    s, ms = divmod(r, 1000)
    return f"{m:02d}:{s:02d}.{ms // 10:02d}"


def srt_time_to_ms(t: str) -> int:
    """h:m:s,ms 格式 → 毫秒 (SRT)

    示例: "1:02:03,000" → 3723000
    """
    t = t.replace(",", ".").replace("：", ":")
    h, m, s = t.split(":")
    if "." in s:
        s, ms = s.split(".")
        ms = ms[:3]
    else:
        ms = "0"
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def ass_time_to_ms(t: str) -> int:
    """h:m:s.ms 格式 → 毫秒 (ASS)

    示例: "1:02:03.00" → 3723000
    """
    t = t.replace(",", ".").replace("：", ":")
    h, m, s = t.split(":")
    if "." in s:
        s, ms = s.split(".")
        ms = (ms + "00")[:2]
    else:
        ms = "0"
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms) * 10


def split_time(ms: int) -> str:
    """毫秒 → m:s 格式 (用于简单显示)

    示例: 90000 → "01:30"
    """
    s = ms // 1000
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"
