"""时间格式转换工具测试"""

from chestnut_studio.utils.time_utils import ms_to_time_str


class TestMsToTimeStr:
    """ms_to_time_str 测试 — HH:MM:SS.mm 格式（厘秒精度）"""

    def test_zero(self):
        assert ms_to_time_str(0) == "00:00:00.00"

    def test_basic(self):
        assert ms_to_time_str(15200) == "00:00:15.20"

    def test_large(self):
        assert ms_to_time_str(3723000) == "01:02:03.00"

    def test_exact_second(self):
        assert ms_to_time_str(5000) == "00:00:05.00"

    def test_centisecond_precision(self):
        # 厘秒精度：15207ms → "00:00:15.20"（7ms 被截断）
        assert ms_to_time_str(15207) == "00:00:15.20"
        assert ms_to_time_str(15210) == "00:00:15.21"

    def test_overflow_hour(self):
        # 超过 1 小时 → 小时位正常进位
        assert ms_to_time_str(3661000) == "01:01:01.00"
        assert ms_to_time_str(3600000) == "01:00:00.00"
        assert ms_to_time_str(7200500) == "02:00:00.50"

    def test_multi_hour(self):
        assert ms_to_time_str(37230000) == "10:20:30.00"
