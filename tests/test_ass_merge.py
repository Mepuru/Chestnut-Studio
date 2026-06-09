"""ASS+TXT 字幕合并测试"""

import tempfile
from pathlib import Path

from chestnut_studio.core.ass_merge import (
    _nth_comma,
    _parse_ass_time,
    _parse_track_colors,
    _parse_txt_time,
    build_merge_plan,
    parse_ass,
    parse_txt,
)
from chestnut_studio.core.model.ass_merge import AssDialogue, MergePlan

# ══════════════════════════════════════════
# 底层工具函数
# ══════════════════════════════════════════


class TestNthComma:
    def test_first(self):
        assert _nth_comma("a,b,c", 0) == 1

    def test_second(self):
        assert _nth_comma("a,b,c", 1) == 3

    def test_out_of_range(self):
        assert _nth_comma("a,b", 5) == -1

    def test_no_comma(self):
        assert _nth_comma("abc", 0) == -1


class TestParseAssTime:
    def test_basic(self):
        assert _parse_ass_time("1:02:03.50") == 3723.5

    def test_zero(self):
        assert _parse_ass_time("0:00:00.00") == 0.0

    def test_short_ms(self):
        assert _parse_ass_time("0:00:15.2") == 15.2

    def test_malformed_returns_zero(self):
        assert _parse_ass_time("") == 0.0
        assert _parse_ass_time("invalid") == 0.0
        assert _parse_ass_time("1:2") == 0.0


class TestParseTxtTime:
    def test_mmss(self):
        assert _parse_txt_time("01:30.50") == 90.5

    def test_hmmss(self):
        assert _parse_txt_time("1:02:03.00") == 3723.0

    def test_zero(self):
        assert _parse_txt_time("00:00.00") == 0.0

    def test_malformed_returns_zero(self):
        assert _parse_txt_time("") == 0.0
        assert _parse_txt_time("invalid") == 0.0


class TestParseTrackColors:
    def test_basic(self):
        raw = "# 轨道颜色: 轨道1=#3b82f6, 轨道2=#10b981\n"
        result = _parse_track_colors(raw)
        assert result == {"轨道1": "#3b82f6", "轨道2": "#10b981"}

    def test_no_colors(self):
        raw = "# 某其他内容\n"
        assert _parse_track_colors(raw) == {}

    def test_invalid_color_skipped(self):
        raw = "# 轨道颜色: 轨道1=invalid, 轨道2=#10b981\n"
        result = _parse_track_colors(raw)
        assert "轨道1" not in result
        assert result["轨道2"] == "#10b981"


# ══════════════════════════════════════════
# ASS 解析（文件模式）
# ══════════════════════════════════════════

SAMPLE_ASS = """[Script Info]
Title: Test

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,思源黑体 CN,70,&H00FFFFFF,&H000000FF,&H00000000,&HFF000000,-1,0,0,0,100,100,0,0,1,5,5,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,First line
Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,Second line
Dialogue: 0,0:00:09.00,0:00:12.00,Default,,0,0,0,,Third line
"""

SAMPLE_TXT = """# Chestnut Studio Notes v2.2.3
# 轨道颜色: 轨道1=#3b82f6
# ---
#1\t轨道1\t00:01.50\t| 笔记A
#2\t轨道1\t00:05.50\t| 笔记B
#3\t轨道1\t00:09.50\t| 笔记C
"""


class TestParseAss:
    def test_parse_ass(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_ASS)
            path = f.name
        try:
            dialogues, raw = parse_ass(path)
            assert len(dialogues) == 3
            assert dialogues[0].start_s == 1.0
            assert dialogues[0].end_s == 4.0
            assert dialogues[1].start_s == 5.0
            assert dialogues[2].start_s == 9.0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_ass_dialogue_structure(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_ASS)
            path = f.name
        try:
            dialogues, raw = parse_ass(path)
            d = dialogues[0]
            assert d.start_str == "0:00:01.00"
            assert d.end_str == "0:00:04.00"
            assert d.style == "Default"
            assert d.raw_before_text.startswith("Dialogue:")
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_ass_malformed_line_skipped(self):
        malformed = SAMPLE_ASS + "Dialogue: 0,0:00:13.00,0:00:15.00\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False, encoding="utf-8") as f:
            f.write(malformed)
            path = f.name
        try:
            dialogues, raw = parse_ass(path)
            assert len(dialogues) == 3
        finally:
            Path(path).unlink(missing_ok=True)


