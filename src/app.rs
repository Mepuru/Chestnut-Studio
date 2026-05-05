use iced::widget::{button, column, container, horizontal_rule, row, text, vertical_rule};
use iced::{Center, Element, Fill, Subscription, Theme};

use crate::message::Message;
use crate::state::AppState;

/// The main application struct.
///
/// Implements the Elm architecture:
/// - `State` (Model): holds all application state
/// - `update` (Update): handles messages and mutates state
/// - `view` (View): renders the UI from state
/// - `subscription` (Subscription): listens for external events
pub struct ChestnutStudio {
    state: AppState,
}

impl ChestnutStudio {
    /// Create the application with default state.
    pub fn new() -> (Self, iced::Task<Message>) {
        (
            Self {
                state: AppState::default(),
            },
            iced::Task::none(),
        )
    }

    /// Window title.
    pub fn title(&self) -> String {
        String::from("Chestnut Studio")
    }

    // ── Elm Architecture: Update ──────────────────────────────────────

    /// Handle a message and update state accordingly.
    pub fn update(&mut self, message: Message) -> iced::Task<Message> {
        match message {
            Message::None => {}

            Message::Tick => {
                // Placeholder: sync playback position from mpv
            }

            Message::WindowResized { .. } => {
                // Placeholder: handle resize
            }

            Message::OpenFile => {
                // Placeholder: open file dialog
                self.state.status = "打开文件对话框...".into();
            }

            Message::FileSelected(path) => {
                if let Some(p) = path {
                    self.state.status = format!("已加载: {}", p);
                }
            }

            Message::TogglePlayPause => {
                self.state.is_playing = !self.state.is_playing;
                self.state.status = if self.state.is_playing {
                    "播放中".into()
                } else {
                    "已暂停".into()
                };
            }

            Message::SeekForward5s => {
                self.state.status = "前进 5 秒".into();
            }

            Message::SeekBackward5s => {
                self.state.status = "后退 5 秒".into();
            }

            Message::SeekTo(frame) => {
                self.state.current_frame = frame;
            }

            Message::FrameStep => {
                self.state.current_frame = self.state.current_frame.saturating_add(1);
            }

            Message::FrameBackStep => {
                self.state.current_frame = self.state.current_frame.saturating_sub(1);
            }

            Message::KeyDown(key) => {
                if key == "Shift" {
                    self.state.shift_held = true;
                }
            }

            Message::KeyUp(key) => {
                if key == "Shift" {
                    self.state.shift_held = false;
                }
            }
        }

        iced::Task::none()
    }

    // ── Elm Architecture: View ────────────────────────────────────────

    /// Render the UI from the current state.
    pub fn view(&self) -> Element<'_, Message> {
        let menu_bar = self.view_menu_bar();
        let toolbar = self.view_toolbar();
        let main_content = self.view_main_content();

        column![
            menu_bar,
            horizontal_rule(1),
            toolbar,
            horizontal_rule(1),
            main_content,
        ]
        .width(Fill)
        .height(Fill)
        .into()
    }

    // ── Elm Architecture: Subscription ────────────────────────────────

    /// Subscribe to external events (timers, keyboard, etc.).
    pub fn subscription(&self) -> Subscription<Message> {
        // Placeholder: periodic tick for syncing playback position
        // iced::time::every(Duration::from_millis(16)).map(|_| Message::Tick)
        Subscription::none()
    }

    // ── Theme ─────────────────────────────────────────────────────────

    /// Return the application theme.
    pub fn theme(&self) -> Theme {
        Theme::Dark
    }

    // ── Private view helpers ──────────────────────────────────────────

    /// Render the menu bar.
    fn view_menu_bar(&self) -> Element<'_, Message> {
        let file_menu = button("文件").on_press(Message::OpenFile);
        let view_menu = button("视图");
        let tools_menu = button("工具");
        let help_menu = button("帮助");

        container(
            row![file_menu, view_menu, tools_menu, help_menu]
                .spacing(4)
                .padding(4),
        )
        .width(Fill)
        .into()
    }

    /// Render the toolbar with playback controls and time display.
    fn view_toolbar(&self) -> Element<'_, Message> {
        let time_display = text(format!(
            "帧: {} | {}",
            self.state.current_frame,
            if self.state.is_playing { "▶" } else { "⏸" }
        ));

        let btn_back = button("◀5s").on_press(Message::SeekBackward5s);
        let btn_play = button(if self.state.is_playing { "⏸" } else { "▶" })
            .on_press(Message::TogglePlayPause);
        let btn_fwd = button("5s▶").on_press(Message::SeekForward5s);
        let btn_frame_back = button("◀帧").on_press(Message::FrameBackStep);
        let btn_frame_fwd = button("帧▶").on_press(Message::FrameStep);

        container(
            row![
                time_display,
                iced::widget::horizontal_space(),
                btn_frame_back,
                btn_back,
                btn_play,
                btn_fwd,
                btn_frame_fwd,
            ]
            .spacing(8)
            .padding(4)
            .align_y(Center),
        )
        .width(Fill)
        .into()
    }

    /// Render the main content area (left + right panels).
    fn view_main_content(&self) -> Element<'_, Message> {
        let left_panel = self.view_left_panel();
        let right_panel = self.view_right_panel();

        row![
            left_panel,
            vertical_rule(1),
            right_panel,
        ]
        .width(Fill)
        .height(Fill)
        .into()
    }

    /// Render the left panel (video + waveform placeholder).
    fn view_left_panel(&self) -> Element<'_, Message> {
        let video_area = container(
            text("视频区域 (mpv 将嵌入此处)")
                .align_x(Center),
        )
        .width(Fill)
        .height(Fill)
        .center_x(Fill)
        .center_y(Fill)
        .style(container::rounded_box);

        let waveform_area = container(
            text("音频波形区域 (Canvas 绘制)")
                .align_x(Center),
        )
        .width(Fill)
        .height(Fill)
        .center_x(Fill)
        .center_y(Fill)
        .style(container::rounded_box);

        column![video_area, waveform_area]
            .width(Fill)
            .height(Fill)
            .spacing(4)
            .padding(4)
            .into()
    }

    /// Render the right panel (axis cards + translation area placeholder).
    fn view_right_panel(&self) -> Element<'_, Message> {
        let axis_cards = container(
            text("轴卡片区\n(水平滚动，显示各轴片段)")
                .align_x(Center),
        )
        .width(Fill)
        .height(Fill)
        .center_x(Fill)
        .center_y(Fill)
        .style(container::rounded_box);

        let translation_area = container(
            text("翻译区 / 术语库")
                .align_x(Center),
        )
        .width(Fill)
        .height(Fill)
        .center_x(Fill)
        .center_y(Fill)
        .style(container::rounded_box);

        // Status bar at the bottom
        let status_bar = container(text(&self.state.status).size(12))
            .width(Fill)
            .padding(4);

        column![axis_cards, translation_area, status_bar]
            .width(Fill)
            .height(Fill)
            .spacing(4)
            .padding(4)
            .into()
    }
}
