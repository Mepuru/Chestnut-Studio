"""字幕导入/导出"""


def ms_to_srt_time(ms: int) -> str:
    """毫秒 → SRT 时间格式 (h:m:s,ms)"""
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h}:{m:02d}:{s:02d},{ms:03d}"


def srt_time_to_ms(t: str) -> int:
    """SRT 时间格式 → 毫秒"""
    t = t.replace(",", ".").replace("：", ":")
    h, m, s = t.split(":")
    if "." in s:
        s, ms = s.split(".")
        ms = ms[:3]
    else:
        ms = "0"
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


class SubtitleIO:
    """字幕导入/导出"""

    @staticmethod
    def import_srt(path: str) -> dict[int, list]:
        """导入 SRT 文件

        Returns:
            {start_ms: [duration_ms, "text"], ...}
        """
        result = {}
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if "-->" in line:
                start_str, end_str = line.split("-->")
                start = srt_time_to_ms(start_str.strip())
                end = srt_time_to_ms(end_str.strip())
                text = lines[i + 1].strip() if i + 1 < len(lines) else ""
                result[start] = [end - start, text]
                i += 3
            else:
                i += 1
        return result

    @staticmethod
    def export_srt(path: str, data: dict[int, list], video_start: int = 0, sub_start: int = 0):
        """导出 SRT 文件

        Args:
            path: 输出路径
            data: 字幕数据
            video_start: 视频起始时间 (ms)
            sub_start: 字幕起始偏移 (ms)
        """
        sorted_keys = sorted(data.keys())
        with open(path, "w", encoding="utf-8") as f:
            for num, start in enumerate(sorted_keys, 1):
                delta, text = data[start]
                if text:
                    srt_start = ms_to_srt_time(start - video_start + sub_start)
                    srt_end = ms_to_srt_time(start - video_start + sub_start + delta)
                    f.write(f"{num}\n{srt_start} --> {srt_end}\n{text}\n\n")
