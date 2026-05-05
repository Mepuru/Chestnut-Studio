# Chestnut Studio 架构设计

## 概述

Chestnut Studio 是一个基于 Rust + Iced 的视频打轴桌面应用，采用 Elm 架构实现。

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Iced Application                     │
├─────────────────────────────────────────────────────────────┤
│  main.rs                                                     │
│  ├── 字体加载 (HarmonyOS Sans SC)                            │
│  └── iced::application 启动                                  │
├─────────────────────────────────────────────────────────────┤
│  app.rs (ChestnutStudio)                                     │
│  ├── update() — 消息处理                                     │
│  ├── view() — UI 渲染                                        │
│  ├── subscription() — 事件订阅                               │
│  └── 样式函数                                                │
├─────────────────────────────────────────────────────────────┤
│  message.rs                                                  │
│  ├── Message 枚举 — 所有应用消息                              │
│  └── Pane 枚举 — 面板标识                                    │
├─────────────────────────────────────────────────────────────┤
│  state.rs                                                    │
│  ├── AppState — 应用状态                                     │
│  └── 数据模型 (Project, Axis, Segment)                       │
├─────────────────────────────────────────────────────────────┤
│  player.rs                                                   │
│  └── VideoPlayer — 视频播放器封装                             │
├─────────────────────────────────────────────────────────────┤
│  decoder.rs                                                  │
│  └── VideoDecoder — ffmpeg 解码器，音视频同步                 │
└─────────────────────────────────────────────────────────────┘
```

## Elm 架构

```
┌─────────────┐     Message     ┌─────────────┐
│    View      │ ──────────────► │   Update    │
│  (UI 渲染)   │                 │ (状态更新)   │
└─────────────┘                 └─────────────┘
       ▲                              │
       │          AppState            │
       └──────────────────────────────┘
```

### Model (状态)

`AppState` 结构体包含所有应用状态：

```rust
pub struct AppState {
    pub panes: pane_grid::State<Pane>,  // 面板布局
    pub focus: Option<pane_grid::Pane>, // 当前聚焦面板
    pub is_maximized: bool,             // 是否最大化
    pub show_video: bool,               // 视频面板可见性
    pub show_waveform: bool,            // 波形面板可见性
    pub show_axis_cards: bool,          // 轴卡片面板可见性
    pub show_translation: bool,         // 翻译面板可见性
    pub project: Option<Project>,       // 项目数据
    pub player: Option<VideoPlayer>,    // 视频播放器
    pub current_frame: u64,             // 当前帧号
    pub position_ms: u64,               // 当前位置(毫秒)
    pub duration_ms: u64,               // 总时长(毫秒)
    pub is_playing: bool,               // 播放状态
    pub volume: u32,                    // 音量
    pub is_muted: bool,                 // 静音状态
    pub speed: f64,                     // 播放速率
    pub fps: f64,                       // 帧率
    pub video_path: Option<String>,     // 视频路径
    pub video_frame_handle: Option<ImageHandle>, // 视频帧
    pub status: String,                 // 状态栏文本
}
```

### Message (消息)

```rust
pub enum Message {
    // 面板布局
    PaneClicked(pane_grid::Pane),
    PaneDragged(pane_grid::DragEvent),
    PaneResized(pane_grid::ResizeEvent),
    PaneMaximize(pane_grid::Pane),
    PaneRestore,
    TogglePanel(Pane),
    
    // 文件操作
    ImportVideo,
    ImportSubtitle,
    ExportSubtitle,
    VideoFileOpened(PathBuf),
    
    // 播放控制
    TogglePlayPause,
    Play,
    Pause,
    SeekTo(u64),
    SeekForward5s,
    SeekBackward5s,
    FrameStep,
    FrameBackStep,
    SetVolume(u32),
    ToggleMute,
    SetSpeed(f64),
    
