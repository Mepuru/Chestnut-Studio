"""字幕管理器测试"""

from chestnut_studio.core.subtitle import SubtitleManager


class TestSubtitleManager:
    """字幕管理器测试"""

    def test_set_and_get(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 2000, "你好")
        assert mgr.get(0, 1000) == [2000, "你好"]

    def test_delete(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 2000, "你好")
        mgr.delete(0, 1000)
        assert mgr.get(0, 1000) is None

    def test_merge(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 1000, "你")
        mgr.set(0, 2000, 1000, "好")
        mgr.merge(0, 1000, 3000, "你好")
        assert mgr.get(0, 1000) == [2000, "你好"]

    def test_split(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 2000, "你好")
        mgr.split(0, 2000)
        assert mgr.get(0, 1000) == [1000, "你好"]
        assert mgr.get(0, 2000) == [1000, "你好"]

    def test_undo_redo(self):
        mgr = SubtitleManager()
        mgr.push_undo()
        mgr.set(0, 1000, 2000, "你好")
        mgr.push_undo()
        mgr.set(0, 3000, 1000, "世界")
        mgr.undo()
        assert mgr.get(0, 3000) is None
        mgr.redo()
        assert mgr.get(0, 3000) == [1000, "世界"]

    def test_clear(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 2000, "你好")
        mgr.set(1, 2000, 1000, "世界")
        mgr.clear(0)
        assert mgr.get(0, 1000) is None
        assert mgr.get(1, 2000) == [1000, "世界"]

    def test_clear_all(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 2000, "你好")
        mgr.set(1, 2000, 1000, "世界")
        mgr.clear_all()
        assert mgr.get(0, 1000) is None
        assert mgr.get(1, 2000) is None
