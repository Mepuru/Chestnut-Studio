"""LogManager 单元测试"""

import pytest

from chestnut_studio.utils.log_manager import (
    Logger,
    LogLevel,
    LogManager,
    LogRecord,
)


@pytest.fixture(autouse=True)
def reset_log_manager():
    """每个测试前重置 LogManager 单例"""
    LogManager.reset()
    yield
    LogManager.reset()


class TestLogLevel:
    """测试日志级别枚举"""

    def test_values(self):
        """测试级别值"""
        assert LogLevel.DEBUG.value == 0
        assert LogLevel.INFO.value == 1
        assert LogLevel.WARNING.value == 2
        assert LogLevel.ERROR.value == 3

    def test_ordering(self):
        """测试级别排序"""
        assert LogLevel.DEBUG.value < LogLevel.INFO.value
        assert LogLevel.INFO.value < LogLevel.WARNING.value
        assert LogLevel.WARNING.value < LogLevel.ERROR.value


class TestLogRecord:
    """测试日志记录数据类"""

    def test_creation(self):
        """测试创建记录"""
        record = LogRecord("FFmpeg", LogLevel.INFO, "test message")
        assert record.source == "FFmpeg"
        assert record.level == LogLevel.INFO
        assert record.message == "test message"

    def test_immutable(self):
        """测试不可变性"""
        record = LogRecord("FFmpeg", LogLevel.INFO, "test")
        with pytest.raises(AttributeError):
            record.source = "changed"


class TestLogger:
    """测试日志器实例"""

    def test_creation(self):
        """测试创建日志器"""
        logger = Logger("Test")
        assert logger.source == "Test"

    def test_debug(self):
        """测试 debug 方法"""
        received = []
        LogManager.instance().add_handler(lambda r: received.append(r))

        logger = Logger("Test")
        logger.debug("debug message")

        assert len(received) == 1
        assert received[0].level == LogLevel.DEBUG
        assert received[0].message == "debug message"

    def test_info(self):
        """测试 info 方法"""
        received = []
        LogManager.instance().add_handler(lambda r: received.append(r))

        logger = Logger("Test")
        logger.info("info message")

        assert len(received) == 1
        assert received[0].level == LogLevel.INFO

    def test_warning(self):
        """测试 warning 方法"""
        received = []
        LogManager.instance().add_handler(lambda r: received.append(r))

        logger = Logger("Test")
        logger.warning("warning message")

        assert len(received) == 1
        assert received[0].level == LogLevel.WARNING

    def test_error(self):
        """测试 error 方法"""
        received = []
        LogManager.instance().add_handler(lambda r: received.append(r))

        logger = Logger("Test")
        logger.error("error message")

        assert len(received) == 1
        assert received[0].level == LogLevel.ERROR


class TestLogManager:
    """测试日志管理器"""

    def test_singleton(self):
        """测试单例模式"""
        m1 = LogManager.instance()
        m2 = LogManager.instance()
        assert m1 is m2

    def test_get_logger(self):
        """测试获取日志器"""
        manager = LogManager.instance()
        logger1 = manager.get_logger("FFmpeg")
        logger2 = manager.get_logger("FFmpeg")
        assert logger1 is logger2

    def test_get_logger_different_sources(self):
        """测试不同源的日志器"""
        manager = LogManager.instance()
        logger1 = manager.get_logger("FFmpeg")
        logger2 = manager.get_logger("波形")
        assert logger1 is not logger2

    def test_add_handler(self):
        """测试添加处理器"""
        received = []
        LogManager.instance().add_handler(lambda r: received.append(r))

        logger = LogManager.instance().get_logger("Test")
        logger.info("test")

        assert len(received) == 1
        assert received[0].message == "test"

    def test_remove_handler(self):
        """测试移除处理器"""
        received = []

        def handler(record):
            received.append(record)

        LogManager.instance().add_handler(handler)
        LogManager.instance().remove_handler(handler)

        logger = LogManager.instance().get_logger("Test")
        logger.info("test")

        assert len(received) == 0

    def test_clear_handlers(self):
        """测试清空处理器"""
        received = []
        LogManager.instance().add_handler(lambda r: received.append(r))
        LogManager.instance().clear_handlers()

        logger = LogManager.instance().get_logger("Test")
        logger.info("test")

        assert len(received) == 0

    def test_multiple_handlers(self):
        """测试多个处理器"""
        received1 = []
        received2 = []

        LogManager.instance().add_handler(lambda r: received1.append(r))
        LogManager.instance().add_handler(lambda r: received2.append(r))

        logger = LogManager.instance().get_logger("Test")
        logger.info("test")

        assert len(received1) == 1
        assert len(received2) == 1

    def test_min_level_filtering(self):
        """测试日志级别过滤"""
        received = []
        LogManager.instance().add_handler(lambda r: received.append(r))
        LogManager.instance().set_min_level(LogLevel.WARNING)

        logger = LogManager.instance().get_logger("Test")
        logger.debug("debug")
        logger.info("info")
        logger.warning("warning")
        logger.error("error")

        assert len(received) == 2
        assert received[0].level == LogLevel.WARNING
        assert received[1].level == LogLevel.ERROR

    def test_get_min_level(self):
        """测试获取最低级别"""
        LogManager.instance().set_min_level(LogLevel.WARNING)
        assert LogManager.instance().get_min_level() == LogLevel.WARNING

    def test_handler_exception_isolation(self):
        """测试处理器异常隔离"""
        call_count = 0

        def bad_handler(record):
            raise ValueError("handler error")

        def good_handler(record):
            nonlocal call_count
            call_count += 1

        LogManager.instance().add_handler(bad_handler)
        LogManager.instance().add_handler(good_handler)

        logger = LogManager.instance().get_logger("Test")
        logger.info("test")

        assert call_count == 1

    def test_emit_directly(self):
        """测试直接发射记录"""
        received = []
        LogManager.instance().add_handler(lambda r: received.append(r))

        record = LogRecord("Test", LogLevel.INFO, "direct emit")
        LogManager.instance().emit(record)

        assert len(received) == 1
        assert received[0].message == "direct emit"


class TestIntegration:
    """集成测试"""

    def test_typical_usage(self):
        """测试典型使用场景"""
        logs = []

        def capture(record):
            logs.append(f"[{record.source}] {record.message}")

        LogManager.instance().add_handler(capture)

        ffmpeg_logger = LogManager.instance().get_logger("FFmpeg")
        waveform_logger = LogManager.instance().get_logger("波形")

        ffmpeg_logger.info("开始处理视频")
        waveform_logger.info("加载波形")
        ffmpeg_logger.error("处理失败")

        assert len(logs) == 3
        assert logs[0] == "[FFmpeg] 开始处理视频"
        assert logs[1] == "[波形] 加载波形"
        assert logs[2] == "[FFmpeg] 处理失败"

    def test_level_filtering_with_multiple_loggers(self):
        """测试多日志器的级别过滤"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))
        LogManager.instance().set_min_level(LogLevel.INFO)

        debug_logger = LogManager.instance().get_logger("Debug")
        info_logger = LogManager.instance().get_logger("Info")

        debug_logger.debug("should be filtered")
        info_logger.info("should pass")
        debug_logger.warning("should also pass")

        assert len(logs) == 2
        assert logs[0].message == "should pass"
        assert logs[1].message == "should also pass"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
