"""项目文件读写

纯 I/O 操作：从磁盘读取或写入 .chestnut 项目文件。
不包含业务逻辑——数据处理由调用方（manager/ 或 ui/）负责。
"""

from __future__ import annotations

import json
from pathlib import Path

from chestnut_studio.core.model.session import SessionState


def read_project(path: str | Path) -> SessionState | None:
    """从指定路径读取 .chestnut 项目文件，损坏时返回 None"""
    try:
        data: dict[str, object] = json.loads(Path(path).read_text(encoding="utf-8"))
        return SessionState.from_dict(data)
    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def write_project(state: SessionState, path: str | Path) -> None:
    """写入 .chestnut 项目文件到指定路径"""
    Path(path).write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