class TestParseTxt:
    def test_parse_txt(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_TXT)
            path = f.name
        try:
            notes, colors = parse_txt(path)
            assert len(notes) == 3
            assert notes[0].text == "笔记A"
            assert notes[0].time_s == 1.5
            assert notes[0].track == "轨道1"
            assert notes[0].index == 1
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_txt_colors(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_TXT)
            path = f.name
        try:
            notes, colors = parse_txt(path)
            assert colors == {"轨道1": "#3b82f6"}
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_txt_no_notes(self):
        empty_text = "# 只有注释行\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(empty_text)
            path = f.name
        try:
            notes, colors = parse_txt(path)
            assert len(notes) == 0
        finally:
            Path(path).unlink(missing_ok=True)


# ══════════════════════════════════════════
# MergePlan 功能
# ══════════════════════════════════════════


class TestMergePlanHelpers:
    def test_hex_to_ass_color(self):
        assert MergePlan._hex_to_ass_color("#3b82f6") == "&H00f6823b"

    def test_hex_to_ass_color_short(self):
        assert MergePlan._hex_to_ass_color("invalid") == "&H00FFFFFF"

    def test_hex_to_ass_color_no_hash(self):
        assert MergePlan._hex_to_ass_color("3b82f6") == "&H00f6823b"

    def test_build_style_line(self):
        line = MergePlan._build_style_line("轨道1", "#3b82f6")
        assert line.startswith("Style: 轨道1,思源黑体 CN,70,&H00f6823b")

    def test_collect_used_tracks(self):
        dialogues = [
            AssDialogue(
                line_index=0,
                start_s=0,
                end_s=1,
                start_str="",
                end_str="",
                style="",
                text="",
                raw_before_text="",
                track="轨道1",
            ),
            AssDialogue(
                line_index=1,
                start_s=1,
                end_s=2,
                start_str="",
                end_str="",
                style="",
                text="",
                raw_before_text="",
                track="",
            ),
            AssDialogue(
                line_index=2,
                start_s=2,
                end_s=3,
                start_str="",
                end_str="",
                style="",
                text="",
                raw_before_text="",
                track="轨道2",
            ),
            AssDialogue(
                line_index=3,
                start_s=3,
                end_s=4,
                start_str="",
                end_str="",
                style="",
                text="",
                raw_before_text="",
                track="轨道1",
            ),
        ]
        plan = MergePlan("", "", dialogues, [], 0, 0, [], [], [], {})
        used = plan._collect_used_tracks()
        assert used == ["轨道1", "轨道2"]


# ══════════════════════════════════════════
# 完整合并测试
# ══════════════════════════════════════════


