"""GitHub 版本更新检查

纯数据定义 + 工具函数，不依赖 PySide6。
网络请求由 UI 层（QNetworkAccessManager）完成，数据解析通过此模块完成。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UpdateInfo:
    """新版本信息"""

    latest_version: str
    download_url: str
    release_notes: str
    release_url: str


API_URL = "https://api.github.com/repos/Mepuru/Chestnut-Studio/releases/latest"


def parse_version(v: str) -> tuple[int, ...]:
    """将版本字符串转为可比较的整数元组

    >>> parse_version("v2.3.0")
    (2, 3, 0)
    """
    return tuple(int(x) for x in v.strip("v").split("."))


def parse_release_data(data: dict, current_version: str) -> UpdateInfo | None:
    """从 GitHub API 返回的 JSON 中解析更新信息

    Args:
        data: GitHub Releases API 返回的 JSON 字典
        current_version: 当前版本号（如 "2.3.0"）

    Returns:
        有新版本时返回 UpdateInfo，否则返回 None
    """
    tag = data.get("tag_name", "")
    if not tag:
        return None

    latest = parse_version(tag)
    current = parse_version(current_version)

    if latest <= current:
        return None

    assets = data.get("assets", [])
    return UpdateInfo(
        latest_version=tag.lstrip("v"),
        download_url=assets[0].get("browser_download_url", "") if assets else "",
        release_notes=data.get("body", ""),
        release_url=data.get("html_url", ""),
    )
