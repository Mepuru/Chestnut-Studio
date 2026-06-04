"""版本号工具

版本号唯一来源：pyproject.toml [project] version 字段。
运行时优先级：importlib.metadata → 直接读取 pyproject.toml。
"""

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _read_pyproject_toml() -> str:
    """从 pyproject.toml 直接读取版本号（打包环境后备）"""
    # 依次尝试常见路径
    candidates = [
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
    优先级: importlib.metadata → 直接读取 pyproject.toml → "unknown"

    Returns:
        版本号字符串，如 "2.1.0"
    """
    try:
        return version("chestnut-studio")
    except PackageNotFoundError:
        return _read_pyproject_toml()
