"""时间格式转换工具测试"""


from chestnut_studio.utils.time_utils import (
    ass_time_to_ms,
    ms_to_ass_time,
    ms_to_lrc_time,
    ms_to_srt_time,
    ms_to_time_str,
    ms_to_vtt_time,
    split_time,
    srt_time_to_ms,
)


class TestMsToTimeStr:
    """ms_to_time_str 测试 — MM:SS.mm 格式（厘秒精度）"""

    def test_zero(self):
        assert ms_to_time_str(0) == "00:00.00"

    def test_basic(self):
        assert ms_to_time_str(15200) == "00:15.20"

    def test_large(self):
        assert ms_to_time_str(3723000) == "62:03.00"

    def test_exact_second(self):
        assert ms_to_time_str(5000) == "00:05.00"

    def test_centisecond_precision(self):
        # 厘秒精度：15207ms → "00:15.20"（7ms 被截断）
        assert ms_to_time_str(15207) == "00:15.20"
        assert ms_to_time_str(15210) == "00:15.21"

    def test_overflow_hour(self):
        # 超过 1 小时
        assert ms_to_time_str(3661000) == "61:01.00"
        assert ms_to_time_str(3600000) == "60:00.00"


class TestMsToSrtTime:
    """ms_to_srt_time 测试 — h:m:s,ms 格式（毫秒精度）"""

    def test_zero(self):
        assert ms_to_srt_time(0) == "0:00:00,000"

    def test_basic(self):
        assert ms_to_srt_time(3723000) == "1:02:03,000"

    def test_full_ms_precision(self):
        assert ms_to_srt_time(15207) == "0:00:15,207"

    def test_exact_hour(self):
        assert ms_to_srt_time(3600000) == "1:00:00,000"

    def test_single_digit_hour(self):
        assert ms_to_srt_time(7200500) == "2:00:00,500"


class TestMsToAssTime:
    """ms_to_ass_time 测试 — h:m:s.ms 格式（厘秒精度）"""

    def test_zero(self):
        assert ms_to_ass_time(0) == "0:00:00.00"

    def test_basic(self):
        assert ms_to_ass_time(3723000) == "1:02:03.00"

    def test_roundtrip_example(self):
        assert ms_to_ass_time(15200) == "0:00:15.20"


class TestMsToVttTime:
    """ms_to_vtt_time 测试 — m:s.ms 格式（毫秒精度）"""

    def test_zero(self):
        assert ms_to_vtt_time(0) == "0:00.000"

    def test_basic(self):
        assert ms_to_vtt_time(15200) == "0:15.200"

    def test_full_ms(self):
        assert ms_to_vtt_time(15207) == "0:15.207"

    def test_large(self):
        assert ms_to_vtt_time(3723000) == "62:03.000"


class TestMsToLrcTime:
    """ms_to_lrc_time 测试 — m:s.xx 格式（厘秒精度）"""

    def test_zero(self):
        assert ms_to_lrc_time(0) == "00:00.00"

    def test_basic(self):
        assert ms_to_lrc_time(15200) == "00:15.20"

    def test_large(self):
        assert ms_to_lrc_time(3723000) == "62:03.00"


class TestSrtTimeToMs:
    """srt_time_to_ms 测试"""

    def test_basic(self):
        assert srt_time_to_ms("1:02:03,000") == 3723000

    def test_with_ms(self):
        assert srt_time_to_ms("0:00:15,207") == 15207

    def test_zero(self):
        assert srt_time_to_ms("0:00:00,000") == 0

    def test_chinese_colon(self):
        """兼容全角冒号"""
        assert srt_time_to_ms("1：02：03,000") == 3723000

    def test_comma_variant(self):
        """兼容逗号句号混用"""
        assert srt_time_to_ms("1:02:03.000") == 3723000

    def test_truncated_ms(self):
        """毫秒不足3位时补零，.2 视为 2ms 而非 200ms"""
        assert srt_time_to_ms("0:00:15,2") == 15002

    def test_large_hour(self):
        assert srt_time_to_ms("2:30:00,000") == 9000000


class TestAssTimeToMs:
    """ass_time_to_ms 测试"""

    def test_basic(self):
        assert ass_time_to_ms("1:02:03.00") == 3723000

    def test_zero(self):
        assert ass_time_to_ms("0:00:00.00") == 0

    def test_chinese_colon(self):
        """兼容全角冒号"""
        assert ass_time_to_ms("1：02：03.00") == 3723000

    def test_comma_variant(self):
        """兼容逗号句号混用"""
        assert ass_time_to_ms("1:02:03,00") == 3723000

    def test_single_digit_cs(self):
        """厘秒不足2位时补零"""
        # .0 在 ass_time_to_ms 中会被补成 .00
        assert ass_time_to_ms("0:00:15.0") == 15000

    def test_three_digit_cs(self):
        """厘秒超过2位时截断"""
        assert ass_time_to_ms("0:00:15.123") == 15120  # 12厘秒

    def test_large_hour(self):
        assert ass_time_to_ms("2:30:00.00") == 9000000


class TestSplitTime:
    """split_time 测试"""

    def test_zero(self):
        assert split_time(0) == "00:00"

    def test_basic(self):
        assert split_time(90000) == "01:30"

    def test_exact_minute(self):
        assert split_time(60000) == "01:00"

    def test_hour_overflow(self):
        """超过1小时：只显示分:秒"""
        assert split_time(3661000) == "61:01"

    def test_round_down_seconds(self):
        """毫秒部分向下取整"""
        assert split_time(91500) == "01:31"  # 91.5秒


class TestRoundtrip:
    """格式转换往返测试"""

    def test_srt_roundtrip(self):
        """SRT 格式往返无损（全毫秒精度）"""
        original = 15207
        converted = srt_time_to_ms(ms_to_srt_time(original))
        assert converted == original

    def test_srt_roundtrip_zero(self):
        assert srt_time_to_ms(ms_to_srt_time(0)) == 0

    def test_srt_roundtrip_large(self):
        original = 3723456
        assert srt_time_to_ms(ms_to_srt_time(original)) == original

    def test_ass_roundtrip_centisecond(self):
        """ASS 格式往返（厘秒精度，10ms 倍数的值无损）"""
        for ms in [0, 15000, 15200, 3723000, 60000]:
            assert ass_time_to_ms(ms_to_ass_time(ms)) == ms

    def test_split_roundtrip_second(self):
        """split_time 只取秒，整秒值往返"""
        for s in [0, 30, 60, 90, 3600]:
            assert split_time(s * 1000) == f"{s // 60:02d}:{s % 60:02d}"
