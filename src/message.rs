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
    PaneClicked(iced::widget::pane_grid::Pane),
    PaneDragged(iced::widget::pane_grid::DragEvent),
    PaneResized(iced::widget::pane_grid::ResizeEvent),
    PaneMaximize(iced::widget::pane_grid::Pane),
    PaneRestore,
    TogglePanel(Pane),
    TogglePlayPause,
    SeekForward5s,
    SeekBackward5s,
    FrameStep,
    FrameBackStep,
    OpenFile,
}
