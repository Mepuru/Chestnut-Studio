/// Application message types for the Elm architecture.
///
/// All user interactions and system events are represented as messages
/// that flow through the update function.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum Message {
    /// No-op message
    None,

    // ── Window lifecycle ──────────────────────────────────────────────
    /// Window was resized
    WindowResized { width: u32, height: u32 },

    // ── Tick / timer ──────────────────────────────────────────────────
    /// Periodic tick for UI updates (e.g. syncing playback position)
    Tick,

    // ── File operations ───────────────────────────────────────────────
    /// User wants to open a video file
    OpenFile,
    /// A file was selected via dialog
    FileSelected(Option<String>),

    // ── Playback control ──────────────────────────────────────────────
    /// Toggle play / pause
    TogglePlayPause,
    /// Seek forward 5 seconds
    SeekForward5s,
    /// Seek backward 5 seconds
    SeekBackward5s,
    /// Seek to an exact frame
    SeekTo(u64),
    /// Step one frame forward
    FrameStep,
    /// Step one frame backward
    FrameBackStep,

    // ── Keyboard ──────────────────────────────────────────────────────
    /// A key was pressed
    KeyDown(String),
    /// A key was released
    KeyUp(String),
}
