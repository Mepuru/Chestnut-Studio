"""字幕管理器测试"""

from chestnut_studio.core.subtitle import SubtitleManager


class TestSubtitleManager:
    """字幕管理器测试"""

    def test_set_and_get(self):
        mgr = SubtitleManager()
        mgr.set(1, 1000, 2000, "你好")
        assert mgr.get(1, 1000) == [2000, "你好"]

    def test_delete(self):
        mgr = SubtitleManager()
        mgr.set(1, 1000, 2000, "你好")
        mgr.delete(1, 1000)
        assert mgr.get(1, 1000) is None

    def test_merge(self):
        mgr = SubtitleManager()
        mgr.set(1, 1000, 1000, "你")
        mgr.set(1, 2000, 1000, "好")
        mgr.merge(1, 1000, 3000, "你好")
        assert mgr.get(1, 1000) == [2000, "你好"]

    def test_split(self):
        mgr = SubtitleManager()
        mgr.set(1, 1000, 2000, "你好")
        mgr.split(1, 2000)
        assert mgr.get(1, 1000) == [1000, "你好"]
        assert mgr.get(1, 2000) == [1000, "你好"]

    def test_undo_redo(self):
        mgr = SubtitleManager()
        mgr.push_undo()
        mgr.set(1, 1000, 2000, "你好")
        mgr.push_undo()
        mgr.set(1, 3000, 1000, "世界")
        mgr.undo()
        assert mgr.get(1, 3000) is None
        mgr.redo()
        assert mgr.get(1, 3000) == [1000, "世界"]

    def test_clear(self):
        mgr = SubtitleManager()
        mgr.set(1, 1000, 2000, "你好")
        mgr.set(2, 2000, 1000, "世界")
        mgr.clear(1)
        assert mgr.get(1, 1000) is None
        assert mgr.get(2, 2000) == [1000, "世界"]

    def test_clear_all(self):
        mgr = SubtitleManager()
        mgr.set(1, 1000, 2000, "你好")
        mgr.set(2, 2000, 1000, "世界")
        mgr.clear_all()
        assert mgr.get(1, 1000) is None
        assert mgr.get(2, 2000) is None

    def test_copy_track(self):
        mgr = SubtitleManager()
        mgr.set(1, 1000, 2000, "你好")
        mgr.set(1, 3000, 1500, "世界")
        success = mgr.copy_track(1, 2)
        assert success is True
        assert mgr.get(2, 1000) == [2000, "你好"]
        assert mgr.get(2, 3000) == [1500, "世界"]

    def test_copy_track_same_col(self):
        mgr = SubtitleManager()
        mgr.set(1, 1000, 2000, "你好")
        success = mgr.copy_track(1, 1)
        assert success is False

    def test_copy_track_independence(self):
        """测试复制后两个轨道独立修改不影响"""
        mgr = SubtitleManager()
        mgr.set(1, 1000, 2000, "你好")
        mgr.copy_track(1, 2)
        # 修改轨道2的文本
        mgr.set(2, 1000, 2000, "こんにちは")
        # 轨道1不受影响
        assert mgr.get(1, 1000) == [2000, "你好"]
        assert mgr.get(2, 1000) == [2000, "こんにちは"]
