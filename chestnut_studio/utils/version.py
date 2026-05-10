"""版本号工具

版本号唯一来源：pyproject.toml [project] version 字段。
运行时通过 importlib.metadata 读取，打包后也能正确获取。
"""

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    """获取当前版本号

    从 pyproject.toml 中定义的版本号读取（通过 importlib.metadata）。
    如果无法获取（如未安装），返回 "unknown"。

    Returns:
        版本号字符串，如 "1.1.1"
    """
    try:
        return version("chestnut-studio")
    except PackageNotFoundError:
        return "unknown"
