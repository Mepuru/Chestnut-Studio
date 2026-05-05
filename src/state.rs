use iced::widget::pane_grid;
use serde::{Deserialize, Serialize};

use crate::message::{LayoutPreset, Pane};

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

    /// 面板可见性
    pub show_video: bool,
    pub show_waveform: bool,
    pub show_axis_cards: bool,
    pub show_translation: bool,

    /// 视图菜单是否展开
    pub view_menu_open: bool,

    /// 项目数据
    pub project: Option<Project>,
    /// 当前帧号
    pub current_frame: u64,
    /// 是否播放中
    pub is_playing: bool,
    /// 状态栏文本
    pub status: String,
}

impl AppState {
    /// 获取当前布局预设
    pub fn current_preset(&self) -> LayoutPreset {
        match (
            self.show_video,
            self.show_waveform,
            self.show_axis_cards,
            self.show_translation,
        ) {
            (true, true, true, true) => LayoutPreset::All,
            (true, true, true, false) => LayoutPreset::Timing,
            (true, false, true, true) => LayoutPreset::Translation,
            (true, false, false, false) => LayoutPreset::VideoOnly,
            _ => LayoutPreset::All, // 自定义布局
        }
    }

    /// 应用预设布局
    pub fn apply_preset(&mut self, preset: LayoutPreset) {
        match preset {
            LayoutPreset::All => {
                self.show_video = true;
                self.show_waveform = true;
                self.show_axis_cards = true;
                self.show_translation = true;
            }
            LayoutPreset::Timing => {
                self.show_video = true;
                self.show_waveform = true;
                self.show_axis_cards = true;
                self.show_translation = false;
            }
            LayoutPreset::Translation => {
                self.show_video = true;
                self.show_waveform = false;
                self.show_axis_cards = true;
                self.show_translation = true;
            }
            LayoutPreset::VideoOnly => {
                self.show_video = true;
                self.show_waveform = false;
                self.show_axis_cards = false;
                self.show_translation = false;
            }
        }
        self.rebuild_panes();
    }

    /// 切换面板可见性
    pub fn toggle_panel(&mut self, pane: Pane) {
        match pane {
            Pane::Video => self.show_video = !self.show_video,
            Pane::Waveform => self.show_waveform = !self.show_waveform,
            Pane::AxisCards => self.show_axis_cards = !self.show_axis_cards,
            Pane::Translation => self.show_translation = !self.show_translation,
        }
        self.rebuild_panes();
    }

    /// 重建面板布局
    fn rebuild_panes(&mut self) {
        let (mut panes, first) = pane_grid::State::new(Pane::Video);

        // 根据可见性决定布局
        let left_panes = [self.show_video.then_some(Pane::Video), self.show_waveform.then_some(Pane::Waveform)]
            .into_iter()
            .flatten()
            .collect::<Vec<_>>();

        let right_panes = [self.show_axis_cards.then_some(Pane::AxisCards), self.show_translation.then_some(Pane::Translation)]
            .into_iter()
            .flatten()
            .collect::<Vec<_>>();

        // 如果左侧有多个面板，需要分割
        if left_panes.len() > 1 {
            if let Some((_, split)) = panes.split(pane_grid::Axis::Horizontal, first, left_panes[1]) {
                panes.resize(split, 0.6);
            }
        }

        // 如果有右侧面板
        if !right_panes.is_empty() {
            // 先分割左右
            if let Some((right, split)) = panes.split(pane_grid::Axis::Vertical, first, right_panes[0]) {
                // 左侧占40%，右侧占60%
                panes.resize(split, 0.4);

                // 如果右侧有多个面板
                if right_panes.len() > 1 {
                    if let Some((_, split_right)) = panes.split(pane_grid::Axis::Horizontal, right, right_panes[1]) {
                        panes.resize(split_right, 0.55);
                    }
                }
            }
        }

        self.panes = panes;
        self.focus = None;
        self.is_maximized = false;
    }
}

impl Default for AppState {
    fn default() -> Self {
        let (mut panes, first) = pane_grid::State::new(Pane::Video);

        // 初始布局: 左右 4:6
        if let Some((right, split)) =
            panes.split(pane_grid::Axis::Vertical, first, Pane::AxisCards)
        {
            panes.resize(split, 0.4);

            // 左侧: 视频60% + 波形40%
            if let Some((_, split_left)) =
                panes.split(pane_grid::Axis::Horizontal, first, Pane::Waveform)
            {
                panes.resize(split_left, 0.6);
            }

            // 右侧: 轴卡片55% + 翻译区45%
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
            show_video: true,
            show_waveform: true,
            show_axis_cards: true,
            show_translation: true,
            view_menu_open: false,
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