def _make_ass_with_dialogues(dialogues: list[tuple[str, str]]) -> str:
    """生成 ASS 字符串 — 每对 (start, end) 是一条 Dialogue"""
    lines = [
        "[Script Info]",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,思源黑体 CN,70,&H00FFFFFF,&H000000FF,&H00000000,&HFF000000,-1,0,0,0,100,100,0,0,1,5,5,2,10,10,10,1",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for start, end in dialogues:
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,Line")
    return "\n".join(lines)


def _make_txt_with_notes(notes: list[tuple[str, str, str]]) -> str:
    """生成 TXT 字符串 — 每条 (type, time, text)"""
    lines = ["# Chestnut Studio Notes v2.2.3", "# 轨道颜色: 轨道1=#3b82f6", "# ---"]
    for i, (typ, time_str, text) in enumerate(notes, 1):
        lines.append(f"#{i}\t{typ}\t{time_str}\t| {text}")
    return "\n".join(lines)


class TestBuildMergePlan:
    def test_simple_non_overlap(self):
        ass = _make_ass_with_dialogues(
            [
                ("0:00:01.00", "0:00:04.00"),
                ("0:00:05.00", "0:00:08.00"),
            ]
        )
        txt = _make_txt_with_notes(
            [
                ("轨道1", "00:02.00", "笔记A"),
                ("轨道1", "00:06.00", "笔记B"),
            ]
        )
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False, encoding="utf-8") as fa,
            tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as ft,
        ):
            fa.write(ass)
            ft.write(txt)
            ass_path, txt_path = fa.name, ft.name
        try:
            plan = build_merge_plan(ass_path, txt_path)
            assert plan.total_notes == 2
            assert plan.auto_matched == 2
            assert len(plan.uncertain) == 0
            assert len(plan.risky) == 0
            assert plan.dialogues[0].text == "笔记A"
            assert plan.dialogues[1].text == "笔记B"
        finally:
            Path(ass_path).unlink(missing_ok=True)
            Path(txt_path).unlink(missing_ok=True)

    def test_single_txt_in_overlap(self):
        ass = _make_ass_with_dialogues(
            [
                ("0:00:01.00", "0:00:06.00"),
                ("0:00:04.00", "0:00:09.00"),
            ]
        )
        txt = _make_txt_with_notes(
            [
                ("轨道1", "00:04.50", "中间笔记"),
            ]
        )
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False, encoding="utf-8") as fa,
            tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as ft,
        ):
            fa.write(ass)
            ft.write(txt)
            ass_path, txt_path = fa.name, ft.name
        try:
            plan = build_merge_plan(ass_path, txt_path)
            assert plan.auto_matched == 1
            assert len(plan.risky) == 1
            assert len(plan.uncertain) == 0
        finally:
            Path(ass_path).unlink(missing_ok=True)
            Path(txt_path).unlink(missing_ok=True)

    def test_multiple_txt_in_exclusive(self):
        ass = _make_ass_with_dialogues(
            [
                ("0:00:01.00", "0:00:06.00"),
            ]
        )
        txt = _make_txt_with_notes(
            [
                ("轨道1", "00:02.00", "笔记A"),
                ("轨道1", "00:04.00", "笔记B"),
            ]
        )
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False, encoding="utf-8") as fa,
            tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as ft,
        ):
            fa.write(ass)
            ft.write(txt)
            ass_path, txt_path = fa.name, ft.name
        try:
            plan = build_merge_plan(ass_path, txt_path)
            assert plan.auto_matched == 0
            assert len(plan.uncertain) == 1
            assert len(plan.uncertain[0].notes) == 2
        finally:
            Path(ass_path).unlink(missing_ok=True)
            Path(txt_path).unlink(missing_ok=True)

    def test_report_structure(self):
        ass = _make_ass_with_dialogues(
            [
                ("0:00:01.00", "0:00:04.00"),
            ]
        )
        txt = _make_txt_with_notes(
            [
                ("轨道1", "00:02.00", "笔记A"),
            ]
        )
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False, encoding="utf-8") as fa,
            tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as ft,
        ):
            fa.write(ass)
            ft.write(txt)
            ass_path, txt_path = fa.name, ft.name
        try:
            plan = build_merge_plan(ass_path, txt_path)
            report = plan.generate_report()
            assert "第 1 节" in report
            assert "第 2 节" in report
            assert "第 3 节" in report
            assert "Chestnut Studio" in report
        finally:
            Path(ass_path).unlink(missing_ok=True)
            Path(txt_path).unlink(missing_ok=True)

    def test_merge_write_output(self):
        ass = _make_ass_with_dialogues(
            [
                ("0:00:01.00", "0:00:04.00"),
            ]
        )
        txt = _make_txt_with_notes(
            [
                ("轨道1", "00:02.00", "笔记A"),
            ]
        )
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False, encoding="utf-8") as fa,
            tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as ft,
        ):
            fa.write(ass)
            ft.write(txt)
            ass_path, txt_path = fa.name, ft.name
        try:
            plan = build_merge_plan(ass_path, txt_path)
            out_path = ass_path.replace(".ass", "M_test.ass")
            ass_out, report_path = plan.write(out_path)
            try:
                output = Path(ass_out).read_text(encoding="utf-8")
                assert "笔记A" in output
                assert Path(report_path).exists()
            finally:
                Path(ass_out).unlink(missing_ok=True)
                Path(report_path).unlink(missing_ok=True)
        finally:
            Path(ass_path).unlink(missing_ok=True)
            Path(txt_path).unlink(missing_ok=True)
