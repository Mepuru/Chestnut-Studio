<div align="center">
  <img src="chestnut_studio/resources/icon.png" width="64" alt="Chestnut Studio">

  # Chestnut Studio

  一个简洁的视频笔记工具 —— 边看视频边添加带时间戳的笔记。v2.6.0
</div>

> **布局**: 左侧视频播放 + 播放控制栏 | 右侧笔记列表（按轨道分组）| 底部输入栏（轨道切换 + 时间戳 + 发送）

## 功能

- **🎬 视频播放** — 支持 mp4/avi/mkv/mov/flv 等常见格式，播放/暂停、倍速（0.5x~2.0x）、音量控制
- **📝 时间戳笔记** — 输入时自动记录当前视频位置，按 `Enter` 发送
- **🎯 10 条彩色轨道** — `Ctrl+1~9` / `Ctrl+0` 快速切换，每条轨道独立颜色
- **📋 笔记列表** — 按轨道分组显示，点击跳转视频位置，支持时间/轨道两种排序
- **📖 术语库** — 选中笔记按 `M` 或右键收录术语，支持原文/译文/出处/备注
- **💾 导出/导入** — TXT / JSON 格式，导出包含轨道颜色、视频信息、术语库
- **🎯 拖放打开** — 直接拖入视频文件到窗口
- **🔗 ASS+TXT 合并** — 将笔记 TXT 合并到 ASS 字幕时间轴
- **🌙 深色主题** — 精心调色的深色 UI，护眼舒适
- **📋 日志系统** — 自动日志记录，崩溃自动快照，方便排查问题

## 快速上手

### 1. 打开视频

```
拖放视频到窗口  或  文件 → 打开视频 (Ctrl+O)
```

支持 mp4 / avi / flv / mkv / mov / wmv / mp3 / wav / aac。

### 2. 添加笔记

1. 选择轨道：`Ctrl+1` ~ `Ctrl+9` / `Ctrl+0`（对应轨道 1~10）
2. 在底部输入栏输入笔记内容（视频会自动暂停）
3. 按 `Enter` 发送，时间戳自动记录

> 每条笔记自动绑定当前视频位置，点击列表中的笔记即可跳转回对应时间点。

### 3. 管理笔记

- **跳转** — 在右侧笔记列表中点击任意笔记，视频跳到对应位置
- **编辑** — 双击笔记，内容载入输入框，修改后按 `Enter` 更新
- **删除** — 选中笔记，按 `Delete` 键
- **排序** — 点击笔记列表顶部的排序按钮，切换「按时间」/「按轨道」排序

### 4. 术语库

选中笔记后按 `M` 键或右键 → 术语，即可将笔记中的关键词收录到术语库：

- 支持字段：原文（上下文）、术语、译文、出处、参考资料、备注
- 查看/编辑：菜单栏「术语」按钮，弹出术语表格，支持右键编辑/删除
- 导出笔记时自动附带术语库

### 5. 导出 / 导入

```
Ctrl+E  导出笔记（TXT 或 JSON）
Ctrl+I  导入笔记
```

导出 TXT 格式包含完整文件头：版本号、术语数、视频信息、轨道颜色。导入时自动解析。

## ASS+TXT 字幕合并

通过 **文件 → 导入字幕合并 (ASS+TXT)...** 将导出的笔记 TXT 合并到 ASS 字幕中。

### 工作原理

| 匹配类型 | 处理方式 |
|----------|----------|
| 独占区 1:1 | 自动填入（100% 确定） |
| 重叠区单条 TXT | 按时间就近分配（标记潜在风险） |
| 多条 TXT 冲突 | 归入报告，手动处理 |

合并时自动生成三段式报告（`.report.txt`）：
- **第 1 节** — 待手动处理项
- **第 2 节** — 潜在风险（建议复核）
- **第 3 节** — 已自动匹配（全部可溯源）

输出文件命名：`[YYMMDD]M_源文件.ass` + `[YYMMDD]R_报告.txt`

## 快捷键

| 按键 | 功能 | 说明 |
|------|------|------|
| `F1` | 播放/暂停 | 全局生效 |
| `F2` / `←` | 后退 5 秒 | 全局生效 |
| `F3` / `→` | 前进 5 秒 | 全局生效 |
| `Ctrl+1~9` / `Ctrl+0` | 切换轨道 1~10 | 全局生效 |
| `Ctrl+O` | 打开视频 | |
| `Ctrl+E` | 导出笔记 | |
| `Ctrl+I` | 导入笔记 | |
| `Ctrl+Q` | 退出 | |
| `Enter` | 发送/更新笔记 | 输入框有焦点时 |
| `Delete` | 删除选中笔记 | 笔记列表有焦点时 |
| `M` | 打开术语录入 | 笔记列表有焦点时 |

