use std::path::PathBuf;

/// 面板标识
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Pane {
    Video,
    Waveform,
    AxisCards,
    Translation,
}

impl Pane {
    pub fn title(&self) -> &str {
        match self {
            Pane::Video => "视频",
            Pane::Waveform => "波形",
            Pane::AxisCards => "轴卡片",
            Pane::Translation => "翻译",
        }
    }
}

/// 应用消息
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum Message {
    // 面板布局
    PaneClicked(iced::widget::pane_grid::Pane),
    PaneDragged(iced::widget::pane_grid::DragEvent),
    PaneResized(iced::widget::pane_grid::ResizeEvent),
    PaneMaximize(iced::widget::pane_grid::Pane),
    PaneRestore,
    TogglePanel(Pane),

    // 文件操作
    ImportVideo,
    ImportSubtitle,
    ExportSubtitle,
    VideoFileOpened(PathBuf),

    // 视频窗口初始化
    InitializeVideoWindow,
    VideoWindowCreated(i64),

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

    // 定时同步
    Tick,
}
