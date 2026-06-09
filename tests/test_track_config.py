"""轨道配置测试"""

from chestnut_studio.core.model.config import (
    MAX_TRACK_COUNT,
    NOTE_TYPES,
    TRACK_COLORS_HEX,
    get_track_bg_color_hex,
    get_track_color,
)


class TestConstants:
    def test_track_count(self):
        assert len(TRACK_COLORS_HEX) == 10
        assert MAX_TRACK_COUNT == 10

    def test_note_types_length(self):
        assert len(NOTE_TYPES) == 10

    def test_note_types_naming(self):
        assert NOTE_TYPES == tuple(f"轨道{i}" for i in range(1, 11))

    def test_colors_are_hex(self):
        for c in TRACK_COLORS_HEX:
            assert c.startswith("#")
            assert len(c) == 7


class TestGetTrackColor:
    def test_track_1(self):
        assert get_track_color(1) == "#3b82f6"

    def test_track_10(self):
        assert get_track_color(10) == "#a855f7"

    def test_wraps_around(self):
        """超出 10 的轨道号循环"""
        assert get_track_color(11) == get_track_color(1)
        assert get_track_color(20) == get_track_color(10)

    def test_track_0_safe(self):
        """轨道号 0 安全返回轨道 1 的颜色"""
        assert get_track_color(0) == "#3b82f6"

    def test_negative_safe(self):
        """负数也安全"""
        assert get_track_color(-1) == "#3b82f6"


class TestGetTrackBgColorHex:
    def test_default_alpha(self):
        bg = get_track_bg_color_hex(1)
        assert bg == "#1e3b82f6"

    def test_custom_alpha(self):
        bg = get_track_bg_color_hex(1, alpha=50)
        assert bg == "#323b82f6"

    def test_alpha_max(self):
        bg = get_track_bg_color_hex(1, alpha=255)
        assert bg == "#ff3b82f6"

    def test_zero_alpha(self):
        bg = get_track_bg_color_hex(1, alpha=0)
        assert bg == "#003b82f6"

    def test_track_10_with_alpha(self):
        bg = get_track_bg_color_hex(10)
        assert bg == "#1ea855f7"
