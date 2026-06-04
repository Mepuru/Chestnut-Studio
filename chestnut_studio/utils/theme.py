"""主题管理模块

集中管理所有设计 token（颜色、间距等），支持多主题切换。
QSS 模板中使用 {{token}} 占位符，运行时由 render_stylesheet() 替换。

用法:
    from chestnut_studio.utils.theme import render_stylesheet
    app.setStyleSheet(render_stylesheet())
"""

import re
from pathlib import Path

from chestnut_studio.resources import get_stylesheet_path

# ── 暗色主题（当前默认） ──

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        # 背景层级（浅 → 深）
        "bg_base": "#1a1a2e",
        "bg_dark": "#16162b",
        "bg_card": "#14142a",
        "bg_surface": "#1e1e38",
        "bg_video": "#000000",
        # 边框
        "border_subtle": "#25254a",
        "border_default": "#2e2e50",
        # 强调色
        "accent": "#7c5cfc",
        "accent_hover": "#9b7cff",
        "accent_pressed": "#6a4ad8",
        # 文字层级（亮 → 暗）
        "text_primary": "#e0e0f0",
        "text_secondary": "#c0c0d8",
        "text_muted": "#9090b0",
        "text_tertiary": "#7070a0",
        "text_dim": "#505080",
        "text_very_dim": "#505068",
        "text_on_accent": "#ffffff",
        "text_time": "#8080b0",
        # 危险色
        "danger": "#f05060",
        # 状态色
        "status_checking": "#d4b85c",
        "status_error": "#c06060",
        "status_update": "#4ecdc4",
        # 交互叠加层
        "overlay_hover": "rgba(255, 255, 255, 0.08)",
        "overlay_pressed": "rgba(255, 255, 255, 0.04)",
        "overlay_selected": "rgba(124, 92, 252, 0.1)",
        "overlay_item": "rgba(255, 255, 255, 0.03)",
        "overlay_item_border": "rgba(255, 255, 255, 0.04)",
        # 交互叠加层（强调色系）
        "overlay_accent": "rgba(124, 92, 252, 0.1)",
        "overlay_accent_light": "rgba(124, 92, 252, 0.15)",
        # 滚动条
        "scrollbar_handle": "rgba(255, 255, 255, 0.1)",
        "scrollbar_hover": "rgba(255, 255, 255, 0.2)",
        # 版本标签
        "version_hover": "#6e7ed4",
    },
}

_current_theme_name: str = "dark"

_THEME_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def get_theme() -> dict[str, str]:
    """获取当前主题的所有 token"""
    return THEMES[_current_theme_name]


def set_theme(name: str) -> None:
    """切换主题"""
    global _current_theme_name
    if name not in THEMES:
        raise ValueError(f"未知主题: {name}，可选: {list(THEMES.keys())}")
    _current_theme_name = name


def render_stylesheet(theme_name: str | None = None) -> str:
    """读取 QSS 模板，替换 {{token}} 占位符为当前主题的色值

    Args:
        theme_name: 主题名称，None 表示使用当前主题

    Returns:
        渲染后的完整样式表字符串
    """
    name = theme_name or _current_theme_name
    theme = THEMES[name]
    template = get_stylesheet_path().read_text(encoding="utf-8")

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in theme:
            raise KeyError(f"主题 '{name}' 中缺少 token: {key}")
        return theme[key]

    return _THEME_PATTERN.sub(_replace, template)