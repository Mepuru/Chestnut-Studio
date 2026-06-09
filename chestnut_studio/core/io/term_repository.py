"""术语读写

纯 I/O 操作：从磁盘读取或追加术语数据。
不包含业务逻辑——读取后的数据处理由调用方（manager/）负责。
"""

from __future__ import annotations

from pathlib import Path

from chestnut_studio.core.model.note import Term


def append_terms(terms: list[Term], path: str | Path) -> None:
    """将术语追加到文本文件末尾"""
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + "# --- 术语 ---" + "\n")
        for term in terms:
            f.write(term.to_line() + "\n")


def read_terms(path: str | Path) -> list[Term]:
    """从文本文件读取术语（区块格式）

    从文件中提取 # --- 术语 --- 标记后的所有术语块并解析。

    Returns:
        解析成功的术语列表
    """
    terms: list[Term] = []
    in_terms = False
    block = ""

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
                        terms.append(t)
                block = s + "\n"
            else:
                block += line
        if block:
            t = Term.from_block(block)
            if t:
                terms.append(t)

    return terms
