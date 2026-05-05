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

/// 预设布局
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LayoutPreset {
    /// 全部面板
    All,
    /// 打轴模式 (隐藏翻译区)
    Timing,
    /// 翻译模式 (隐藏波形)
    Translation,
    /// 仅视频
    VideoOnly,
}

impl LayoutPreset {
    #[allow(dead_code)]
    pub fn label(&self) -> &str {
        match self {
            LayoutPreset::All => "全部面板",
            LayoutPreset::Timing => "打轴模式",
            LayoutPreset::Translation => "翻译模式",
            LayoutPreset::VideoOnly => "仅视频",
        }
    }
}

/// 应用消息
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum Message {
    // ── 面板布局 ──────────────────────────────────────────────────
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

    // ── 视图控制 ──────────────────────────────────────────────────
    /// 切换面板可见性
    TogglePanel(Pane),
    /// 应用预设布局
    ApplyLayout(LayoutPreset),
    /// 切换视图菜单展开/收起
    ToggleViewMenu,

    // ── 播放控制 ──────────────────────────────────────────────────
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

    // ── 文件操作 ──────────────────────────────────────────────────
    /// 打开文件
    OpenFile,
}
