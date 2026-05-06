# Chestnut Studio

> 现代化卡片化字幕工具 - 基于 PySide6 的字幕编辑器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## 简介

Chestnut Studio 是一款面向字幕组/烤肉组的现代化字幕工具，采用卡片化工作台设计，支持自由布局调整。

## 核心特性

- **卡片化工作台** - 四张独立卡片，可拖拽、停靠、浮动、调整大小
- **视频播放** - 支持多种格式，字幕叠加预览，AB 循环
- **音频波形** - 实时波形显示，红线跟随播放，包络线增强
- **双轴时间轴** - 源轴 + 译文轴，支持同步调整，ASS 双轴导出
- **翻译面板** - 简单文本区域，手动填写翻译（Phase 4）
- **现代暗色主题** - 圆角卡片，深蓝灰配色

## 界面布局

```
┌──────────────────────────────────────────────────────────────────────┐
│  菜单栏 / 工具栏（播放控制 · AB循环 · 轴选择 · 倍速 · 帧号）          │
├────────────────────────────────┬─────────────────────────────────────┤
│    ① 视频播放区                 │    ③ 双轴时间轴区                    │
│    - 视频渲染 + 字幕叠加预览    │    - 源轴（源语言字幕）               │
│    - 滚轮缩放 · 拖放打开        │    - 译文轴（翻译字幕）               │
│                                │    - 同步调整 · ASS 导出              │
├────────────────────────────────┼─────────────────────────────────────┤
│    ② 音频波形区                 │    ④ 翻译面板（Phase 4）            │
│    - 主音轨波形 + 包络线        │    - 简单文本区域                     │
│    - 字幕条覆盖 · 红线跟随      │    - 手动填写/编辑翻译                │
│    - Shift+拖动平移 · 滚轮缩放  │                                     │
└────────────────────────────────┴─────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.12+
- FFmpeg（需要加入 PATH）

### 安装

```bash
# 克隆仓库
git clone https://gitee.com/kurikana/chestnut-studio.git
cd chestnut-studio

# 使用 uv 安装依赖
uv sync

# 激活虚拟环境
.venv\Scripts\activate
```

### 运行

```bash
# 运行应用
uv run python main.py

# 或者激活虚拟环境后直接运行
python main.py
```

### 开发

```bash
# 安装开发依赖
uv sync --group dev

# 运行测试
uv run pytest

# 代码检查
uv run ruff check chestnut_studio/

# 代码格式化
uv run ruff format chestnut_studio/
```

## 项目结构

```
ChestnutStudio/
├── main.py                        # 入口文件
├── CLAUDE.md                      # AI 开发指南
├── chestnut_studio/               # 主模块
│   ├── __init__.py
│   ├── core/                      # 核心逻辑（无 UI 依赖）
│   │   ├── __init__.py
│   │   ├── ffmpeg.py              # FFmpeg 封装
│   │   ├── audio.py               # 音频数据处理
│   │   ├── subtitle.py            # 字幕数据结构
│   │   └── subtitle_io.py         # 字幕导入/导出
│   ├── ui/                        # UI 层
│   │   ├── __init__.py
│   │   ├── main_window.py         # 主窗口
│   │   ├── toolbar.py             # 工具栏
│   │   ├── menubar.py             # 菜单栏
│   │   ├── statusbar.py           # 状态栏
│   │   ├── cards/                 # 卡片组件
│   │   │   ├── __init__.py
│   │   │   ├── player_card.py     # 视频播放卡片
│   │   │   ├── waveform_card.py   # 音频波形卡片
│   │   │   ├── timeline_card.py   # 双轴时间轴卡片
│   │   │   └── translate_card.py  # 翻译面板卡片
│   │   └── dialogs/               # 弹窗
│   │       └── __init__.py
│   ├── utils/                     # 工具函数
│   │   ├── __init__.py
│   │   └── time_utils.py          # 时间格式转换
│   └── resources/                 # 资源文件
│       ├── style.qss              # 暗色主题样式表
│       └── fonts/                 # 字体（HarmonyOS Sans）
├── docs/                          # 文档
│   ├── architecture.md            # 架构文档
│   ├── development.md             # 开发指南
│   ├── core.md                    # 核心层模块文档
│   ├── ui.md                      # UI 层模块文档
│   ├── utils.md                   # 工具层模块文档
│   └── changelog.md               # 变更日志
├── tests/                         # 测试
│   ├── conftest.py                # 测试配置
│   ├── test_phase0.py             # Phase 0 测试
│   ├── test_phase1.py             # Phase 1 测试
│   ├── test_phase2.py             # Phase 2 测试
│   └── test_subtitle.py           # 字幕测试
├── prototypes/                    # 设计文档
├── pyproject.toml                 # 项目配置
├── uv.lock                        # 依赖锁定
├── README.md
└── LICENSE                        # MIT 协议
```

## 开发路线

- **Phase 0** - 基础设施（项目骨架 + 主题）✅
- **Phase 1** - 视频播放（播放器卡片 + 工具栏）✅
- **Phase 2** - 音频波形（波形图卡片 + FFmpeg）✅
- **Phase 3** - 双轴时间轴（源轴 + 译文轴 + 同步调整）
- **Phase 4** - 翻译面板（翻译卡片 + 字幕导入导出 + ASS 双轴导出）
- **Phase 5** - 打磨收尾（布局持久化 + 打包）

详见 [roadmap.md](prototypes/roadmap.md)

## 快捷键

### 全局快捷键

| 按键 | 功能 |
|------|------|
| `Space` | 播放/暂停 |
| `[` | 设置 AB 循环 A 点 |
| `]` | 设置 AB 循环 B 点 |
| `\` | 清除 AB 循环 |
| `Ctrl+O` | 打开视频文件 |

### 波形图操作

| 操作 | 功能 |
|------|------|
| `左键点击` | 跳转到点击位置 |
| `Shift + 左键拖动` | 平移视窗 |
| `滚轮` | 缩放视窗 |

### 字幕列表操作

| 操作 | 功能 |
|------|------|
| `右键点击` | 显示编辑菜单 |
| `双击` | 跳转到字幕位置 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Tab` | 切换轴（源轴↔译文轴） |

## 技术栈

- **UI 框架**: PySide6 (Qt6)
- **波形图**: pyqtgraph
- **数据处理**: numpy
- **包管理**: uv
- **代码检查**: ruff
- **测试框架**: pytest

## 协议

本项目使用 [MIT 协议](LICENSE)。
