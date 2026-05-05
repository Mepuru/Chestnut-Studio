/// 面板标识
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Pane {
    /// 视频播放器
    Video,
    /// 音频波形
    Waveform,
    /// 轴卡片列表
    AxisCards,
    /// 翻译区
    Translation,
}

impl Pane {
    /// 面板显示名称
    pub fn title(&self) -> &str {
        match self {
            Pane::Video => "视频播放器",
            Pane::Waveform => "音频波形",
            Pane::AxisCards => "轴卡片列表",
            Pane::Translation => "翻译区",
        }
    }
}

/// 应用消息
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum Message {
    /// 面板被点击
    PaneClicked(iced::widget::pane_grid::Pane),
    /// 面板被拖拽
    PaneDragged(iced::widget::pane_grid::DragEvent),
    /// 面板被调整大小
    PaneResized(iced::widget::pane_grid::ResizeEvent),
    /// 面板最大化/还原
    PaneMaximize(iced::widget::pane_grid::Pane),
    /// 还原面板
    PaneRestore,
    /// 关闭面板
    PaneClose(iced::widget::pane_grid::Pane),

    // 播放控制
    /// 切换播放/暂停
    TogglePlayPause,
    /// 前进5秒
    SeekForward5s,
    /// 后退5秒
    SeekBackward5s,
    /// 帧前进
    FrameStep,
    /// 帧后退
    FrameBackStep,

    // 文件操作
    /// 打开文件
    OpenFile,
}
