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
            Pane::Video => "视频播放器",
            Pane::Waveform => "音频波形",
            Pane::AxisCards => "轴卡片列表",
            Pane::Translation => "翻译区",
        }
    }

    pub fn icon(&self) -> &str {
        match self {
            Pane::Video => "\u{e0d0}",       // film
            Pane::Waveform => "\u{e55b}",    // audio-waveform
            Pane::AxisCards => "\u{e156}",   // list
            Pane::Translation => "\u{e0fe}", // languages
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

    // 视图控制
    TogglePanel(Pane),
    ApplyLayout(()),
    ToggleViewMenu,

    // 播放控制
    TogglePlayPause,
    SeekForward5s,
    SeekBackward5s,
    FrameStep,
    FrameBackStep,

    // 文件操作
    OpenFile,
}
