"""I/O 模块 — 文件读写，无 PySide6 依赖

本包处理所有文件系统操作：笔记导入导出、术语库读写、字幕文件解析。
不包含业务逻辑——数据从磁盘读入后的处理交由 compute/ 或 manager/。

分层规则:
  io/ → 依赖 model/ + compute/，可被 manager/、ui/ 引用
  io/ 不可反向依赖 manager/
"""

from chestnut_studio.core.io.ass_repository import read_ass, read_txt_notes
from chestnut_studio.core.io.ass_writer import generate_merge_report, write_output
from chestnut_studio.core.io.note_repository import (
    read_notes_text,
    write_notes_text,
)
from chestnut_studio.core.io.term_repository import append_terms, read_terms

__all__ = [
    "write_notes_text",
    "read_notes_text",
    "append_terms",
    "read_terms",
    "read_ass",
    "read_txt_notes",
    "generate_merge_report",
    "write_output",
]
