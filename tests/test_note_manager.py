"""笔记管理器测试"""

import json
import tempfile
from pathlib import Path

import pytest

from chestnut_studio.core.note_manager import Note, NoteManager, NOTE_TYPES


class TestNote:
    """Note 数据类测试"""

    def test_create_note(self):
        note = Note(timestamp_ms=12345, text="测试笔记", type="字幕")
        assert note.timestamp_ms == 12345
        assert note.text == "测试笔记"
        assert note.type == "字幕"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="笔记类型"):
            Note(timestamp_ms=0, text="", type="无效类型")

    def test_negative_timestamp(self):
        with pytest.raises(ValueError, match="不能为负"):
            Note(timestamp_ms=-1, text="", type="字幕")

    def test_to_dict(self):
        note = Note(timestamp_ms=5000, text="你好", type="画面")
        d = note.to_dict()
        assert d["timestamp_ms"] == 5000
        assert d["text"] == "你好"
        assert d["type"] == "画面"

    def test_from_dict(self):
        d = {"timestamp_ms": 3000, "text": "测试", "type": "字幕"}
        note = Note.from_dict(d)
        assert note.timestamp_ms == 3000
        assert note.text == "测试"
        assert note.type == "字幕"

    def test_from_dict_default_type(self):
        d = {"timestamp_ms": 1000, "text": "默认类型"}
        note = Note.from_dict(d)
        assert note.type == "字幕"


class TestNoteManager:
    """NoteManager 测试"""

    def test_add(self):
        mgr = NoteManager()
        note = mgr.add(5000, "测试", "字幕")
        assert mgr.count() == 1
        assert note.timestamp_ms == 5000

    def test_add_default_type(self):
        mgr = NoteManager()
        mgr.add(1000, "默认")
        assert mgr.get_all()[0].type == "字幕"

    def test_auto_sort(self):
        mgr = NoteManager()
        mgr.add(3000, "B")
        mgr.add(1000, "A")
        mgr.add(2000, "C")
        notes = mgr.get_all()
        assert [n.text for n in notes] == ["A", "C", "B"]

    def test_remove(self):
        mgr = NoteManager()
        note = mgr.add(1000, "测试")
        assert mgr.count() == 1
        mgr.remove(note)
        assert mgr.count() == 0

    def test_remove_nonexistent(self):
        mgr = NoteManager()
        note = Note(1000, "测试")
        assert mgr.remove(note) is False

    def test_clear(self):
        mgr = NoteManager()
        mgr.add(1000, "A")
        mgr.add(2000, "B")
        mgr.clear()
        assert mgr.count() == 0

    def test_get_by_type(self):
        mgr = NoteManager()
        mgr.add(1000, "字幕A", "字幕")
        mgr.add(2000, "画面A", "画面")
        mgr.add(3000, "字幕B", "字幕")

        subs = mgr.get_by_type("字幕")
        assert len(subs) == 2
        assert all(n.type == "字幕" for n in subs)

        screens = mgr.get_by_type("画面")
        assert len(screens) == 1

    def test_export_json(self):
        mgr = NoteManager()
        mgr.add(1000, "测试", "字幕")

        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            path = f.name

        try:
            mgr.export_json(path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "version" in data
            assert "notes" in data
            assert len(data["notes"]) == 1
            assert data["notes"][0]["text"] == "测试"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_import_json(self):
        mgr = NoteManager()
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            json.dump({"version": 1, "notes": [{"timestamp_ms": 5000, "text": "导入的笔记", "type": "画面"}]}, f, ensure_ascii=False)
            path = f.name

        try:
            count = mgr.import_json(path)
            assert count == 1
            assert mgr.count() == 1
            assert mgr.get_all()[0].type == "画面"
        finally:
            Path(path).unlink(missing_ok=True)
