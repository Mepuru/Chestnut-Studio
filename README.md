<div align="center">
    <img alt="Chestnut Studio" src="chestnut_studio/resources/icon.png" width=180 height=180/>

# Chestnut Studio

现代化卡片化字幕工具 - 基于 PySide6 的字幕编辑器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

</div>

## 简介

Chestnut Studio 是一款面向字幕组/烤肉组的现代化字幕工具，采用卡片化工作台设计，支持自由布局调整。

## 核心特性

- **卡片化工作台** - 四张独立卡片，可拖拽、停靠、浮动、调整大小
- **视频播放** - 支持多种格式，字幕叠加预览，AB 循环
- **音频波形** - 实时波形显示，红线跟随播放，包络线增强
- **打轴功能** - 在音频波形区通过快捷键打轴，时间轴列表显示
- **编辑模式** - 可视化调整字幕起止点，实时预览
- **多轨道支持** - 最多 8 个轨道，不同颜色区分
- **复制轴功能** - 将一个轨道的字幕复制到另一个轨道
- **翻译面板** - 编辑当前轨道字幕文本，支持快速跳转（Ctrl+Enter）
- **字幕导入导出** - 支持 SRT/ASS 格式导入，多轨道 ASS 导出
- **现代暗色主题** - 圆角卡片，深蓝灰配色

## 界面布局

```
┌──────────────────────────────────────────────────────────────────────┐
│  菜单栏 / 工具栏（播放控制 · AB循环 · 倍速 · 帧号）                   │
├────────────────────────┬─────────────────────────────────────────────┤
│    ① 视频播放区         │    ③ 时间轴列表区                          │
│    - 视频渲染           │    - 已打轴的字幕列表                       │
│    - 字幕叠加预览       │    - 查看/编辑/锁定/删除                    │
├────────────────────────┼─────────────────────────────────────────────┤
│    ② 音频波形区         │    ④ 翻译面板                              │
│    - 主音轨波形         │    - 源语言 → 目标语言                      │
│    - I/O 键打轴         │    - 快速跳转                               │
└────────────────────────┴─────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.12+
- FFmpeg（需要加入 PATH，详见 [FFmpeg 安装指南](docs/ffmpeg-setup.md)）

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

## 快捷键

### 全局快捷键

| 按键 | 功能 |
|------|------|
| `Space` | 播放/暂停 |
| `[` | 设置 AB 循环 A 点 |
| `]` | 设置 AB 循环 B 点 |
| `\` | 清除 AB 循环 |
| `Ctrl+O` | 打开视频文件 |
| `1` `2` `3` `4` | 切换轨道 |

### 波形图操作

| 操作 | 功能 |
|------|------|
| `左键点击` | 跳转到点击位置 |
| `Shift + 左键拖动` | 平移视窗 |
| `滚轮` | 缩放视窗 |
| `I` | 标记字幕开始点（打轴） / 编辑模式设为起点 |
| `O` | 标记字幕结束点（打轴） / 编辑模式设为终点 |
| `Enter` | 确认编辑（编辑模式） |
| `Escape` | 取消编辑（编辑模式） |

### 时间轴列表操作

| 操作 | 功能 |
|------|------|
| `点击查看` | 跳转到字幕起始点 |
| `点击编辑` | 进入编辑模式，可视化调整区间 |
| `点击锁定` | 切换锁定状态 |
| `点击删除` | 删除字幕 |
| `双击行` | 跳转到起始点 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Delete` | 删除选中字幕 |

### 翻译面板操作

| 操作 | 功能 |
|------|------|
| `Ctrl+Enter` | 保存并跳转到下一条字幕 |
| `Shift+Enter` | 跳转到上一条字幕 |
| `Enter` | 换行（文本框内） |

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
│   │   ├── subtitle_io.py         # 字幕导入/导出
│   │   └── track_config.py        # 轨道配置（颜色、数量）
│   ├── ui/                        # UI 层
│   │   ├── __init__.py
│   │   ├── main_window.py         # 主窗口
│   │   ├── toolbar.py             # 工具栏
│   │   ├── menubar.py             # 菜单栏
│   │   ├── statusbar.py           # 状态栏
│   │   ├── drag_overlay.py        # 拖放覆盖层
│   │   ├── cards/                 # 卡片组件
│   │   │   ├── __init__.py
│   │   │   ├── player_card.py     # 视频播放卡片
│   │   │   ├── waveform_card.py   # 音频波形卡片
│   │   │   ├── timeline_card.py   # 打轴编辑卡片
│   │   │   └── translate_card.py  # 翻译面板卡片
│   │   └── dialogs/               # 弹窗
│   │       ├── __init__.py
│   │       └── edit_subtitle_dialog.py  # 字幕编辑对话框
│   ├── utils/                     # 工具函数
│   │   ├── __init__.py
│   │   └── time_utils.py          # 时间格式转换
│   └── resources/                 # 资源文件
│       ├── icon.png               # 应用图标
│       ├── style.qss              # 暗色主题样式表
│       └── fonts/                 # 字体（HarmonyOS Sans）
├── docs/                          # 文档
│   ├── architecture.md            # 架构文档
│   ├── development.md             # 开发指南
│   ├── README.md                  # 文档导航
│   ├── core/                      # 核心层模块文档
│   │   └── track_config.md        # 轨道配置
│   ├── ui/                        # UI 层模块文档
│   │   └── drag_overlay.md        # 拖放覆盖层
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
- **Phase 3** - 打轴功能（音频波形打轴 + 时间轴列表 + 编辑模式）✅
- **Phase 4** - 翻译面板（翻译卡片 + 字幕导入导出）✅
- **Phase 5** - 打磨收尾（布局持久化 + 打包）

详见 [roadmap.md](prototypes/roadmap.md)

## 技术栈

- **UI 框架**: PySide6 (Qt6)
- **波形图**: pyqtgraph
- **数据处理**: numpy
- **包管理**: uv
- **代码检查**: ruff
- **测试框架**: pytest

## 协议

本项目使用 [MIT 协议](LICENSE)。
