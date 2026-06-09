"""编排器模块 — 组合 model + compute + io 的轻量胶水代码

编排器位于此目录：
  note_manager.py  — NoteManager（笔记 CRUD + 导入导出编排）
  ass_merge.py     — build_merge_plan（ASS+TXT 合并编排）

分层规则:
  manager/ → 依赖 model/、compute/、io/，可被 ui/ 引用
  manager/ 不可反向依赖 UI 层
"""
