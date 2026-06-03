# Chestnut Studio

一个简洁的视频笔记工具——边看视频边添加带时间戳的笔记。v2.2.3

```
┌──────────────────────────────────────────────┐
│ Chestnut Studio — example.mp4                │
├──────────────────────┬───────────────────────┤
│                      │  笔记              [3] │
│  视频播放器           │  ─── 轨道1 ──        │
│                      │  [00:12] 你好         │
│                      │  [01:23] 再见         │
│                      │  ─── 轨道3 ──        │
│  ◀◀ ▶ ▶▶ ████●████  │  [00:05] 设置按钮     │
│  🔊 ─── 1.0x 01:23   │                       │
├──────────────────────┴───────────────────────┤
│ [🎨 轨道1] 输入翻译或笔记...         00:12.34 │
│                                     [发送]   │
└──────────────────────────────────────────────┘
```

## 功能

- **🎬 视频播放** — mp4/avi/mkv/mov/flv，播放/暂停、倍速、音量
- **📝 时间戳笔记** — 输入时自动记录视频位置，支持 10 条彩色轨道
- **🎯 10 条轨道** — Ctrl+1~9/0 快速切换，颜色区分，支持自定义取色
- **📋 笔记列表** — 按轨道分组，点击跳转视频位置
- **📖 术语库** — 选中笔记按 M 或右键收录术语
- **💾 导出/导入** — TXT / JSON 格式，含轨道颜色头
- **🎯 拖放打开** — 直接拖入视频文件
- **🔗 ASS+TXT 合并** — 将笔记文本合并到 ASS 字幕时间轴，自动匹配 + 手动处理报告

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

## 快速开始

```bash
# 安装依赖
uv sync

# 运行
uv run python main.py
```

## 构建

提供两种打包后端，输出单文件 exe：

```bash
# 构建全部（PyInstaller + Nuitka）
uv run python scripts/build_release.py

# 仅构建 PyInstaller 版（≈55 MB，构建快）
uv run python scripts/build_release.py pyinstaller

# 仅构建 Nuitka 版（≈33 MB，编译耗时稍长）
uv run python scripts/build_release.py nuitka
```

输出:
```
dist/
├── ChestnutStudio-{version}-PyInstaller.exe   (≈55 MB)
└── ChestnutStudio-{version}-Nuitka.exe        (≈33 MB)
```

| 后端 | 大小 | 原理 | 适用场景 |
|------|------|------|----------|
| PyInstaller | ≈55 MB | 捆绑 Python + DLL | 兼容性优先 |
| Nuitka | ≈33 MB | 编译 Python → 原生 exe | 体积/启动速度优先 |

## 项目结构

```
chestnut_studio/
├── core/                  # 核心逻辑（无 UI 依赖）
│   ├── ass_merge.py       # ASS+TXT 合并引擎
│   ├── ffmpeg.py          # FFmpeg 封装
│   ├── note_manager.py    # 笔记 + 术语数据模型
│   └── track_config.py    # 轨道配置（颜色/数量）
├── ui/                    # UI 组件
│   ├── main_window.py     # 主窗口
│   ├── input_bar.py       # 底部输入栏
│   ├── merge_dialog.py    # ASS+TXT 合并对话框
│   ├── note_panel.py      # 笔记列表面板
│   ├── player_controls.py # 播放控制栏
│   ├── term_dialog.py     # 术语编辑对话框
│   └── cards/
│       └── player_card.py # 视频播放器
├── resources/
│   ├── icons/             # SVG 图标
│   ├── icon.png           # 应用图标
│   └── style.qss          # 深色主题
└── utils/
    ├── log_manager.py     # 日志系统
    ├── time_utils.py      # 时间格式转换
    └── version.py         # 版本号读取
```

## 技术栈

- **Python 3.12+**
- **PySide6** — Qt6 绑定
- **FFmpeg**（可选）— 视频信息解析

## 快捷键

| 按键 | 功能 |
|------|------|
| `F1` | 播放/暂停 |
| `F2` / `←` | 后退 5 秒 |
| `F3` / `→` | 前进 5 秒 |
| `Ctrl+1~9` / `Ctrl+0` | 切换轨道 |
| `Ctrl+O` | 打开视频 |
| `Ctrl+E` | 导出笔记 |
| `Ctrl+I` | 导入笔记 |
| `Ctrl+Q` | 退出 |
| `Enter` | 发送笔记 |
| `Delete` | 删除笔记 |
| `M` | 术语录入 |

## 许可证

MIT
