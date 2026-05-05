# DD_KaoRou2 重构模块总览 (MVP版本)

## 1. 项目概述

本文档汇总了DD_KaoRou2视频打轴机的**最小可行产品(MVP)**功能模块，用于指导从Python/PySide2到Rust/Iced的技术栈重构。

MVP聚焦于核心打轴功能：**手动波形拖拽打轴**，暂不包含AI自动打轴。

## 2. 技术栈对比

| 组件 | 原版 (DD_KaoRou2) | 目标 (Rust) |
|------|-------------------|-------------|
| 语言 | Python 3 | Rust |
| GUI | PySide2 (Qt5) | Iced |
| 视频播放 | QMediaPlayer | libmpv |
| 音频处理 | ffmpeg | ffmpeg |
| 波形显示 | pyqtgraph | Iced Canvas |
| 打轴方式 | AI自动 (Spleeter) | **手动波形拖拽 (Shift+左键)** |
| 持久化 | 无 | serde + JSON/RON |

## 3. MVP功能范围

### 包含功能 (Must Have)
- [x] 视频播放与帧级控制
- [x] 音频波形显示
- [x] **Shift+左键拖拽打轴**
- [x] 右键删除轴
- [x] 轴卡片列表显示
- [x] 片段文本编辑
- [x] 字幕导出 (ASS/SRT)

### 延伸功能 (Should Have)
- [ ] 撤销/重做
- [ ] 快捷键系统
- [ ] 多轴管理
- [ ] 轴颜色/锁定

### 暂不实现 (Won't Have)
- ~~AI自动打轴~~ (使用手动打轴)
- ~~字幕样式配置~~ (使用默认样式)
- ~~视频压制~~ (后续版本)
- ~~翻译功能~~
- ~~YouTube下载器~~
- ~~Anime4K~~

## 4. 模块清单

| 编号 | 模块 | 文档 | MVP优先级 |
|------|------|------|-----------|
| 01 | 视频播放 | [01_video_player.md](./01_video_player.md) | P0 |
| 02 | 波形打轴 | [02_waveform_timing.md](./02_waveform_timing.md) | P0 |
| 03 | 音频波形 | [03_waveform.md](./03_waveform.md) | P0 |
| 04 | 轴卡片管理 | [04_axis_cards.md](./04_axis_cards.md) | P0 |
| 05 | 片段编辑 | [05_segment_editor.md](./05_segment_editor.md) | P0 |
| 06 | 字幕导出 | [06_subtitle_export.md](./06_subtitle_export.md) | P1 |

## 5. 核心交互流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        MVP核心流程                              │
└─────────────────────────────────────────────────────────────────┘
                                
    打开视频 ─────────► 显示视频 + 加载波形
                            │
                            ▼
                    ┌───────────────┐
                    │  Shift+拖拽   │◄──── 波形区域
                    │  创建新轴     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  轴卡片显示   │◄──── 右侧面板
                    │  片段列表     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  双击编辑文本 │◄──── 片段条目
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  导出字幕     │
                    └───────────────┘
```

## 6. 界面布局

```
┌──────────────────────────────────────────────┐
│  菜单栏 (文件 / 视图 / 帮助)                   │
├──────────────────────────────────────────────┤
│  工具栏 (视频名 | 时间显示 | ◀5s ⏸️ ▶5s)       │
├──────────────────────┬───────────────────────┤
│  左侧面板             │  右侧面板             │
│ ┌──────────────────┐ │  ┌──────────────────┐ │
│ │  视频区域        │ │  │  轴卡片区        │ │
│ │  (嵌入 mpv)      │ │  │  ┌──┬──┬──┬──┐  │ │
│ │                  │ │  │  │轴│轴│轴│轴│  │ │
│ └──────────────────┘ │  │  │1 │2 │3 │4 │  │ │
│ ┌──────────────────┐ │  │  └──┴──┴──┴──┘  │ │
│ │  音频波形        │ │  │                  │ │
│ │  (Shift+拖拽)    │ │  │  点击跳帧        │ │
│ └──────────────────┘ │  │  双击编辑        │ │
└──────────────────────┴───────────────────────┘
```

## 7. 数据模型

```rust
/// 应用状态
pub struct AppState {
    /// 项目数据
    pub project: Option<Project>,
    /// 播放器状态
    pub player: PlayerState,
    /// 轴列表
    pub axes: Vec<Axis>,
    /// 波形数据
    pub waveform: Option<WaveformData>,
    /// 当前帧号
    pub current_frame: u64,
    /// 拖拽状态
    pub drag_state: DragState,
}

/// 轴
pub struct Axis {
    pub id: u64,
    pub index: usize,
    pub name: String,
    pub color: Color,
    pub locked: bool,
    pub segments: Vec<Segment>,
}

/// 片段
pub struct Segment {
    pub id: u64,
    pub start_frame: u64,
    pub end_frame: u64,
    pub text: String,
}

/// 拖拽状态
pub enum DragState {
    None,
    Dragging { start_frame: u64, current_frame: u64 },
}
```

## 8. 消息架构

```rust
pub enum Message {
    // 文件操作
    OpenFile,
    SaveProject,
    LoadProject,
    ExportSubtitle(ExportFormat),
    
    // 播放控制
    TogglePlayPause,
    SeekTo(u64),
    SeekForward5s,
    SeekBackward5s,
    FrameStep,
    FrameBackStep,
    
    // 波形打轴
    WaveformMouseDown { frame: u64 },
    WaveformMouseMove { frame: u64 },
    WaveformMouseUp { frame: u64 },
    WaveformRightClick { frame: u64 },
    
    // 轴管理
    AxisClick { axis_id: u64 },
    AxisRightClick { axis_id: u64, action: AxisAction },
    DeleteAxis { axis_id: u64 },
    
    // 片段编辑
    SegmentClick { axis_id: u64, segment_id: u64 },
    SegmentDoubleClick { axis_id: u64, segment_id: u64 },
    SegmentTextChanged { axis_id: u64, segment_id: u64, text: String },
    
    // 定时器
    Tick,
}
```

## 9. 开发路线图

详见 [MVP_ROADMAP.md](./MVP_ROADMAP.md)

## 10. 依赖清单 (精简版)

```toml
[dependencies]
# GUI
iced = { version = "0.13", features = ["canvas", "wgpu"] }

# 视频
mpv = "0.37"

# 音频处理 (仅用于波形提取)
ffmpeg-next = "7.0"

# 序列化
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# 错误处理
anyhow = "1"

# 日志
tracing = "0.1"
tracing-subscriber = "0.3"
```
