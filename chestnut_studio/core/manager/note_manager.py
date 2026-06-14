"""笔记管理器模块

编排 Notes 和 Terms 的 CRUD、导入导出。
数据模型位于 core/model/note.py，计算逻辑位于 core/compute/note_processor.py，
文件 I/O 位于 core/io/note_repository.py 和 core/io/term_repository.py。
"""

from __future__ import annotations

import bisect
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from chestnut_studio.core.compute.note_processor import (
    assign_note_ids,
    filter_notes_by_type,
    get_used_note_types,
)
from chestnut_studio.core.compute.note_processor import (
    get_note_id as compute_get_note_id,
)
from chestnut_studio.core.compute.note_processor import (
    search_notes as compute_search_notes,
)
from chestnut_studio.core.io.note_repository import (
    read_notes_text,
    write_notes_text,
)
from chestnut_studio.core.io.term_repository import append_terms, read_terms
from chestnut_studio.core.model.config import NOTE_TYPES, TRACK_COLORS_HEX
from chestnut_studio.core.model.note import Note, Term
from chestnut_studio.utils import get_logger
from chestnut_studio.utils.time_utils import ms_to_time_str
from chestnut_studio.utils.version import get_version

# 导出文本格式说明（文件头）
EXPORT_HEADER = """# Chestnut Studio Notes v{version}
# 术语数: {terms}
# 视频: {video}
# 时长: {duration}
# 分辨率: {resolution}
# 帧率: {fps}
# 码率: {bitrate}
# 导出时间: {time}
# 轨道颜色: {track_colors}
# 格式: 轨道名  时间	| 内容
# 批量删除前缀: 用正则替换  ^.+?\\d{{2}}:\\d{{2}}\\.\\d{{2}}\t\\|  为空
# ---"""


