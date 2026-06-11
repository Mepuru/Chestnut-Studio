"""ASS+TXT 字幕合并编排

将 Chestnut Studio 导出的 TXT 笔记文本合并到 ASS 字幕时间轴中。
职责：文件解析 → 委托计算引擎 → 返回结果。
具体文件解析位于 core/io/ass_repository.py，纯计算位于 core/compute/ass_merge_engine.py。

用法:
     from chestnut_studio.core.manager.ass_merge import build_merge_plan
    from chestnut_studio.core.io.ass_writer import generate_merge_report, write_output

    plan = build_merge_plan("input.ass", "notes.txt")
    print(generate_merge_report(plan))  # 查看不确定项
    write_output(plan, "output.ass")    # 写出 ASS + 报告
"""

from chestnut_studio.core.compute.ass_merge_engine import compute_merge_plan
from chestnut_studio.core.io.ass_repository import read_ass, read_txt_notes
from chestnut_studio.core.model.ass_merge import MergePlan


def build_merge_plan(ass_path: str, txt_path: str) -> MergePlan:
    """构建合并计划——纯计算引擎的 I/O 编排器

    流程:
    1. 解析 ASS 和 TXT 文件
    2. 委托 compute_merge_plan 执行匹配算法
    3. 返回 MergePlan
    """
    dialogues, raw_lines = read_ass(ass_path)
    notes, track_colors = read_txt_notes(txt_path)

    return compute_merge_plan(
        dialogues=dialogues,
        notes=notes,
        track_colors=track_colors,
        ass_path=ass_path,
        txt_path=txt_path,
        raw_ass_lines=raw_lines,
    )
