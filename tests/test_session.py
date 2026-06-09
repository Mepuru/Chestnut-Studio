"""项目文件 / SessionState 测试"""

import json
import tempfile
from pathlib import Path

from chestnut_studio.core.io.session_repository import read_project, write_project
from chestnut_studio.core.model.session import SessionState


class TestSessionState:
    """SessionState 数据类序列化测试"""

    def test_default_values(self):
        state = SessionState()
        assert state.version == "1"
        assert state.notes == []
        assert state.terms == []
        assert state.video_path == ""
        assert state.video_position == 0
        assert state.volume == 80
        assert state.playback_rate == 1.0
        assert state.sort_mode == "time"
        assert state.current_track == 0

    def test_to_dict(self):
        state = SessionState(
            notes=[{"timestamp_ms": 1000, "text": "你好", "type": "轨道1"}],
            video_path="C:/video.mp4",
            video_position=5000,
            volume=60,
        )
        d = state.to_dict()
        assert d["version"] == "1"
        assert d["notes"] == [{"timestamp_ms": 1000, "text": "你好", "type": "轨道1"}]
        assert d["video_path"] == "C:/video.mp4"
        assert d["video_position"] == 5000
        assert d["volume"] == 60

    def test_from_dict(self):
        data = {
            "version": "1",
            "notes": [{"timestamp_ms": 2000, "text": "测试", "type": "轨道2"}],
            "terms": [{"source": "ありがとう", "translation": "谢谢"}],
            "video_path": "D:/movie.mp4",
            "video_position": 12345,
            "volume": 50,
            "sort_mode": "track",
            "current_track": 2,
        }
        state = SessionState.from_dict(data)
        assert state.notes == [{"timestamp_ms": 2000, "text": "测试", "type": "轨道2"}]
        assert state.terms == [{"source": "ありがとう", "translation": "谢谢"}]
        assert state.video_path == "D:/movie.mp4"
        assert state.video_position == 12345
        assert state.volume == 50
        assert state.sort_mode == "track"
        assert state.current_track == 2

    def test_from_dict_partial(self):
        """缺失字段应使用默认值"""
        state = SessionState.from_dict({})
        assert state.notes == []
        assert state.terms == []
        assert state.video_path == ""
        assert state.volume == 80

    def test_from_dict_none_values(self):
        """notes/terms 为 None 时应变为 []"""
        state = SessionState.from_dict({"notes": None, "terms": None})
        assert state.notes == []
        assert state.terms == []

    def test_roundtrip_json(self):
        """to_dict → JSON → from_dict 无损往返"""
        original = SessionState(
            notes=[{"timestamp_ms": 1000, "text": "a", "type": "轨道1"}],
            terms=[{"source": "test", "translation": "测试"}],
            video_path="/path/video.mp4",
            video_position=9999,
            volume=75,
            playback_rate=1.5,
            sort_mode="track",
            current_track=3,
        )
        json_str = json.dumps(original.to_dict(), ensure_ascii=False)
        restored = SessionState.from_dict(json.loads(json_str))
        assert restored == original


class TestProjectRepository:
    """项目文件 I/O 测试"""

    def test_write_read_project(self):
        state = SessionState(
            notes=[{"timestamp_ms": 5000, "text": "项目文件测试", "type": "轨道3"}],
        )
        with tempfile.NamedTemporaryFile(suffix=".chestnut", mode="w", delete=False, encoding="utf-8") as f:
            project_path = f.name
        try:
            write_project(state, project_path)
            restored = read_project(project_path)
            assert restored is not None
            assert restored.notes == state.notes
        finally:
            Path(project_path).unlink(missing_ok=True)

    def test_read_project_nonexistent(self):
        state = read_project("/nonexistent/project.chestnut")
        assert state is None

    def test_read_project_corrupted(self):
        with tempfile.NamedTemporaryFile(suffix=".chestnut", mode="w", delete=False, encoding="utf-8") as f:
            f.write("{{{invalid")
            path = f.name
        try:
            state = read_project(path)
            assert state is None
        finally:
            Path(path).unlink(missing_ok=True)