    // 视频帧更新
    UpdateVideoFrame,
    Tick,
}
```

### Update (更新)

`update()` 方法处理所有消息，更新状态：

```rust
fn update(&mut self, message: Message) -> iced::Task<Message> {
    match message {
        Message::TogglePanel(pane) => self.state.toggle_panel(pane),
        Message::TogglePlayPause => {
            if let Some(ref mut player) = self.state.player {
                player.toggle_play_pause()?;
                self.state.is_playing = player.is_playing();
            }
        },
        Message::Tick => {
            // 同步播放状态和视频帧
        },
        // ...
    }
    iced::Task::none()
}
```

### View (视图)

`view()` 方法渲染 UI：

```rust
fn view(&self) -> Element<'_, Message> {
    column![
        self.view_menu_bar(),    // 菜单栏
        self.view_toolbar(),     // 工具栏
        self.view_pane_grid(),   // 面板网格
        self.view_status_bar(),  // 状态栏
    ].into()
}
```

## 面板系统

使用 Iced 的 `PaneGrid` 组件实现可调整大小的面板布局。

### 面板类型

| 面板 | 用途 | 默认位置 |
|------|------|----------|
| Video | 视频播放器 (16:9) | 左上 |
| Waveform | 音频波形 | 左下 |
| AxisCards | 轴卡片列表 | 右上 |
| Translation | 翻译区 | 右下 |

### 布局比例

```
┌──────────────┬────────────────────┐
│  视频 (16:9)  │  轴卡片 (55%)     │  ← 40% : 60%
│  (60%)       │                    │
├──────────────┤                    │
│  音频波形    │  翻译区 (45%)     │
│  (40%)       │                    │
└──────────────┴────────────────────┘
```

### 面板操作

- **拖拽分割线**: 调整面板比例
- **拖拽标题栏**: 重排面板
- **最大化按钮**: 最大化/还原面板
- **关闭按钮**: 隐藏面板
- **菜单栏按钮**: 切换面板可见性

## 视频播放架构

```
┌─────────────────────────────────────────────────────────┐
│                    VideoPlayer                          │
├─────────────────────────────────────────────────────────┤
│  player.rs                                              │
│  ├── load_file() — 加载视频                             │
│  ├── play() / pause() — 播放控制                        │
│  ├── seek_*() — 跳转控制                                │
│  └── current_frame() — 获取当前帧                       │
├─────────────────────────────────────────────────────────┤
│  decoder.rs                                             │
│  ├── VideoDecoder — 视频解码器                          │
│  ├── video_playback_thread — 视频播放线程               │
│  ├── audio_playback_thread — 音频播放线程               │
│  └── extract_frame() — 提取单帧                         │
└─────────────────────────────────────────────────────────┘
```

### 视频解码流程

1. 使用 `ffmpeg` 解码视频为 RGBA 原始数据
2. 降低分辨率到 640px 宽，提高性能
3. 通过管道传输到 Rust
4. 使用 `iced::widget::image` 显示

### 音频播放流程

1. 使用 `ffmpeg` 解码音频为 f32le 格式
2. 通过管道传输到 Rust
3. 使用 `cpal` 输出到音频设备
4. 音频缓冲区限制避免延迟

### 音视频同步

- 使用独立线程处理音频和视频
- 视频帧率控制使用精确计时
- 音频缓冲区限制避免延迟
- Seek 操作时同时更新音频和视频位置

## 数据模型

```rust
pub struct Project {
    pub media_path: String,
    pub frame_rate: f64,
    pub total_frames: u64,
    pub axes: Vec<Axis>,
    pub translation_axis_ids: Vec<AxisId>,
}

pub struct Axis {
    pub id: AxisId,
    pub index: usize,
    pub name: String,
    pub axis_type: AxisType,
    pub color: [f32; 4],
    pub locked: bool,
    pub segments: Vec<Segment>,
}

pub struct Segment {
    pub id: u64,
    pub start_frame: u64,
    pub end_frame: u64,
    pub text: String,
}
```

## UI 样式系统

### 颜色常量

```rust
const BG_DARK: Color = Color::from_rgb(0.11, 0.11, 0.12);
const BG_PANEL: Color = Color::from_rgb(0.15, 0.15, 0.17);
const ACCENT: Color = Color::from_rgb(0.35, 0.55, 0.85);
const TEXT_PRIMARY: Color = Color::from_rgb(0.90, 0.90, 0.92);
const TEXT_SECONDARY: Color = Color::from_rgb(0.55, 0.55, 0.60);
```

### 按钮样式工厂

- `menu_btn()` — 菜单按钮
- `tool_btn()` — 工具栏按钮
- `accent_btn()` — 强调按钮
- `pane_ctrl_btn()` — 面板控制按钮

## 依赖关系

```toml
[dependencies]
iced = { version = "0.13", features = ["canvas", "wgpu", "multi-window", "lazy", "tokio", "image"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
anyhow = "1"
rfd = "0.15"
tracing = "0.1"
tracing-subscriber = "0.3"
image = "0.25"
cpal = "0.17"
```

## 环境要求

- Rust 2024 Edition (1.80+)
- ffmpeg（需要添加到 PATH）

## 后续集成

### 阶段三：音频波形
- 使用 ffmpeg 提取音频波形数据
- 实现 Canvas 波形绘制
- 实现播放位置红线

### 阶段四：波形打轴
- 实现 Shift+拖拽创建轴
- 实现轴区域可视化
- 实现右键删除轴
