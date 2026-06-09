"""ASS+TXT 字幕合并数据模型

纯数据类定义。MergePlan 的 I/O 方法通过 core/io/ass_writer 实现。
数据类无 PySide6 依赖。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AssDialogue:
    """ASS 文件中的一条 Dialogue"""

    line_index: int  # 在原始文件中的行号
    start_s: float  # 开始时间（秒）
    end_s: float  # 结束时间（秒）
    start_str: str  # 原始时间字符串 h:mm:ss.xx
    end_str: str  # 原始时间字符串 h:mm:ss.xx
    style: str  # 样式名
    text: str  # 文本内容（初始为空）
    raw_before_text: str  # "Dialogue: ..." 最后一个逗号之前的部分
    track: str = ""  # 轨道名（从 TXT 继承）
    src_note_idx: int = 0  # 源 TXT 序号（0=无来源）


@dataclass
class TxtNote:
    """TXT 笔记中的一条"""

    index: int  # 在 TXT 中的序号（从1开始）
    time_s: float  # 时间点（秒）
    track: str  # 轨道名
    text: str  # 文本内容


@dataclass
class UncertainMatch:
    """不能 100% 确定的匹配项——需要手动处理"""

    ass_idx: int  # ASS 行索引
    ass_start: str  # ASS 开始时间
    ass_end: str  # ASS 结束时间
    notes: list[TxtNote]  # 候选 TXT 笔记
    reason: str  # 原因


@dataclass
class MergePlan:
    """完整的合并计划"""

    ass_path: str
    txt_path: str
    dialogues: list[AssDialogue]
    notes: list[TxtNote]
    total_notes: int  # TXT 总条数
    auto_matched: int  # 100% 确定自动匹配的条数
    uncertain: list[UncertainMatch]  # 不确定的匹配项（需手动）
    risky: list[UncertainMatch]  # 潜在风险项（重叠区就近分配）
    _raw_ass_lines: list[str] = field(repr=False)  # 原始 ASS 行
    track_colors: dict[str, str] = field(default_factory=dict[str, str])  # 轨道名→颜色
