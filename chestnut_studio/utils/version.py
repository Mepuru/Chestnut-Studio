"""版本号工具

版本号唯一来源：pyproject.toml [project] version 字段。
运行时优先级：直接读取 pyproject.toml → importlib.metadata → "unknown"。
"""

import re
from pathlib import Path

try:
    from importlib.metadata import version as _metadata_version
except ImportError:
    _metadata_version = None


def _read_pyproject_toml() -> str:
    """从 pyproject.toml 直接读取版本号"""
    candidates = [
        # Nuitka standalone: pyproject.toml 被 --include-data-file 打包到 dist 根目录
        # 开发环境: __file__ 回溯两级到 package 根，再回溯一级到项目根
        Path(__file__).parent.parent.parent / "pyproject.toml",
        Path.cwd() / "pyproject.toml",
    ]
    for path in candidates:
        if path.exists():
            match = re.search(r'^version\s*=\s*"([^"]+)"', path.read_text("utf-8"), re.MULTILINE)
            if match:
                return match.group(1)
    return "unknown"


def get_version() -> str:
    """获取当前版本号

    从 pyproject.toml 中定义的版本号读取。
    优先级: 直接读取 pyproject.toml → importlib.metadata → "unknown"

    Returns:
        版本号字符串，如 "2.5.0"
    """
    v = _read_pyproject_toml()
    if v != "unknown":
        return v
    if _metadata_version is not None:
        try:
            return _metadata_version("chestnut-studio")
        except Exception:
            pass
    return "unknown"
