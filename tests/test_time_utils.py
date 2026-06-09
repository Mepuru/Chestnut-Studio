"""时间格式转换工具测试"""

from chestnut_studio.utils.time_utils import ms_to_time_str


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
