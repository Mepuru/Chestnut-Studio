"""字幕导入/导出"""

from chestnut_studio.core.subtitle import SubtitleEntry
from chestnut_studio.utils.time_utils import ass_time_to_ms, ms_to_ass_time, ms_to_srt_time, srt_time_to_ms


class SubtitleIO:
    """字幕导入/导出"""

    @staticmethod
    def import_srt(path: str) -> dict[int, SubtitleEntry]:
        """导入 SRT 文件

        Returns:
            {start_ms: SubtitleEntry(duration_ms, text), ...}
        """
        result: dict[int, SubtitleEntry] = {}
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
                result[start] = SubtitleEntry(end - start, text)
                i += 3
            else:
                i += 1
        return result

    @staticmethod
    def export_srt(path: str, data: dict[int, SubtitleEntry], video_start: int = 0, sub_start: int = 0):
        """导出 SRT 文件

        Args:
            path: 输出路径
            data: 字幕数据 {start_ms: SubtitleEntry(duration_ms, text)}
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

    @staticmethod
    def import_ass(path: str) -> dict[int, SubtitleEntry]:
        """导入 ASS 文件（读取第一个样式的字幕，兼容旧接口）

        Returns:
            {start_ms: SubtitleEntry(duration_ms, text), ...}
        """
        multi_data = SubtitleIO.import_ass_multi_track(path)
        if not multi_data:
            return {}

        # 合并所有样式到一个字典
        result: dict[int, SubtitleEntry] = {}
        for style_data in multi_data.values():
            result.update(style_data)
        return result

    @staticmethod
    def import_ass_multi_track(path: str) -> dict[str, dict[int, SubtitleEntry]]:
        """导入 ASS 文件（按样式分轨道）

        Returns:
            {style_name: {start_ms: SubtitleEntry(duration_ms, text), ...}}
        """
        result: dict[str, dict[int, SubtitleEntry]] = {}

        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Dialogue:"):
                    parts = line.split(",", 9)
                    if len(parts) >= 10:
                        style = parts[3].strip()
                        start = ass_time_to_ms(parts[1])
                        end = ass_time_to_ms(parts[2])
                        text = parts[9].replace("\\N", "\n").replace("\\n", "\n")
                        # 移除 ASS 标签（保留标签后的文本）
                        while text.startswith("{") and "}" in text:
                            text = text[text.index("}") + 1:]

                        if style not in result:
                            result[style] = {}
                        result[style][start] = SubtitleEntry(end - start, text)

        return result

    @staticmethod
    def export_ass(
        path: str,
        tracks: dict[int, dict[int, SubtitleEntry]],
        track_styles: dict[int, str] = None,
        fontname: str = "Arial",
        fontsize: int = 20,
    ):
        """导出 ASS 文件（多轨道）

        Args:
            path: 输出路径
            tracks: {col: {start_ms: SubtitleEntry(duration_ms, text), ...}}
            track_styles: {col: "样式名"} 默认使用 "轨道 1", "轨道 2" 等
            fontname: 字体名称
            fontsize: 字体大小
        """
        # 默认样式名
        if track_styles is None:
            track_styles = {}
        for col in tracks:
            if col not in track_styles:
                track_styles[col] = f"轨道 {col}"

        # 收集所有用到的样式
        used_styles = set(track_styles.values())

        # 生成样式颜色（不同样式不同颜色）
        style_colors = {
            "轨道 1": "&H00FFFFFF",  # 白色
            "轨道 2": "&H0000FFFF",  # 黄色
            "轨道 3": "&H0000FF00",  # 绿色
            "轨道 4": "&H00FF0000",  # 蓝色
        }

        with open(path, "w", encoding="utf-8-sig") as f:
            # Script Info
            f.write("[Script Info]\n")
            f.write("Title: Chestnut Studio Export\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1920\n")
            f.write("PlayResY: 1080\n")
            f.write("\n")

            # V4+ Styles
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")

            for style_name in sorted(used_styles):
                color = style_colors.get(style_name, "&H00FFFFFF")
                f.write(
                    f"Style: {style_name},{fontname},{fontsize},{color},&H000000FF,&H00000000,&H80000000,"
                    f"0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1\n"
                )
            f.write("\n")

            # Events（按起始时间排序，跨轨道合并）
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            all_entries: list[tuple[int, int, int, str]] = []  # (start_ms, duration, col, text)
            for col, sub_data in tracks.items():
                for start_ms, (duration, text) in sub_data.items():
                    if text.strip():
                        all_entries.append((start_ms, duration, col, text))

            for start_ms, duration, col, text in sorted(all_entries, key=lambda x: x[0]):
                style_name = track_styles.get(col, f"轨道 {col}")
                start_time = ms_to_ass_time(start_ms)
                end_time = ms_to_ass_time(start_ms + duration)
                ass_text = text.replace("\n", "\\N")
                f.write(f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{ass_text}\n")

    @staticmethod
    def export_ass_single(
        path: str,
        data: dict[int, SubtitleEntry],
        style_name: str = "Default",
        fontname: str = "Arial",
        fontsize: int = 20,
    ):
        """导出单轨道 ASS 文件

        Args:
            path: 输出路径
            data: {start_ms: SubtitleEntry(duration_ms, text)}
            style_name: 样式名称
            fontname: 字体名称
            fontsize: 字体大小
        """
        SubtitleIO.export_ass(
            path,
            tracks={1: data},
            track_styles={1: style_name},
            fontname=fontname,
            fontsize=fontsize,
        )
