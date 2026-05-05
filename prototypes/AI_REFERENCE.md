# AI开发参考文件清单

## 概述

本文档列出了AI在开发过程中应参考的文件，按功能模块和开发阶段组织。

## 核心参考文件

### 1. 架构设计

| 文件 | 说明 | 何时参考 |
|------|------|----------|
| `prototype.md` | 完整技术方案 | 开始开发前通读，理解整体架构 |
| `00_overview.md` | MVP总览 | 了解MVP范围和模块关系 |

### 2. 模块设计文档

| 文件 | 说明 | 开发阶段 |
|------|------|----------|
| `01_video_player.md` | 视频播放模块 | 阶段2 |
| `02_waveform_timing.md` | 波形打轴模块 | 阶段4 |
| `03_waveform.md` | 音频波形模块 | 阶段3 |
| `04_axis_cards.md` | 轴卡片模块 | 阶段5 |
| `05_segment_editor.md` | 片段编辑模块 | 阶段6 |
| `06_subtitle_export.md` | 字幕导出模块 | 阶段7 |

### 3. 开发路线

| 文件 | 说明 | 何时参考 |
|------|------|----------|
| `MVP_ROADMAP.md` | 开发路线图 | 每日站会，检查进度 |

---

## 按开发阶段的参考顺序

### 阶段1: 项目基础
```
必读:
├── prototype.md          # 技术栈选型
├── 00_overview.md        # 依赖清单
└── MVP_ROADMAP.md        # 了解整体计划

参考:
└── (无)
```

### 阶段2: 视频播放
```
必读:
├── prototype.md          # 5.1节 mpv集成
├── 01_video_player.md    # 播放器设计
└── 00_overview.md        # 依赖配置

代码参考:
├── DD_KaoRou2/main.py           # 入口结构
└── DD_KaoRou2/utils/main_ui.py  # 播放器部分
```

### 阶段3: 音频波形
```
必读:
├── prototype.md          # 5.2节 音频波形
└── 03_waveform.md        # 波形模块设计

代码参考:
├── DD_KaoRou2/utils/graph.py    # 波形绘制逻辑
└── DD_KaoRou2/utils/AI.py       # getWave函数
```

### 阶段4: 波形打轴
```
必读:
├── prototype.md          # 5.2.2节 打轴交互
└── 02_waveform_timing.md # 打轴模块设计

代码参考:
└── DD_KaoRou2/utils/main_ui.py  # 鼠标事件处理
```

### 阶段5: 轴卡片
```
必读:
├── prototype.md          # 5.4节 轴卡片区域
└── 04_axis_cards.md      # 轴卡片设计

代码参考:
└── DD_KaoRou2/utils/main_ui.py  # 字幕表格部分
```

### 阶段6: 文本编辑
```
必读:
├── prototype.md          # 5.4节 片段编辑
└── 05_segment_editor.md  # 编辑器设计

代码参考:
└── DD_KaoRou2/utils/main_ui.py  # subEdit函数
```

### 阶段7: 字幕导出
```
必读:
└── 06_subtitle_export.md # 导出模块设计

代码参考:
├── DD_KaoRou2/utils/videoDecoder.py  # writeAss函数
└── DD_KaoRou2/utils/subtitle.py      # 导出逻辑
```

### 阶段8: 完善优化
```
必读:
├── 00_overview.md        # 最终检查清单
└── MVP_ROADMAP.md        # 里程碑确认

代码参考:
├── DD_KaoRou2/utils/hotKey.py    # 快捷键定义
└── DD_KaoRou2/utils/setting.py   # 设置页面
```

---

## prototype.md 关键章节速查

| 章节 | 内容 | 页码 |
|------|------|------|
| 2. 技术栈 | Iced + mpv选型 | - |
| 3. 核心数据模型 | Axis/Segment定义 | - |
| 4. 界面布局设计 | 面板划分 | - |
| 5.1 视频播放 | mpv集成细节 | - |
| 5.2 音频波形 | 波形生成和打轴 | - |
| 5.3 帧级表格 | 可选功能 | - |
| 5.4 轴卡片区域 | 卡片列表设计 | - |
| 6. 状态管理 | Elm架构 | - |
| 7. 依赖清单 | Cargo.toml | - |
| 8. 开发路线图 | 阶段划分 | - |

---

## DD_KaoRou2 源码参考

### 入口和框架
```
DD_KaoRou2/
├── main.py               # 应用入口，窗口初始化
├── requirements.txt      # Python依赖
└── utils/
    ├── main_ui.py        # 主窗口，所有核心逻辑
    ├── AI.py             # AI打轴(可跳过)
    ├── graph.py          # 波形绘制
    ├── videoDecoder.py   # 字幕导出和视频压制
    ├── subtitle.py       # 字幕裁剪
    ├── hotKey.py         # 快捷键定义
    ├── setting.py        # 设置页面
    └── anime4k.py        # Anime4K(可跳过)
```

### 关键函数索引

| 文件 | 函数 | 说明 |
|------|------|------|
| main_ui.py | `setPlayer()` | 视频播放器初始化 |
| main_ui.py | `setGraph()` | 波形面板初始化 |
| main_ui.py | `setSubtitle()` | 字幕表格初始化 |
| main_ui.py | `refreshTable()` | 刷新表格显示 |
| main_ui.py | `subEdit()` | 字幕编辑处理 |
| main_ui.py | `popTableMenu()` | 右键菜单 |
| graph.py | `graph_main.plot()` | 波形绘制 |
| videoDecoder.py | `writeAss()` | ASS字幕导出 |
| AI.py | `getWave()` | 波形数据提取 |

---

## Iced框架参考

### 官方示例
- https://github.com/iced-rs/iced/tree/master/examples
- 重点参考: `canvas`, `custom_widget`, `game_of_life`

### 关键API
```rust
// 应用框架
Application::new()
Application::update()
Application::view()
Application::subscription()

// Canvas绑图
canvas::Program
canvas::Frame
canvas::Geometry

// 事件处理
Event::Mouse
Event::Keyboard
```

---

## mpv集成参考

### mpv-rs crate
- https://docs.rs/mpv/latest/mpv/
- 重点参考: `MpvHandler`, `set_property`, `command`

### 关键API
```rust
// 初始化
MpvHandler::new()?
mpv.set_property("wid", window_id)?

// 播放控制
mpv.command("loadfile", &[path])?
mpv.set_property("pause", true)?
mpv.command("seek", &[time, "exact"])?

// 帧控制
mpv.command("frame-step")?
mpv.command("frame-back-step")?

// 时间获取
mpv.get_property::<f64>("time-pos")?
```
