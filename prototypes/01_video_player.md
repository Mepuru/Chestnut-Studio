# 视频播放模块

## 1. 模块概述

视频播放模块负责视频文件的加载、播放、暂停、进度控制、倍速播放等核心播放功能。

## 2. 功能清单

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 视频加载 | 支持本地文件打开、拖拽导入 | P0 |
| 播放/暂停 | 空格键切换播放状态 | P0 |
| 进度控制 | 进度条拖拽、点击跳转 | P0 |
| 倍速播放 | 0.1x ~ 2.0x 可选 | P1 |
| 音量控制 | 音量滑块、静音切换 | P1 |
| 循环播放 | AB区间循环、单次播放 | P2 |
| 视频尺寸 | 滚轮调整视频窗口大小 | P2 |
| 时间显示 | 当前时间/总时长显示 | P0 |
| 逐帧步进 | 前进/后退一帧 | P2 |

## 3. 数据模型

```rust
/// 播放器状态
pub struct PlayerState {
    /// 视频文件路径
    pub video_path: String,
    /// 视频总时长(毫秒)
    pub duration_ms: u64,
    /// 当前播放位置(毫秒)
    pub position_ms: u64,
    /// 当前帧号
    pub current_frame: u64,
    /// 是否正在播放
    pub is_playing: bool,
    /// 播放速率
    pub play_rate: f64,
    /// 音量 (0-100)
    pub volume: u32,
    /// 是否静音
    pub is_muted: bool,
    /// 循环模式
    pub loop_mode: LoopMode,
    /// 视频宽度
    pub video_width: u32,
    /// 视频高度
    pub video_height: u32,
    /// 帧率
    pub fps: f64,
}

/// 循环模式
pub enum LoopMode {
    /// 播放完整视频
    None,
    /// AB区间循环
    Loop { start_ms: u64, end_ms: u64 },
    /// 单次播放区间
    Once { start_ms: u64, end_ms: u64 },
}
```

## 4. 核心交互流程

### 4.1 视频加载流程

```
用户打开文件 → 选择视频文件 → 解析视频信息 → 初始化播放器 → 显示第一帧
                ↓
            拖拽文件 → 验证格式 → 同上
```

### 4.2 播放控制流程

```
Space键/点击播放按钮
    ↓
检查当前播放状态
    ↓
┌─────────────────┬─────────────────┐
│   当前暂停       │   当前播放       │
│   ↓              │   ↓              │
│   开始播放       │   暂停播放       │
│   启动定时器     │   停止定时器     │
└─────────────────┴─────────────────┘
```

### 4.3 进度同步机制

```rust
// 定时器回调 (每16ms ≈ 60fps)
fn on_tick(&mut self) {
    if self.is_playing && !self.is_dragging {
        if let Ok(time) = self.mpv.get_property::<f64>("time-pos") {
            self.current_frame = time_to_frame(time, self.fps);
            self.position_ms = (time * 1000.0) as u64;
        }
    }
}
```

## 5. 消息定义

```rust
pub enum PlayerMessage {
    /// 打开视频文件
    OpenFile(PathBuf),
    /// 切换播放/暂停
    TogglePlayPause,
    /// 只播放(不切换)
    Play,
    /// 只暂停(不切换)
    Pause,
    /// 跳转到指定位置
    SeekTo(u64),
    /// 前进5秒
    SeekForward5s,
    /// 后退5秒
    SeekBackward5s,
    /// 前进一帧
    FrameStep,
    /// 后退一帧
    FrameBackStep,
    /// 设置播放速率
    SetPlayRate(f64),
    /// 设置音量
    SetVolume(u32),
    /// 切换静音
    ToggleMute,
    /// 设置循环模式
    SetLoopMode(LoopMode),
    /// 时间同步Tick
    Tick,
    /// 进度条开始拖拽
    DragStart,
    /// 进度条拖拽中
    DragMove(u64),
    /// 进度条拖拽结束
    DragEnd,
}
```

## 6. 快捷键映射

| 快捷键 | 功能 |
|--------|------|
| Space | 播放/暂停 |
| ← | 后退一行(根据间隔) |
| → | 前进一行(根据间隔) |
| ↑ | 跳转到上一条字幕 |
| ↓ | 跳转到下一条字幕 |
| , | 后退一帧 |
| . | 前进一帧 |

## 7. mpv集成要点

```rust
// mpv关键配置
mpv.set_property("keep-open", true)?;      // 播放结束后保持窗口
mpv.set_property("no-osd", true)?;         // 禁用OSD
mpv.set_property("no-border", true)?;      // 无边框
mpv.set_property("video-sync", "audio")?;  // 音画同步
mpv.set_property("hr-seek", "yes")?;       // 高精度seek

// 精确seek
mpv.command("seek", &[&format!("{:.6}", time_secs), "exact"])?;

// 逐帧步进
mpv.command("frame-step")?;      // 下一帧
mpv.command("frame-back-step")?; // 上一帧
```

## 8. 与原版差异

| 功能 | DD_KaoRou2 (PySide2) | Rust方案 (libmpv) |
|------|---------------------|-------------------|
| 播放器 | QMediaPlayer | libmpv |
| 视频嵌入 | QGraphicsVideoItem | winit窗口嵌入 |
| 帧控制 | 不支持逐帧 | frame-step/frame-back-step |
| 精度 | 毫秒级 | 微秒级 |
| 格式支持 | Qt支持的格式 | mpv全格式支持 |
