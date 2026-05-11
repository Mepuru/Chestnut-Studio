"""日志装饰器单元测试"""

import pytest

from chestnut_studio.utils.log_decorator import log_call, log_source
from chestnut_studio.utils.log_manager import LogLevel, LogManager


@pytest.fixture(autouse=True)
def reset_log_manager():
    """每个测试前重置 LogManager 单例"""
    LogManager.reset()
    yield
    LogManager.reset()


class TestLogSource:
    """测试 @log_source 装饰器"""

    def test_sets_log_source(self):
        """测试设置日志源属性"""

        @log_source("FFmpeg")
        class FFmpeg:
            pass

        assert FFmpeg._log_source == "FFmpeg"

    def test_preserves_class(self):
        """测试保留类的其他属性"""

        @log_source("FFmpeg")
        class FFmpeg:
            value = 42

            def method(self):
                return "test"

        assert FFmpeg.value == 42
        assert FFmpeg().method() == "test"

    def test_different_sources(self):
        """测试不同类可以有不同的日志源"""

        @log_source("FFmpeg")
        class FFmpeg:
            pass

        @log_source("波形")
        class Waveform:
            pass

        assert FFmpeg._log_source == "FFmpeg"
        assert Waveform._log_source == "波形"


class TestLogCall:
    """测试 @log_call 装饰器"""

    def test_logs_start_and_success(self):
        """测试记录开始和成功日志"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.INFO)
            def my_method(self):
                return "result"

        obj = MyClass()
        result = obj.my_method()

        assert result == "result"
        assert len(logs) == 2
        assert logs[0].message == "my_method 开始"
        assert logs[0].level == LogLevel.INFO
        assert logs[1].message == "my_method 成功"
        assert logs[1].level == LogLevel.INFO

    def test_logs_with_custom_message(self):
        """测试自定义日志消息"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.INFO, message="获取视频信息")
            def my_method(self):
                return "result"

        obj = MyClass()
        obj.my_method()

        assert len(logs) == 2
        assert logs[0].message == "获取视频信息 开始"
        assert logs[1].message == "获取视频信息 成功"

    def test_logs_error_on_exception(self):
        """测试异常时记录错误日志"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.INFO)
            def my_method(self):
                raise ValueError("test error")

        obj = MyClass()
        with pytest.raises(ValueError, match="test error"):
            obj.my_method()

        assert len(logs) == 2
        assert logs[0].message == "my_method 开始"
        assert logs[0].level == LogLevel.INFO
        assert logs[1].message == "my_method 失败: test error"
        assert logs[1].level == LogLevel.ERROR

    def test_uses_log_source(self):
        """测试使用 @log_source 定义的日志源"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        @log_source("FFmpeg")
        class FFmpeg:
            @log_call(LogLevel.INFO)
            def get_video_info(self):
                pass

        obj = FFmpeg()
        obj.get_video_info()

        assert len(logs) == 2
        assert all(r.source == "FFmpeg" for r in logs)

    def test_unknown_source_without_decorator(self):
        """测试未使用 @log_source 时使用 Unknown"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class NoSource:
            @log_call(LogLevel.INFO)
            def my_method(self):
                pass

        obj = NoSource()
        obj.my_method()

        assert len(logs) == 2
        assert all(r.source == "Unknown" for r in logs)

    def test_preserves_return_value(self):
        """测试保留返回值"""

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.INFO)
            def my_method(self):
                return 42

        obj = MyClass()
        assert obj.my_method() == 42

    def test_preserves_arguments(self):
        """测试保留参数"""

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.INFO)
            def my_method(self, a, b, c=None):
                return (a, b, c)

        obj = MyClass()
        assert obj.my_method(1, 2, c=3) == (1, 2, 3)

    def test_preserves_function_metadata(self):
        """测试保留函数元信息"""

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.INFO)
            def my_method(self):
                """My docstring"""
                pass

        assert MyClass.my_method.__name__ == "my_method"
        assert MyClass.my_method.__doc__ == "My docstring"

    def test_respects_log_level(self):
        """测试日志级别"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))
        LogManager.instance().set_min_level(LogLevel.WARNING)

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.INFO)
            def my_method(self):
                pass

        obj = MyClass()
        obj.my_method()

        # INFO 级别被过滤，应该没有日志
        assert len(logs) == 0

    def test_debug_level(self):
        """测试 DEBUG 级别"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.DEBUG)
            def my_method(self):
                pass

        obj = MyClass()
        obj.my_method()

        assert len(logs) == 2
        assert all(r.level == LogLevel.DEBUG for r in logs)

    def test_warning_level(self):
        """测试 WARNING 级别"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        @log_source("Test")
        class MyClass:
            @log_call(LogLevel.WARNING)
            def my_method(self):
                pass

        obj = MyClass()
        obj.my_method()

        assert len(logs) == 2
        assert all(r.level == LogLevel.WARNING for r in logs)


class TestIntegration:
    """集成测试"""

    def test_multiple_methods(self):
        """测试多个方法"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        @log_source("FFmpeg")
        class FFmpeg:
            @log_call(LogLevel.INFO)
            def get_video_info(self):
                pass

            @log_call(LogLevel.INFO, message="提取音频")
            def extract_audio(self):
                pass

        obj = FFmpeg()
        obj.get_video_info()
        obj.extract_audio()

        assert len(logs) == 4
        assert logs[0].message == "get_video_info 开始"
        assert logs[1].message == "get_video_info 成功"
        assert logs[2].message == "提取音频 开始"
        assert logs[3].message == "提取音频 成功"

    def test_mixed_manual_and_auto_logging(self):
        """测试混合使用手动和自动日志"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        @log_source("FFmpeg")
        class FFmpeg:
            @log_call(LogLevel.INFO)
            def auto_logged(self):
                pass

            def manual_logged(self):
                logger = LogManager.instance().get_logger("FFmpeg")
                logger.debug("手动日志")

        obj = FFmpeg()
        obj.auto_logged()
        obj.manual_logged()

        assert len(logs) == 3
        assert logs[0].message == "auto_logged 开始"
        assert logs[1].message == "auto_logged 成功"
        assert logs[2].message == "手动日志"
        assert logs[2].level == LogLevel.DEBUG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
