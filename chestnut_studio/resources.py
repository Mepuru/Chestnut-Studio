"""资源管理模块

统一管理应用程序的资源文件路径。
"""

from pathlib import Path

# 资源目录路径
_RESOURCES_DIR = Path(__file__).parent / "resources"


def get_resource_path(relative_path: str) -> Path:
    """获取资源文件的绝对路径
    
    Args:
        relative_path: 相对于resources目录的路径
        
    Returns:
        资源文件的绝对路径
    """
    return _RESOURCES_DIR / relative_path


def get_icon_path() -> Path:
    """获取应用程序图标的路径
    
    Returns:
        icon.png的绝对路径
    """
    return get_resource_path("icon.png")


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
