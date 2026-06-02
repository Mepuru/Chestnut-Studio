"""资源管理模块

统一管理应用程序的资源文件路径。
支持开发环境和 PyInstaller 打包环境。
"""

import sys
from pathlib import Path


def _get_resources_dir() -> Path:
    """获取资源目录路径

    支持开发环境和 PyInstaller 打包环境

    Returns:
        资源目录的绝对路径
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstaller 打包环境
        return Path(sys._MEIPASS) / "chestnut_studio" / "resources"
    else:
        # 开发环境
        return Path(__file__).parent / "resources"


# 资源目录路径
_RESOURCES_DIR = _get_resources_dir()


def get_resource_path(relative_path: str) -> Path:
    """获取资源文件的绝对路径

    Args:
        relative_path: 相对于resources目录的路径

    Returns:
        资源文件的绝对路径
    """
    return _RESOURCES_DIR / relative_path


def get_icon_path(name: str = "") -> Path:
    """获取图标文件的路径

    Args:
        name: 图标文件名（不含后缀），如 "play"、"send"。
              空字符串返回应用图标 icon.png。

    Returns:
        图标文件的绝对路径
    """
    if not name:
        return get_resource_path("icon.png")
    return get_resource_path(f"icons/{name}.svg")


def get_stylesheet_path() -> Path:
    """获取样式表文件的路径

    Returns:
        style.qss的绝对路径
    """
    return get_resource_path("style.qss")


def get_fonts_dir() -> Path:
    """获取字体目录的路径

    Returns:
        fonts目录的绝对路径
    """
    return get_resource_path("fonts")
