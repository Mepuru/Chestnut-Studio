use iced::widget::pane_grid;
use serde::{Deserialize, Serialize};

use crate::message::Pane;

/// 应用状态
#[derive(Debug)]
#[allow(dead_code)]
pub struct AppState {
    pub panes: pane_grid::State<Pane>,
    pub focus: Option<pane_grid::Pane>,
    pub is_maximized: bool,

    pub show_video: bool,
    pub show_waveform: bool,
    pub show_axis_cards: bool,
    pub show_translation: bool,

    pub project: Option<Project>,
    pub current_frame: u64,
    pub is_playing: bool,
    pub status: String,
}

impl AppState {
    /// 是否有任何面板可见
    pub fn has_visible_panes(&self) -> bool {
        self.show_video || self.show_waveform || self.show_axis_cards || self.show_translation
    }

    pub fn toggle_panel(&mut self, pane: Pane) {
        match pane {
            Pane::Video => self.show_video = !self.show_video,
            Pane::Waveform => self.show_waveform = !self.show_waveform,
            Pane::AxisCards => self.show_axis_cards = !self.show_axis_cards,
            Pane::Translation => self.show_translation = !self.show_translation,
        }
        self.rebuild_panes();
    }

    fn rebuild_panes(&mut self) {
        let left_panes: Vec<Pane> = [
            self.show_video.then_some(Pane::Video),
            self.show_waveform.then_some(Pane::Waveform),
        ]
        .into_iter()
        .flatten()
        .collect();

        let right_panes: Vec<Pane> = [
            self.show_axis_cards.then_some(Pane::AxisCards),
            self.show_translation.then_some(Pane::Translation),
        ]
        .into_iter()
        .flatten()
        .collect();

        let all_panes: Vec<Pane> = left_panes.iter().chain(right_panes.iter()).copied().collect();

        if all_panes.is_empty() {
            let (panes, _) = pane_grid::State::new(Pane::Video);
            self.panes = panes;
            self.focus = None;
            self.is_maximized = false;
            return;
        }

        let (mut panes, first) = pane_grid::State::new(all_panes[0]);

        if !left_panes.is_empty() && !right_panes.is_empty() {
            if let Some((right, split)) =
                panes.split(pane_grid::Axis::Vertical, first, right_panes[0])
            {
                panes.resize(split, 0.4);

                if left_panes.len() > 1 {
                    if let Some((_, s)) = panes.split(pane_grid::Axis::Horizontal, first, left_panes[1]) {
                        panes.resize(s, 0.6);
                    }
                }

                if right_panes.len() > 1 {
                    if let Some((_, s)) = panes.split(pane_grid::Axis::Horizontal, right, right_panes[1]) {
                        panes.resize(s, 0.55);
                    }
                }
            }
        } else if left_panes.len() > 1 {
            if let Some((_, s)) = panes.split(pane_grid::Axis::Horizontal, first, left_panes[1]) {
                panes.resize(s, 0.6);
            }
        } else if right_panes.len() > 1 {
            if let Some((_, s)) = panes.split(pane_grid::Axis::Horizontal, first, right_panes[1]) {
                panes.resize(s, 0.55);
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

        if let Some((right, split)) =
            panes.split(pane_grid::Axis::Vertical, first, Pane::AxisCards)
        {
            panes.resize(split, 0.4);

            if let Some((_, s)) = panes.split(pane_grid::Axis::Horizontal, first, Pane::Waveform) {
                panes.resize(s, 0.6);
            }

            if let Some((_, s)) = panes.split(pane_grid::Axis::Horizontal, right, Pane::Translation) {
                panes.resize(s, 0.55);
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
            project: None,
            current_frame: 0,
            is_playing: false,
            status: String::from("就绪 - 请打开视频文件"),
        }
    }
}

// ── 数据模型 ────────────────────────────────────────────────────────

pub type AxisId = u64;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub media_path: String,
    pub frame_rate: f64,
    pub total_frames: u64,
    pub axes: Vec<Axis>,
    pub translation_axis_ids: Vec<AxisId>,
}

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

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum AxisType {
    Source,
    Target,
    Note,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Segment {
    pub id: u64,
    pub start_frame: u64,
    pub end_frame: u64,
    pub text: String,
}
