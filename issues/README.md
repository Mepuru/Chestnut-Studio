# Chestnut Studio — Issue 跟踪

> 项目改进方案、架构提案、技术债务的集中管理。
> 每个 Issue 独立文件夹，完成后合并到 `docs/`。

---

## 工作流

```
Issue 生命周期:

  提案 ──► 评审 ──► 实施 ──► 验收 ──► 合并到 docs/
  (issues/)                          (删除 issue 文件夹)
```

### 状态定义

| 状态 | 含义 | 标记 |
|------|------|------|
| `proposed` | 提案中，待评审 | Issue 文件夹存在 |
| `accepted` | 已接受，待实施 | `STATUS` 文件中标记 |
| `in_progress` | 实施中 | `STATUS` 文件中标记 |
| `delivered` | 已交付，待验收 | 移入 `_delivered/` 子目录 |
| `merged` | 已合并到 docs/ | 删除 Issue 文件夹，更新本文件 |

### 交付流程

1. 实施完成后，将 Issue 文件夹移入 `_delivered/`
2. 在 Issue 的 `STATUS` 文件中标记 `delivered`
3. 验收通过后，将文档合并到 `docs/` 对应位置
4. 删除 Issue 文件夹，更新本文件的 Issue 列表

---

## Issue 列表

### 进行中

| Issue | 状态 | 说明 | 文档数 |
|-------|------|------|--------|
| [scalability](scalability/) | `proposed` | 可扩展架构方案：BaseCard、注册表、声明式信号、配置驱动布局 | 6 |

### 已完成

（暂无）

---

## 目录结构

```
issues/
├── README.md                      # 本文件 — Issue 导航
├── _template/                     # Issue 模板（可选）
│   └── ISSUE_TEMPLATE.md
├── _delivered/                    # 已交付待验收的 Issue
├── scalability/                   # Issue #1: 可扩展架构
│   ├── STATUS                     # 状态标记
│   ├── architecture_scalability.md  # 总览文档
│   ├── base_card.md               # BaseCard 基类设计
│   ├── card_registry.md           # 卡片注册表设计
│   ├── declarative_signals.md     # 声明式信号系统设计
│   ├── layout_system.md           # 配置驱动布局系统设计
│   └── auto_menu.md               # 菜单自动生成设计
└── ...                            # 未来 Issue
```

---

## 创建新 Issue

1. 在 `issues/` 下创建文件夹，命名使用小写英文 + 连字符
2. 创建 `STATUS` 文件，内容为状态标记
3. 编写方案文档
4. 更新本文件的 Issue 列表

### STATUS 文件格式

```
status: proposed
title: 可扩展架构方案
created: 2026-05-10
updated: 2026-05-10
```

---

## 与 docs/ 的关系

| 目录 | 性质 | 内容 |
|------|------|------|
| `docs/` | 正式文档 | 已实现、已验收的文档 |
| `issues/` | 提案/跟踪 | 待评审、实施中、待验收的方案 |

**原则**: `issues/` 中的文档是提案性质，未经实施验收不进入 `docs/`。
