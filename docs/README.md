# Chestnut Studio 文档

> 项目文档导航中心

---

## 文档结构

```
docs/
├── README.md                    # 文档导航首页（本文件）
├── architecture.md              # 架构文档
├── development.md               # 开发指南
├── performance-optimization.md  # 性能优化方案
├── changelog.md                 # 变更日志
├── core/                        # 核心层模块文档
│   ├── README.md                # 核心层概述
│   ├── ffmpeg.md                # FFmpeg 封装
│   ├── audio.md                 # 音频处理
│   ├── subtitle.md              # 字幕数据结构
│   ├── subtitle_io.md           # 字幕导入导出
│   └── track_config.md          # 轨道配置
├── ui/                          # UI 层模块文档
│   ├── README.md                # UI 层概述
│   ├── main_window.md           # 主窗口
│   ├── toolbar.md               # 工具栏
│   ├── menubar.md               # 菜单栏
│   ├── statusbar.md             # 状态栏
│   ├── drag_overlay.md          # 拖放覆盖层
│   ├── cards/                   # 卡片组件文档
│   │   ├── README.md            # 卡片组件概述
│   │   ├── player_card.md       # 视频播放卡片
│   │   ├── waveform_card.md     # 音频波形卡片
│   │   ├── timeline_card.md     # 时间轴列表卡片
│   │   └── translate_card.md    # 翻译面板卡片
│   └── dialogs/                 # 弹窗文档
│       ├── README.md            # 弹窗概述
│       └── edit_subtitle_dialog.md  # 字幕编辑对话框
└── utils/                       # 工具层模块文档
    ├── README.md                # 工具层概述
    └── time_utils.md            # 时间格式转换
```

---

## 快速导航

### 架构与设计

| 文档 | 说明 |
|------|------|
| [架构文档](architecture.md) | 项目整体架构、模块职责、数据流设计 |
| [开发指南](development.md) | 代码风格、项目结构、提交规范、协作约定 |
| [性能优化与架构改进](performance-optimization.md) | 字幕列表操作卡顿的瓶颈分析、短期修复与长期架构改进方案 |
| [变更日志](changelog.md) | 项目重要变更和里程碑记录 |

### 核心层 (core/)

| 文档 | 说明 |
|------|------|
| [核心层概述](core/README.md) | 核心层整体介绍、依赖关系、设计原则 |
| [FFmpeg 封装](core/ffmpeg.md) | 视频信息解析、音轨提取 |
| [音频处理](core/audio.md) | 波形加载、包络计算、人声增强 |
| [字幕数据结构](core/subtitle.md) | SubtitleEntry 定义、字幕操作、叠轴检测 |
| [字幕导入导出](core/subtitle_io.md) | SRT/ASS/VTT/LRC 格式支持 |
| [轨道配置](core/track_config.md) | 轨道颜色、数量等集中配置 |

### UI 层 (ui/)

| 文档 | 说明 |
|------|------|
| [UI 层概述](ui/README.md) | UI 层整体介绍、依赖关系、设计原则 |
| [主窗口](ui/main_window.md) | MainWindow 布局管理、信号连接、全局快捷键 |
| [信号管理器](ui/signal_manager.md) | SignalManager 声明式信号系统 |
| [工具栏](ui/toolbar.md) | 播放控制、AB 循环、倍速选择 |
| [菜单栏](ui/menubar.md) | 文件/视图/帮助菜单 |
| [状态栏](ui/statusbar.md) | 三段式状态显示 |
| [拖放覆盖层](ui/drag_overlay.md) | 全局文件拖放、类型识别 |

### 卡片组件 (ui/cards/)

| 文档 | 说明 |
|------|------|
| [卡片组件概述](ui/cards/README.md) | 卡片组件整体介绍、基类规范 |
| [视频播放卡片](ui/cards/player_card.md) | 视频渲染、播放控制、AB 循环 |
| [音频波形卡片](ui/cards/waveform_card.md) | 波形显示、打轴操作、缩放平移 |
| [时间轴列表卡片](ui/cards/timeline_card.md) | 字幕列表显示、编辑、锁定 |
| [翻译面板卡片](ui/cards/translate_card.md) | 字幕文本编辑、快速跳转 |

### 弹窗组件 (ui/dialogs/)

| 文档 | 说明 |
|------|------|
| [弹窗概述](ui/dialogs/README.md) | 弹窗组件整体介绍 |
| [字幕编辑对话框](ui/dialogs/edit_subtitle_dialog.md) | 字幕区间编辑 |

### 工具层 (utils/)

| 文档 | 说明 |
|------|------|
| [工具层概述](utils/README.md) | 工具层整体介绍 |
| [时间格式转换](utils/time_utils.md) | 毫秒与各格式互转 |

---

## 文档编写规范

### 文件命名

- 使用小写字母和连字符：`player-card.md`
- 模块文档与代码文件对应：`player_card.py` → `player-card.md`

### 文档结构

每个模块文档应包含：

1. **标题** - 模块名称和简要说明
2. **职责** - 模块的主要功能
3. **接口** - 公有方法、信号、属性
4. **用法示例** - 代码示例
5. **注意事项** - 使用时需要注意的问题

### 更新要求

- 代码变更时同步更新文档
- 新增功能必须补充文档
- 修复 Bug 时更新相关说明
