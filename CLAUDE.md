# Chestnut Studio — AI 开发指南

> 供 AI Agent 在本项目中协作开发时参考

---

## 项目概述

Chestnut Studio 是一款面向字幕组/烤肉组的现代化字幕工具，基于 PySide6 开发。

**当前进度**: Phase 6 完成（可扩展架构重构）

**核心特性**: 
- 音频波形区：用户通过快捷键打轴（标记开始/结束点）
- 时间轴列表：显示已打轴的字幕条（编号 + 起止时间 + 文本）
- 翻译面板：编辑当前轨道的字幕文本，支持快速跳转
- 复制轴功能：将一个轨道的字幕复制到另一个轨道
- ASS 导出：支持多轨道导出，按起始时间排序
- 拖放导入：全局覆盖层，自动识别视频/字幕文件
- 多轨道：最多 8 个轨道，颜色由 track_config.py 集中配置

---

## 核心约定

### 分层架构

```
UI 层 (ui/)          → 依赖核心层和工具层，依赖 PySide6
核心层 (core/)        → 只依赖工具层，不依赖 PySide6（可独立测试）
工具层 (utils/)       → 无外部依赖
```

**红线**: 核心层绝不引入 PySide6 依赖。

### 卡片间通信

- 卡片间通过 **Signal** 通信，不直接引用
- **SignalManager** 负责连接所有信号（声明式 + 中转）
- 卡片通过 `listens_to()` 声明订阅的信号
- 错误做法: `self.player_card._player.setPosition(1000)`
- 正确做法: `self.player_card.position_changed.connect(...)`

---

## 关键路径

| 文件 | 职责 |
|------|------|
| `ui/main_window.py` | 主窗口，初始化和协调 |
| `ui/signal_manager.py` | 信号管理器，集中管理所有信号连接 |
| `ui/layout_config.py` | 布局配置数据类 |
| `ui/layout_engine.py` | 布局应用引擎 |
| `ui/auto_menu.py` | 菜单自动生成 |
| `ui/cards/base_card.py` | BaseCard 基类，生命周期钩子 |
| `ui/cards/registry.py` | 卡片注册表，@register_card 装饰器 |
| `ui/cards/player_card.py` | 视频播放 + AB 循环 |
| `ui/cards/waveform_card.py` | 音频波形显示 + 打轴功能 |
| `ui/cards/timeline_card.py` | 时间轴列表，显示已打轴的字幕 |
| `ui/cards/translate_card.py` | 翻译面板，填写源语言和目标语言 |
| `ui/toolbar.py` | 工具栏按钮 |
| `core/audio.py` | 音频处理函数 |
| `core/ffmpeg.py` | FFmpeg 封装 |
| `core/track_config.py` | 轨道颜色、数量等集中配置（默认 8 轨道） |
| `utils/log_manager.py` | 统一日志管理器，声明式、可扩展的日志系统 |
| `utils/log_decorator.py` | 日志装饰器，声明式方式定义日志源和记录方法调用 |
| `utils/version.py` | 版本号工具，从 pyproject.toml 单源读取 |

---

## 快捷键清单

| 快捷键 | 功能 | 所在文件 |
|--------|------|----------|
| `Space` | 播放/暂停 | `main_window.py` |
| `[` | 设置 AB 循环 A 点 | `main_window.py` |
| `]` | 设置 AB 循环 B 点 | `main_window.py` |
| `\` | 清除 AB 循环 | `main_window.py` |
| `Ctrl+O` | 打开视频 | `menubar.py` |
| `I` | 标记字幕开始点 | `waveform_card.py` |
| `O` | 标记字幕结束点 | `waveform_card.py` |
| `Ctrl+Enter` | 保存翻译并跳转下一条 | `translate_card.py` |
| `Shift+Enter` | 跳转到上一条字幕 | `translate_card.py` |
| `1` `2` `3` `4` | 快速切换轨道 | `main_window.py` |

---

## 信号连接图

```
┌─────────────────────────────────────────────────────────────────┐
│                        SignalManager                            │
│                                                                 │
│  卡片声明 @subscribe / listens_to():                            │
│    WaveformCard ← player.position_changed/duration_changed     │
│                    player.ab_loop_changed                       │
│                    timeline.edit_subtitle_requested             │
│    TimelineCard ← player.duration_changed                      │
│    TranslateCard ← timeline.subtitle_selected                  │
│    PlayerCard ← waveform.position_clicked                      │
│                ← timeline.jump_to_position                     │
│                ← toolbar.play_clicked/rate_changed/ab_loop_*   │
│                                                                 │
│    ToolBar ← player.position_changed/duration_changed          │
│            ← player.playback_state_changed/ab_loop_changed     │
│                                                                 │
│  中转处理 (@relay 装饰器):                                       │
│    player.video_opened → MainWindow._on_video_opened           │
│    player.ab_loop_changed → MainWindow._on_ab_loop_changed     │
│    waveform.subtitle_created → MainWindow._on_subtitle_created │
│    waveform.subtitle_edited → MainWindow._on_subtitle_edited   │
│    timeline.subtitle_selected → MainWindow._on_subtitle_selected│
│    translate.jump_to_next/prev → MainWindow._on_jump_to_*      │
│                                                                 │
│  动态订阅 (状态栏等):                                            │
│    player.position_changed → StatusBar.set_time                │
│    player.duration_changed → StatusBar.set_status              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 测试命令

```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试文件
uv run pytest tests/test_phase2.py -v

# 代码检查
uv run ruff check chestnut_studio/

# 代码格式化
uv run ruff format chestnut_studio/
```

---

## 注意事项

1. **不要修改 prototypes/ 目录** - 这是历史设计文档
2. **docs/ 目录的文档要保持面向外部读者** - 不要写"我记得..."
3. **新增功能要同步更新文档** - 特别是 docs/ui.md 和 docs/core.md
4. **全局快捷键在 MainWindow.keyPressEvent 中处理** - 确保任何卡片获得焦点都能响应
5. **版本号唯一来源是 pyproject.toml** - 改版本只需改 `pyproject.toml` + `uv lock`，不要在代码中硬编码
