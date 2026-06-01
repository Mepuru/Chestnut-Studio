"""笔记管理器测试"""

import json
import tempfile
from pathlib import Path

import pytest

from chestnut_studio.core.note_manager import Note, NoteManager, NOTE_TYPES


class TestNote:
    """Note 数据类测试"""

    def test_create_note(self):
        note = Note(timestamp_ms=12345, text="测试笔记", type="轨道1")
        assert note.timestamp_ms == 12345
        assert note.text == "测试笔记"
        assert note.type == "轨道1"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="笔记类型"):
            Note(timestamp_ms=0, text="", type="无效类型")

    def test_negative_timestamp(self):
        with pytest.raises(ValueError, match="不能为负"):
            Note(timestamp_ms=-1, text="", type="轨道1")

    def test_to_dict(self):
        note = Note(timestamp_ms=5000, text="你好", type="轨道3")
        d = note.to_dict()
        assert d["timestamp_ms"] == 5000
        assert d["text"] == "你好"
        assert d["type"] == "轨道3"

    def test_from_dict(self):
        d = {"timestamp_ms": 3000, "text": "测试", "type": "轨道2"}
        note = Note.from_dict(d)
        assert note.timestamp_ms == 3000
        assert note.text == "测试"
        assert note.type == "轨道2"

    def test_from_dict_default_type(self):
        d = {"timestamp_ms": 1000, "text": "默认类型"}
        note = Note.from_dict(d)
        assert note.type == "轨道1"

    def test_to_line(self):
        note = Note(timestamp_ms=15200, text="你好", type="轨道1")
        line = note.to_line()
        assert "轨道1" in line
        assert "00:15.20" in line
        assert "你好" in line

    def test_from_line_valid(self):
        note = Note.from_line("轨道1\t00:15.20\t| 你好")
        assert note is not None
        assert note.timestamp_ms == 15200
        assert note.text == "你好"
        assert note.type == "轨道1"

    def test_from_line_invalid(self):
        assert Note.from_line("") is None
        assert Note.from_line("# 注释行") is None
        assert Note.from_line("随便写的东西") is None

    def test_roundtrip(self):
        # 厘秒精度（10ms）无损
        note = Note(timestamp_ms=123450, text="测试内容", type="轨道3")
        line = note.to_line()
        restored = Note.from_line(line)
        assert restored == note


class TestNoteManager:
    """NoteManager 测试"""

    def test_add(self):
        mgr = NoteManager()
        note = mgr.add(5000, "测试", "轨道2")
        assert mgr.count() == 1
        assert note.timestamp_ms == 5000

    def test_add_default_type(self):
        mgr = NoteManager()
        mgr.add(1000, "默认")
        assert mgr.get_all()[0].type == "轨道1"

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
        mgr.add(1000, "轨道1注释", "轨道1")
        mgr.add(2000, "轨道3注释", "轨道3")
        mgr.add(3000, "轨道1另一条", "轨道1")

        t1 = mgr.get_by_type("轨道1")
        assert len(t1) == 2
        assert all(n.type == "轨道1" for n in t1)

        t3 = mgr.get_by_type("轨道3")
        assert len(t3) == 1

    def test_get_used_types(self):
        mgr = NoteManager()
        assert mgr.get_used_types() == []
        mgr.add(1000, "a", "轨道2")
        mgr.add(2000, "b", "轨道4")
        used = mgr.get_used_types()
        assert "轨道2" in used
        assert "轨道4" in used
        assert "轨道1" not in used

    def test_export_text(self):
        mgr = NoteManager()
        mgr.add(15200, "你好", "轨道1")
        mgr.add(30000, "再见", "轨道2")

        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False, encoding="utf-8") as f:
            path = f.name

        try:
            count = mgr.export_text(path)
            assert count == 2
            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert "# Chestnut Studio Notes" in content
            assert "00:15.20" in content
            assert "你好" in content
        finally:
            Path(path).unlink(missing_ok=True)

    def test_export_text_filtered(self):
        mgr = NoteManager()
        mgr.add(1000, "轨道1的", "轨道1")
        mgr.add(2000, "轨道2的", "轨道2")

        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False, encoding="utf-8") as f:
            path = f.name

        try:
            count = mgr.export_text(path, ["轨道1"])
            assert count == 1
            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert "轨道1的" in content
            assert "轨道2的" not in content
        finally:
            Path(path).unlink(missing_ok=True)

    def test_import_text(self):
        mgr = NoteManager()
        content = "轨道1\t00:15.20\t| 你好\n轨道2\t01:00.00\t| 再见\n"
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            count = mgr.import_text(path)
            assert count == 2
            assert mgr.count() == 2
            assert mgr.get_all()[0].text == "你好"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_export_json(self):
        mgr = NoteManager()
        mgr.add(1000, "测试", "轨道2")

        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            path = f.name

        try:
            count = mgr.export_json(path)
            assert count == 1
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["notes"][0]["text"] == "测试"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_export_json_filtered(self):
        mgr = NoteManager()
        mgr.add(1000, "轨道1的", "轨道1")
        mgr.add(2000, "轨道2的", "轨道2")

        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            path = f.name

        try:
            count = mgr.export_json(path, ["轨道1"])
            assert count == 1
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert len(data["notes"]) == 1
            assert data["notes"][0]["text"] == "轨道1的"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_import_json(self):
        mgr = NoteManager()
        data = {"version": 1, "notes": [{"timestamp_ms": 5000, "text": "导入的笔记", "type": "轨道4"}]}
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            path = f.name

        try:
            count = mgr.import_json(path)
            assert count == 1
            assert mgr.get_all()[0].type == "轨道4"
        finally:
            Path(path).unlink(missing_ok=True)