class TestNoteManagerSerialization:
    """NoteManager to_dict / from_dict 测试"""

    def test_to_dict_empty(self):
        from chestnut_studio.core.manager.note_manager import NoteManager

        mgr = NoteManager()
        d = mgr.to_dict()
        assert d["notes"] == []
        assert d["terms"] == []

    def test_to_dict_with_notes(self):
        mgr = _make_manager()
        d = mgr.to_dict()
        assert len(d["notes"]) == 2
        assert d["notes"][0]["text"] == "你好"
        assert d["notes"][0]["type"] == "轨道1"
        assert d["notes"][1]["text"] == "再见"

    def test_to_dict_with_terms(self):
        mgr = _make_manager(with_terms=True)
        d = mgr.to_dict()
        assert len(d["terms"]) == 1
        assert d["terms"][0]["source"] == "ありがとう"
        assert d["terms"][0]["translation"] == "谢谢"

    def test_from_dict(self):
        from chestnut_studio.core.manager.note_manager import NoteManager

        data = {
            "notes": [
                {"timestamp_ms": 1000, "text": "A", "type": "轨道1"},
                {"timestamp_ms": 2000, "text": "B", "type": "轨道2"},
            ],
            "terms": [
                {"source": "test", "translation": "测试"},
            ],
        }
        mgr = NoteManager()
        mgr.from_dict(data)
        assert mgr.count() == 2
        assert mgr.term_count() == 1
        assert mgr.get_all()[0].text == "A"
        assert mgr.get_terms()[0].source == "test"

    def test_from_dict_clears_existing(self):
        mgr = _make_manager(with_terms=True)
        mgr.from_dict({"notes": [], "terms": []})
        assert mgr.count() == 0
        assert mgr.term_count() == 0

    def test_from_dict_empty_input(self):
        mgr = _make_manager()
        mgr.from_dict({})
        assert mgr.count() == 0

    def test_roundtrip(self):
        """to_dict → from_dict 应完整恢复数据"""
        original = _make_manager(with_terms=True)
        data = original.to_dict()
        restored = _make_manager()
        restored.from_dict(data)
        assert restored.count() == original.count()
        assert restored.term_count() == original.term_count()
        for o, r in zip(original.get_all(), restored.get_all()):
            assert o.timestamp_ms == r.timestamp_ms
            assert o.text == r.text
            assert o.type == r.type
        for o, r in zip(original.get_terms(), restored.get_terms()):
            assert o.source == r.source
            assert o.translation == r.translation
            assert o.origin == r.origin
            assert o.note == r.note

    def test_session_note_manager_integration(self):
        """SessionState + NoteManager 全链路测试"""
        from chestnut_studio.core.manager.note_manager import NoteManager

        mgr = _make_manager(with_terms=True)
        mgr_dict = mgr.to_dict()

        state = SessionState(
            notes=mgr_dict["notes"],
            terms=mgr_dict["terms"],
            video_path="/path/video.mp4",
            video_position=5000,
        )

        json_str = json.dumps(state.to_dict(), ensure_ascii=False)
        restored_state = SessionState.from_dict(json.loads(json_str))

        restored_mgr = NoteManager()
        restored_mgr.from_dict({"notes": restored_state.notes, "terms": restored_state.terms})
        assert restored_mgr.count() == 2
        assert restored_mgr.term_count() == 1
        assert restored_mgr.get_all()[0].text == "你好"


def _make_manager(with_terms: bool = False):
    """创建包含测试数据的 NoteManager"""
    from chestnut_studio.core.manager.note_manager import NoteManager

    mgr = NoteManager()
    mgr.add(1000, "你好", "轨道1")
    mgr.add(3000, "再见", "轨道2")
    if with_terms:
        mgr.add_term("ありがとう", "谢谢", "日常")
    return mgr
