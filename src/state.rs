use serde::{Deserialize, Serialize};

/// Core application state (the "Model" in Elm architecture).
///
/// All mutable state lives here. The view function reads it,
/// and the update function mutates it in response to messages.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct AppState {
    /// Project data (None until a file is loaded)
    pub project: Option<Project>,

    /// Current playback frame number
    pub current_frame: u64,

    /// Whether video is currently playing
    pub is_playing: bool,

    /// Whether the user is dragging in the waveform area
    pub is_dragging: bool,

    /// Whether Shift key is held down
    pub shift_held: bool,

    /// Waveform zoom scale
    pub waveform_scale: f64,

    /// Waveform scroll offset (in seconds)
    pub waveform_offset: f64,

    /// Drag start frame (while dragging)
    pub drag_start_frame: Option<u64>,

    /// Drag end frame (while dragging)
    pub drag_end_frame: Option<u64>,

    /// Status message for the toolbar
    pub status: String,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            project: None,
            current_frame: 0,
            is_playing: false,
            is_dragging: false,
            shift_held: false,
            waveform_scale: 1.0,
            waveform_offset: 0.0,
            drag_start_frame: None,
            drag_end_frame: None,
            status: String::from("就绪 - 请打开视频文件"),
        }
    }
}

// ── Data model ────────────────────────────────────────────────────────────

/// A unique identifier for an axis.
pub type AxisId = u64;

/// A complete project containing media info and all axes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    /// Path to the media file
    pub media_path: String,
    /// Video frame rate (e.g. 23.976, 29.97)
    pub frame_rate: f64,
    /// Total number of frames
    pub total_frames: u64,
    /// All axes in this project
    pub axes: Vec<Axis>,
    /// Axis IDs shown in the translation panel (max 2)
    pub translation_axis_ids: Vec<AxisId>,
}

/// An axis groups related segments together.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Axis {
    pub id: AxisId,
    /// Auto-incrementing display index (1, 2, 3, ...)
    pub index: usize,
    /// Display name, e.g. "轴1"
    pub name: String,
    /// Axis category
    pub axis_type: AxisType,
    /// Display color (stored as RGBA)
    pub color: [f32; 4],
    /// Whether editing is locked
    pub locked: bool,
    /// Ordered segments within this axis
    pub segments: Vec<Segment>,
}

/// Axis category.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum AxisType {
    /// Source language
    Source,
    /// Target (translation) language
    Target,
    /// Notes / annotations
    Note,
}

/// A time-coded text segment within an axis.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Segment {
    pub id: u64,
    /// Start frame (inclusive)
    pub start_frame: u64,
    /// End frame (exclusive); always > start_frame
    pub end_frame: u64,
    /// Text content
    pub text: String,
}
