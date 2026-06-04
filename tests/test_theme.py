"""主题引擎测试"""

import re

import pytest

from chestnut_studio.utils.theme import (
    THEMES,
    _current_theme_name,
    get_theme,
    render_stylesheet,
    set_theme,
)

_THEME_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class TestGetTheme:
    def test_returns_dict(self):
        theme = get_theme()
        assert isinstance(theme, dict)

    def test_has_required_tokens(self):
        theme = get_theme()
        required = ["bg_base", "accent", "text_primary", "danger"]
        for key in required:
            assert key in theme, f"缺少 token: {key}"

    def test_token_values_are_strings(self):
        theme = get_theme()
        for v in theme.values():
            assert isinstance(v, str)

    def test_total_token_count(self):
        assert len(get_theme()) == 32


class TestSetTheme:
    def test_set_theme_invalid(self):
        with pytest.raises(ValueError):
            set_theme("nonexistent")

    def test_set_theme_valid(self):
        current = _current_theme_name
        set_theme("dark")
        assert _current_theme_name == "dark"
        # 恢复
        set_theme(current)


class TestRenderStylesheet:
    def test_returns_string(self):
        result = render_stylesheet()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_no_unreplaced_tokens(self):
        """所有 {{token}} 占位符都应该被替换"""
        result = render_stylesheet()
        unreplaced = _THEME_PATTERN.findall(result)
        assert unreplaced == [], f"还有未替换的占位符: {unreplaced}"

    def test_contains_qss_rules(self):
        result = render_stylesheet()
        assert "QMainWindow" in result or "QWidget" in result

    def test_specific_theme_name(self):
        result = render_stylesheet("dark")
        assert isinstance(result, str)
        assert len(result) > 0


class TestThemeStructure:
    def test_themes_dict_not_empty(self):
        assert len(THEMES) > 0

    def test_dark_is_default(self):
        assert "dark" in THEMES
        assert _current_theme_name == "dark"

    def test_all_tokens_have_values(self):
        for name, theme in THEMES.items():
            for key, value in theme.items():
                assert value, f"主题 '{name}' 的 token '{key}' 值为空"
