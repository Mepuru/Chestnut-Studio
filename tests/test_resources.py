"""资源管理测试"""

from pathlib import Path

from chestnut_studio.resources import get_icon_path, get_resource_path, get_stylesheet_path


class TestGetResourcePath:
    def test_relative_path(self):
        p = get_resource_path("icon.png")
        assert isinstance(p, Path)
        assert p.name == "icon.png"
        assert p.suffix == ".png"

    def test_subdir_path(self):
        p = get_resource_path("icons/play.svg")
        assert p.name == "play.svg"
        assert "icons" in p.parts

    def test_exists(self):
        p = get_resource_path("icon.png")
        assert p.exists()

    def test_parent_is_resources(self):
        p = get_resource_path("icon.png")
        assert p.parent.name == "resources"


class TestGetIconPath:
    def test_default_icon(self):
        p = get_icon_path()
        assert p.name == "icon.png"
        assert p.exists()

    def test_named_icon(self):
        p = get_icon_path("play")
        assert p.name == "play.svg"
        assert p.exists()

    def test_named_icon_nonexistent(self):
        p = get_icon_path("nonexistent")
        assert p.name == "nonexistent.svg"
        assert not p.exists()


class TestGetStylesheetPath:
    def test_path_format(self):
        p = get_stylesheet_path()
        assert p.name == "style.qss"
        assert p.exists()

    def test_readable(self):
        p = get_stylesheet_path()
        content = p.read_text(encoding="utf-8")
        assert len(content) > 0
        assert "Chestnut" in content or "QMainWindow" in content or "{{" in content
