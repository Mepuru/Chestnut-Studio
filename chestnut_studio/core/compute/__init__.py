"""计算模块 — 纯函数，零 I/O，零副作用

本包中的所有模块均为纯计算函数：
- 输入决定输出，无状态
- 无文件 I/O、无网络请求
- 不依赖 PySide6

用于替换核心层中原本与 I/O 耦合在一起的计算逻辑，
也为纯计算逻辑提供清晰的边界接口。

分层规则:
  compute/ → 依赖 model/，可被 io/、manager/、ui/ 引用
  compute/ 不可反向依赖 io/ 或 manager/
"""

from chestnut_studio.core.compute.ass_merge_engine import compute_merge_plan
from chestnut_studio.core.compute.note_processor import (
    assign_note_ids,
    filter_notes_by_type,
    get_note_id,
    get_used_note_types,
)

__all__ = [
    "assign_note_ids",
    "get_note_id",
    "filter_notes_by_type",
    "get_used_note_types",
    "compute_merge_plan",
]