## 日志与故障排查

应用日志自动写入系统目录，崩溃时无需手动保存：

```
%LOCALAPPDATA%/ChestnutStudio/logs/
├── app.log              # 当前会话日志
├── app.20260604_143000.log  # 历史归档（1MB 自动轮转）
└── crash_20260604_143000.log  # 崩溃快照（自动生成）
```

- 日志超过 1MB 自动轮转，保留最近 10 个归档
- 程序崩溃时自动生成时间戳快照并弹出提示
- 查看日志：菜单 **帮助 → 查看日志**

## 快速开始

```bash
# 安装依赖
uv sync

# 运行
uv run python main.py
```

> 依赖 FFmpeg（可选）：用于在导出时获取视频分辨率、帧率、码率等信息。未安装不影响核心功能。

## 构建

```bash
uv run python scripts/build_release.py
```

构建为目录式 exe（Nuitka --mode=standalone + NSIS 打包），输出到 `dist/ChestnutStudio-{version}-Setup-x86_64_v1.exe`（≈29 MB）。

## 项目结构

```
├── main.py                   # 应用入口
├── pyproject.toml            # 项目配置 + 版本号
├── scripts/
│   └── build_release.py      # Nuitka 构建脚本
├── tests/                    # 219 个测试用例
│   ├── conftest.py
│   ├── test_note_manager.py
│   ├── test_ass_merge.py
│   ├── test_time_utils.py
│   ├── test_log_manager.py
│   ├── test_version.py
│   ├── test_integration.py
│   ├── test_track_config.py
│   ├── test_theme.py
│   ├── test_update_checker.py
│   └── test_resources.py
└── chestnut_studio/
    ├── core/                  # 核心逻辑（零 PySide6 依赖）
    │   ├── model/             # 纯数据类（Note, Term, AssDialogue, MergePlan, VideoInfo）
    │   │   ├── note.py
    │   │   ├── ass_merge.py
    │   │   ├── config.py      # 轨道数量/颜色/NOTE_TYPES 单源
    │   │   └── ffmpeg.py
    │   ├── compute/           # 纯计算函数（无 I/O 无副作用）
    │   │   ├── note_processor.py
    │   │   └── ass_merge_engine.py
    │   ├── io/                # 文件/网络 I/O
    │   │   ├── note_repository.py
    │   │   ├── term_repository.py
    │   │   ├── ass_repository.py
    │   │   └── ass_writer.py
    │   ├── manager/           # 编排器（胶水层）
    │   │   ├── note_manager.py
    │   │   └── ass_merge.py
│   ├── ffmpeg.py          # FFmpeg 封装
    ├── ui/                    # UI 组件（PySide6）
    │   ├── main_window.py     # 主窗口：菜单栏、信号、快捷键、拖放
    │   ├── input_bar.py       # 底部输入栏：轨道切换 + 时间戳
    │   ├── note_panel.py      # 笔记列表：分组、排序、右键菜单
    │   ├── term_dialog.py     # 术语编辑/查看对话框
    │   ├── player_controls.py # 播放控制栏：进度条、音量、倍速
    │   ├── merge_dialog.py    # ASS+TXT 合并对话框
    │   ├── debug_box.py       # 开发者百宝箱
    │   └── cards/
    │       └── player_card.py # QMediaPlayer 视频播放封装
    ├── utils/                 # 工具函数（无第三方依赖）
    │   ├── log_manager.py     # 线程安全日志系统
    │   ├── log_utils.py       # @log_operation 装饰器
    │   ├── theme.py           # 主题引擎（32 token 驱动 QSS）
    │   ├── time_utils.py      # 时间格式转换
    │   ├── update_checker.py  # GitHub 版本更新检查
    │   └── version.py         # 版本号从 pyproject.toml 单源读取
    └── resources/             # 资源文件
        ├── icons/             # SVG 图标（play/pause/音量等）
        ├── icon.png           # 应用图标
        ├── splash.png         # 启动页背景
        └── style.qss          # 深色主题 QSS 模板（{{token}} 占位符）
```

## 技术栈

| 组件 | 用途 |
|------|------|
| **Python 3.12+** | 运行时 |
| **PySide6** | Qt6 绑定（GUI） |
| **FFmpeg**（可选） | 视频信息解析（分辨率/帧率/码率） |
| **Nuitka** | 构建为原生 exe（可选 zig 编译器） |

## 许可证

MIT
