use iced::widget::pane_grid;
use serde::{Deserialize, Serialize};

use crate::message::Pane;

/// 应用状态
#[derive(Debug)]
#[allow(dead_code)]
pub struct AppState {
    /// PaneGrid 状态
    pub panes: pane_grid::State<Pane>,
    /// 当前聚焦的面板
    pub focus: Option<pane_grid::Pane>,
    /// 是否最大化
    pub is_maximized: bool,

    /// 项目数据
    pub project: Option<Project>,
    /// 当前帧号
    pub current_frame: u64,
    /// 是否播放中
    pub is_playing: bool,
    /// 状态栏文本
    pub status: String,
}

impl Default for AppState {
    fn default() -> Self {
        // 创建初始面板: 视频
        let (mut panes, first) = pane_grid::State::new(Pane::Video);

        // 在右侧分割出轴卡片 (4:6 比例，左侧40%，右侧60%)
        if let Some((right, split)) =
            panes.split(pane_grid::Axis::Vertical, first, Pane::AxisCards)
        {
            // 设置左右比例为 4:6
            panes.resize(split, 0.4);

            // 左侧下方分割出波形 (视频占60%，波形占40%)
            if let Some((_, split_left)) =
                panes.split(pane_grid::Axis::Horizontal, first, Pane::Waveform)
            {
                panes.resize(split_left, 0.6);
            }

            // 右侧下方分割出翻译区 (轴卡片占55%，翻译区占45%)
            if let Some((_, split_right)) =
                panes.split(pane_grid::Axis::Horizontal, right, Pane::Translation)
            {
                panes.resize(split_right, 0.55);
            }
        }

        Self {
            panes,
            focus: None,
            is_maximized: false,
            project: None,
            current_frame: 0,
            is_playing: false,
            status: String::from("就绪 - 请打开视频文件"),
        }
    }
}

// ── 数据模型 ────────────────────────────────────────────────────────────

/// 轴ID
pub type AxisId = u64;

/// 项目
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub media_path: String,
    pub frame_rate: f64,
    pub total_frames: u64,
    pub axes: Vec<Axis>,
    pub translation_axis_ids: Vec<AxisId>,
}

/// 轴
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Axis {
    pub id: AxisId,
    pub index: usize,
    pub name: String,
    pub axis_type: AxisType,
    pub color: [f32; 4],
    pub locked: bool,
    pub segments: Vec<Segment>,
}

/// 轴类型
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum AxisType {
    Source,
    Target,
    Note,
}

/// 片段
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Segment {
    pub id: u64,
    pub start_frame: u64,
    pub end_frame: u64,
    pub text: String,
}
