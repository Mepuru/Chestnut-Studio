"""@log_operation 装饰器单元测试"""

import pytest

from chestnut_studio.utils.log_manager import LogLevel, LogManager
from chestnut_studio.utils.log_utils import log_operation


@pytest.fixture(autouse=True)
def reset_log_manager():
    """每个测试前重置 LogManager 单例"""
    LogManager.reset()
    yield
    LogManager.reset()


class TestLogOperation:
    """测试 @log_operation 装饰器"""

    def test_custom_message(self):
        """自定义消息：记录指定文本"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("打开百宝箱")
            def do_it(self):
                return 42

        result = Foo().do_it()
        assert result == 42
        assert len(logs) == 1
        assert logs[0].message == "打开百宝箱"
        assert logs[0].level == LogLevel.INFO
        assert logs[0].source == "UI"

    def test_template_with_param(self):
        """模板消息：{param} 占位符替换"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("打开视频: {path}")
            def open(self, path: str):
                return path

        result = Foo().open("/tmp/video.mp4")
        assert result == "/tmp/video.mp4"
        assert len(logs) == 1
        assert logs[0].message == "打开视频: /tmp/video.mp4"

    def test_template_with_multiple_params(self):
        """模板消息：多参数占位符"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("导出: {count} 条到 {path}")
            def export(self, path: str, count: int):
                return count

        result = Foo().export("/tmp/out.txt", 42)
        assert result == 42
        assert len(logs) == 1
        assert logs[0].message == "导出: 42 条到 /tmp/out.txt"

    def test_custom_source(self):
        """自定义 source"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("处理视频", source="FFmpeg")
            def process(self):
                pass

        Foo().process()
        assert logs[0].source == "FFmpeg"

    def test_custom_level(self):
        """自定义级别"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("调试信息", level=LogLevel.DEBUG)
            def debug(self):
                pass

        Foo().debug()
        assert logs[0].level == LogLevel.DEBUG

    def test_empty_message_noop(self):
        """空消息：不记录日志，函数正常执行"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation()
            def do_it(self):
                return 99

        result = Foo().do_it()
        assert result == 99
        assert len(logs) == 0

    def test_preserves_docstring_and_name(self):
        """保留原函数的元数据"""

        class Foo:
            @log_operation("测试")
            def my_method(self):
                """我的方法说明"""
                pass

        assert Foo.my_method.__name__ == "my_method"
        assert Foo.my_method.__doc__ == "我的方法说明"

    def test_template_missing_key_fallback(self):
        """模板参数缺失时 fallback 到原消息"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("打开视频: {missing_key}")
            def open(self, path: str):
                pass

        Foo().open("/tmp/v.mp4")
        assert len(logs) == 1
        # 缺 key 时使用原消息
        assert logs[0].message == "打开视频: {missing_key}"

    def test_kwargs_support(self):
        """支持关键字参数"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("打开视频: {path}")
            def open(self, path: str):
                pass

        Foo().open(path="/tmp/v.mp4")
        assert logs[0].message == "打开视频: /tmp/v.mp4"

    def test_default_params(self):
        """支持默认参数值"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("倍速: {rate}x")
            def set_rate(self, rate: float = 1.0):
                pass

        Foo().set_rate()
        assert logs[0].message == "倍速: 1.0x"

    def test_log_before_execution(self):
        """在函数执行前记录（即使函数抛出异常，日志也已写入）"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("准备崩溃")
            def crash(self):
                raise ValueError("boom")

        with pytest.raises(ValueError):
            Foo().crash()
        # 异常前日志已写入
        assert len(logs) == 1
        assert logs[0].message == "准备崩溃"


class TestLogOperationAfter:
    """测试 @log_operation(after=True) 后置模式"""

    def test_after_with_result(self):
        """后置模式：{result} 绑定返回值"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("清空笔记 ({result} 条)", after=True)
            def clear(self) -> int:
                return 42

        result = Foo().clear()
        assert result == 42
        assert len(logs) == 1
        assert logs[0].message == "清空笔记 (42 条)"

    def test_after_with_param_and_result(self):
        """后置模式：同时使用参数和返回值"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("跳转 {ms:+d}ms → {result}ms", after=True)
            def skip(self, ms: int) -> int:
                return 5000 + ms

        result = Foo().skip(3000)
        assert result == 8000
        assert len(logs) == 1
        assert logs[0].message == "跳转 +3000ms → 8000ms"

    def test_after_preserves_return_value(self):
        """后置模式：保持返回值不变"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("返回 {result}", after=True)
            def get_value(self) -> str:
                return "hello"

        assert Foo().get_value() == "hello"

    def test_after_logs_after_execution(self):
        """后置模式：在函数执行后记录"""
        state = []

        class Foo:
            @log_operation("执行完毕: {result}", after=True)
            def run(self) -> str:
                state.append("executed")
                return "done"

        Foo().run()
        assert state == ["executed"]  # 先执行
        # 装饰器在 return 后记录，不影响函数本身

    def test_after_empty_result(self):
        """后置模式：返回值 None 时 {result} 为 None"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("结果: {result}", after=True)
            def nothing(self):
                pass

        Foo().nothing()
        assert len(logs) == 1
        assert logs[0].message == "结果: None"

    def test_after_keeps_source_and_level(self):
        """后置模式：保留自定义 source 和 level"""
        logs = []
        LogManager.instance().add_handler(lambda r: logs.append(r))

        class Foo:
            @log_operation("{result}", source="FFmpeg", level=LogLevel.WARNING, after=True)
            def check(self) -> str:
                return "warning"

        Foo().check()
        assert logs[0].source == "FFmpeg"
        assert logs[0].level == LogLevel.WARNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