class NoteManager:
    """笔记管理器"""

    def __init__(self):
        self._notes: list[Note] = []
        self._terms: list[Term] = []
        self._logger = get_logger("NoteManager")

    # ── 增 ──

    def add(self, timestamp_ms: int, text: str, note_type: str = "轨道1") -> Note:
        if note_type not in NOTE_TYPES:
            raise ValueError(f"笔记类型必须为 {NOTE_TYPES}，收到: {note_type}")
        note = Note(timestamp_ms=timestamp_ms, text=text, type=note_type)
        bisect.insort(self._notes, note)
        self._logger.info(f"添加笔记: [{note_type}] {ms_to_time_str(timestamp_ms)} {text[:50]}")
        return note

    # ── 删 ──

    def remove(self, note: Note) -> bool:
        try:
            self._notes.remove(note)
            self._logger.info(f"删除笔记: [{note.type}] {ms_to_time_str(note.timestamp_ms)} {note.text[:50]}")
            return True
        except ValueError:
            return False

    def clear(self):
        self._notes.clear()

    # ── 查 ──

    def get_all(self) -> list[Note]:
        return list(self._notes)

    def get_by_type(self, note_type: str) -> list[Note]:
        return filter_notes_by_type(self._notes, note_type)

    def get_used_types(self) -> list[str]:
        return get_used_note_types(self._notes, NOTE_TYPES)

    def search(self, query: str) -> list[Note]:
        return compute_search_notes(self._notes, query)

    def count(self) -> int:
        return len(self._notes)

    # ── 文本格式导出/导入 ──

    @staticmethod
    def _build_track_colors_line(types: Sequence[str] | None = None) -> str:
        """生成轨道颜色行，例如 '轨道1=#3b82f6, 轨道2=#10b981'"""
        used_types = types or NOTE_TYPES
        pairs: list[str] = []
        for i, name in enumerate(used_types):
            pairs.append(f"{name}={TRACK_COLORS_HEX[i % len(TRACK_COLORS_HEX)]}")
        return ", ".join(pairs)

    def export_text(
        self,
        path: str | Path,
        types: list[str] | None = None,
        video_name: str = "",
        video_duration: str = "",
        video_resolution: str = "",
        video_fps: str = "",
        video_bitrate: str = "",
    ) -> int:
        notes = self._notes if types is None else [n for n in self._notes if n.type in types]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        track_colors = self._build_track_colors_line(types)
        header = (
            EXPORT_HEADER.format(
                version=get_version(),
                video=video_name,
                duration=video_duration,
                resolution=video_resolution,
                fps=video_fps,
                bitrate=video_bitrate,
                time=now,
                terms=len(self._terms),
                track_colors=track_colors,
            )
            + "\n"
        )
        try:
            id_map = self.assign_ids()
            write_notes_text(notes, path, header, id_map)
        except OSError as e:
            self._logger.error(f"导出文本失败: {path} — {e}")
            raise OSError(f"导出笔记失败: {e}") from e
        self._logger.info(f"导出文本: {len(notes)} 条 → {path}")
        return len(notes)

    def assign_ids(self) -> dict[Note, int]:
        """按时间排序分配序号，返回 {Note对象: 序号} 映射"""
        self._notes.sort()
        return assign_note_ids(self._notes)

    def get_note_id(self, note: Note) -> int:
        """获取笔记在当前排序下的序号"""
        self._notes.sort()
        return compute_get_note_id(self._notes, note)

    def import_text(self, path: str | Path) -> int:
        """从文本文件导入笔记"""
        try:
            imported = read_notes_text(path)
        except (OSError, UnicodeDecodeError) as e:
            self._logger.error(f"导入文本失败: {path} — {e}")
            raise OSError(f"导入笔记失败: {e}") from e
        self._notes.extend(imported)
        self._notes.sort()
        self._logger.info(f"导入文本: {len(imported)} 条 ← {path}")
        return len(imported)

    # ── JSON 序列化（自动保存/项目文件） ──

    def to_dict(self) -> dict[str, Any]:
        """将所有笔记和术语序列化为可 JSON 序列化的 dict"""
        return {
            "notes": [n.to_dict() for n in self._notes],
            "terms": [t.to_dict() for t in self._terms],
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """从 dict 恢复笔记和术语（清空当前数据后加载）"""
        self._notes.clear()
        self._terms.clear()
        for n in data.get("notes", []):
            self._notes.append(Note.from_dict(n))
        for t in data.get("terms", []):
            self._terms.append(Term.from_dict(t))
        self._notes.sort()

    # ── 术语库 ──

    def add_term(self, source: str, translation: str, origin: str = "", note: str = "") -> Term:
        """添加术语"""
        term = Term(source=source, translation=translation, origin=origin, note=note)
        # 如果 source 已存在则替换
        for i, t in enumerate(self._terms):
            if t.source == source:
                self._terms[i] = term
                self._logger.debug(f"更新术语: {source} → {translation}")
                return term
        self._terms.append(term)
        self._logger.debug(f"添加术语: {source} → {translation}")
        return term

    def get_terms(self) -> list[Term]:
        return list(self._terms)

    def update_term(self, old_source: str, new_source: str, translation: str, origin: str, note: str) -> bool:
        """更新术语"""
        for i, t in enumerate(self._terms):
            if t.source == old_source:
                self._terms[i] = Term(source=new_source, translation=translation, origin=origin, note=note)
                return True
        return False

    def remove_term(self, source: str) -> bool:
        for i, t in enumerate(self._terms):
            if t.source == source:
                self._terms.pop(i)
                return True
        return False

    def clear_terms(self):
        self._terms.clear()

    def term_count(self) -> int:
        return len(self._terms)

    def export_terms(self, path: str | Path) -> int:
        """导出术语库到文件末尾"""
        try:
            append_terms(self._terms, path)
        except OSError as e:
            self._logger.error(f"导出术语失败: {path} — {e}")
            raise OSError(f"导出术语失败: {e}") from e
        self._logger.info(f"导出术语: {len(self._terms)} 条")
        return len(self._terms)

    def import_terms(self, path: str | Path) -> int:
        """从文件导入术语（区块格式）"""
        try:
            imported = read_terms(path)
        except (OSError, UnicodeDecodeError) as e:
            self._logger.error(f"导入术语失败: {path} — {e}")
            raise OSError(f"导入术语失败: {e}") from e
        count = 0
        for t in imported:
            self.add_term(t.source, t.translation, t.origin, t.note)
            count += 1
        self._logger.info(f"导入术语: {count} 条")
        return count
