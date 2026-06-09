"""笔记管理器模块

编排 Notes 和 Terms 的 CRUD、导入导出。
数据模型定义位于 core/model/note.py。
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from chestnut_studio.core.model.note import Note, Term
from chestnut_studio.core.track_config import NOTE_TYPES, TRACK_COLORS_HEX
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
        note = Note(timestamp_ms=timestamp_ms, text=text, type=note_type)
        self._notes.append(note)
        self._notes.sort(key=lambda n: n.timestamp_ms)
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
        return [n for n in self._notes if n.type == note_type]

    def get_used_types(self) -> list[str]:
        """获取有数据的轨道列表"""
        used = set(n.type for n in self._notes)
        return [t for t in NOTE_TYPES if t in used]

    def count(self) -> int:
        return len(self._notes)

    # ── 文本格式导出/导入 ──

    @staticmethod
    def _build_track_colors_line(types: Sequence[str] | None = None) -> str:
        """生成轨道颜色行，例如 '轨道1=#3b82f6, 轨道2=#10b981'"""
        used_types = types or NOTE_TYPES
        pairs = []
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
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(
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
                id_map = self.assign_ids()
                for n in notes:
                    f.write(n.to_line(id_map.get(n, 0)) + "\n")
        except OSError as e:
            self._logger.error(f"导出文本失败: {path} — {e}")
            raise OSError(f"导出笔记失败: {e}") from e
        self._logger.info(f"导出文本: {len(notes)} 条 → {path}")
        return len(notes)

    def assign_ids(self) -> dict[Note, int]:
        """按时间排序分配序号，返回 {Note对象: 序号} 映射"""
        self._notes.sort(key=lambda n: n.timestamp_ms)
        return {note: i for i, note in enumerate(self._notes, 1)}

    def get_note_id(self, note: Note) -> int:
        """获取笔记在当前排序下的序号"""
        self._notes.sort(key=lambda n: n.timestamp_ms)
        for i, n in enumerate(self._notes, 1):
            if n is note:
                return i
        return 0

    def import_text(self, path: str | Path) -> int:
        """从文本文件导入笔记"""
        count = 0
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    note = Note.from_line(line)
                    if note:
                        self._notes.append(note)
                        count += 1
        except (OSError, UnicodeDecodeError) as e:
            self._logger.error(f"导入文本失败: {path} — {e}")
            raise OSError(f"导入笔记失败: {e}") from e
        self._notes.sort()
        self._logger.info(f"导入文本: {count} 条 ← {path}")
        return count

    def export_json(self, path: str | Path, types: list[str] | None = None) -> int:
        notes = self._notes if types is None else [n for n in self._notes if n.type in types]
        data = {"version": 1, "notes": [n.to_dict() for n in notes]}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            self._logger.error(f"导出 JSON 失败: {path} — {e}")
            raise OSError(f"导出 JSON 失败: {e}") from e
        self._logger.info(f"导出 JSON: {len(notes)} 条 → {path}")
        return len(notes)

    def import_json(self, path: str | Path) -> int:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            self._logger.error(f"导入 JSON 失败: {path} — {e}")
            raise OSError(f"导入 JSON 失败: {e}") from e
        for item in data.get("notes", []):
            note = Note.from_dict(item)
            self._notes.append(note)
        self._notes.sort()
        count = len(data.get("notes", []))
        self._logger.info(f"导入 JSON: {count} 条 ← {path}")
        return count

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
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n" + "# --- 术语 ---" + "\n")
                for term in self._terms:
                    f.write(term.to_line() + "\n")
        except OSError as e:
            self._logger.error(f"导出术语失败: {path} — {e}")
            raise OSError(f"导出术语失败: {e}") from e
        self._logger.info(f"导出术语: {len(self._terms)} 条")
        return len(self._terms)

    def import_terms(self, path: str | Path) -> int:
        """从文件导入术语（区块格式）"""
        count = 0
        in_terms = False
        block = ""
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not in_terms:
                        if s == "# --- 术语 ---" or s == "# 术语":
                            in_terms = True
                        continue
                    if not s:
                        continue
                    if s.startswith("# ---"):
                        if block:
                            t = Term.from_block(block)
                            if t:
                                self.add_term(t.source, t.translation, t.origin, t.note)
                                count += 1
                        block = s + "\n"
                    else:
                        block += line
                if block:
                    t = Term.from_block(block)
                    if t:
                        self.add_term(t.source, t.translation, t.origin, t.note)
                        count += 1
        except (OSError, UnicodeDecodeError) as e:
            self._logger.error(f"导入术语失败: {path} — {e}")
            raise OSError(f"导入术语失败: {e}") from e
        self._logger.info(f"导入术语: {count} 条")
        return count
