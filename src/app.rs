use iced::widget::{
    button, column, container, horizontal_space, image, pane_grid,
    row, text, PaneGrid,
};
use iced::{Center, Color, ContentFit, Element, Fill, Font, Subscription, Theme};
use std::path::PathBuf;
use std::time::Duration;

use crate::message::{Message, Pane};
use crate::player::{self, VideoPlayer};
use crate::state::AppState;

// ── 字体 ────────────────────────────────────────────────────────────

const FONT: Font = Font::with_name("HarmonyOS Sans SC");
const FONT_BOLD: Font = Font {
    family: iced::font::Family::Name("HarmonyOS Sans SC"),
    weight: iced::font::Weight::Bold,
    stretch: iced::font::Stretch::Normal,
    style: iced::font::Style::Normal,
};

// ── 颜色 ────────────────────────────────────────────────────────────

const BG_DARK: Color = Color::from_rgb(0.11, 0.11, 0.12);
const BG_PANEL: Color = Color::from_rgb(0.15, 0.15, 0.17);
const BG_SURFACE: Color = Color::from_rgb(0.18, 0.18, 0.20);
const ACCENT: Color = Color::from_rgb(0.35, 0.55, 0.85);
const ACCENT_HOVER: Color = Color::from_rgb(0.40, 0.62, 0.92);
const TEXT_PRIMARY: Color = Color::from_rgb(0.90, 0.90, 0.92);
const TEXT_SECONDARY: Color = Color::from_rgb(0.55, 0.55, 0.60);
const TEXT_ACTIVE: Color = Color::from_rgb(0.50, 0.75, 1.0);
const BORDER: Color = Color::from_rgb(0.25, 0.25, 0.28);
const TITLE_BAR_BG: Color = Color::from_rgb(0.13, 0.13, 0.15);
const TITLE_BAR_FOCUSED: Color = Color::from_rgb(0.18, 0.25, 0.38);
const DANGER: Color = Color::from_rgb(0.85, 0.35, 0.35);

// ── 应用 ────────────────────────────────────────────────────────────

pub struct ChestnutStudio {
    state: AppState,
}

impl ChestnutStudio {
    pub fn new() -> (Self, iced::Task<Message>) {
        let mut state = AppState::default();
        
        // 尝试初始化播放器
        match VideoPlayer::new() {
            Ok(player) => {
                state.player = Some(player);
                state.status = "播放器已就绪 - 请打开视频文件".into();
                tracing::info!("播放器初始化成功");
            }
            Err(e) => {
                let err_msg = format!("初始化播放器失败: {:#}", e);
                tracing::warn!("{}", err_msg);
                state.status = format!("播放器初始化失败: {}", err_msg);
            }
        }

        (Self { state }, iced::Task::none())
    }

    pub fn title(&self) -> String {
        String::from("Chestnut Studio")
    }

    pub fn update(&mut self, message: Message) -> iced::Task<Message> {
        match message {
            // 面板布局
            Message::PaneClicked(pane) => self.state.focus = Some(pane),
            Message::PaneDragged(pane_grid::DragEvent::Dropped { pane, target }) => {
                self.state.panes.drop(pane, target);
            }
            Message::PaneDragged(_) => {}
            Message::PaneResized(pane_grid::ResizeEvent { split, ratio }) => {
                self.state.panes.resize(split, ratio);
            }
            Message::PaneMaximize(pane) => {
                self.state.panes.maximize(pane);
                self.state.is_maximized = true;
            }
            Message::PaneRestore => {
                self.state.panes.restore();
                self.state.is_maximized = false;
            }
            Message::TogglePanel(pane) => self.state.toggle_panel(pane),

            // 文件操作
            Message::ImportVideo => {
                // 打开文件选择对话框
                return iced::Task::perform(
                    async {
                        rfd::AsyncFileDialog::new()
                            .add_filter("视频文件", &["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv"])
                            .add_filter("所有文件", &["*"])
                            .set_title("选择视频文件")
                            .pick_file()
                            .await
                            .map(|f| PathBuf::from(f.path()))
                    },
                    |path| {
                        if let Some(p) = path {
                            Message::VideoFileOpened(p)
                        } else {
                            Message::ImportVideo // 取消时不做任何事
                        }
                    },
                );
            }
            Message::VideoFileOpened(path) => {
                if let Some(ref mut player) = self.state.player {
                    match player.load_file(&path) {
                        Ok(()) => {
                            self.state.video_path = path.to_str().map(|s| s.to_string());
                            self.state.duration_ms = player.get_duration_ms();
                            self.state.fps = player.get_fps();
                            self.state.current_frame = 0;
                            self.state.position_ms = 0;
                            self.state.is_playing = false;
                            self.state.status = format!("已加载: {}", path.file_name().unwrap_or_default().to_string_lossy());
                            tracing::info!("视频已加载: {:?}", path);
                        }
                        Err(e) => {
                            self.state.status = format!("加载失败: {}", e);
                            tracing::error!("加载视频失败: {}", e);
                        }
                    }
                } else {
                    self.state.status = "播放器未初始化".into();
                }
            }
            Message::ImportSubtitle => self.state.status = "导入字幕 (预留)".into(),
            Message::ExportSubtitle => self.state.status = "导出字幕 (预留)".into(),

            // 播放控制
            Message::TogglePlayPause => {
                if let Some(ref mut player) = self.state.player {
                    if let Err(e) = player.toggle_play_pause() {
                        self.state.status = format!("播放控制失败: {}", e);
                    } else {
                        self.state.is_playing = player.is_playing();
                        self.state.status = if self.state.is_playing { "播放中" } else { "已暂停" }.into();
                    }
                }
            }
            Message::Play => {
                if let Some(ref mut player) = self.state.player {
                    if let Err(e) = player.play() {
                        self.state.status = format!("播放失败: {}", e);
                    } else {
                        self.state.is_playing = true;
                        self.state.status = "播放中".into();
                    }
                }
            }
            Message::Pause => {
                if let Some(ref mut player) = self.state.player {
                    player.pause();
                    self.state.is_playing = false;
                    self.state.status = "已暂停".into();
                }
            }
            Message::SeekTo(frame) => {
                if let Some(ref mut player) = self.state.player {
                    if let Err(e) = player.seek_to_frame(frame) {
                        self.state.status = format!("跳转失败: {}", e);
                    } else {
                        self.state.current_frame = frame;
                        self.state.position_ms = (frame as f64 / self.state.fps * 1000.0) as u64;
                    }
                }
            }
            Message::SeekForward5s => {
                if let Some(ref mut player) = self.state.player {
                    if let Err(e) = player.seek_forward(5.0) {
                        self.state.status = format!("跳转失败: {}", e);
                    } else {
                        self.state.position_ms = player.get_position_ms();
                        self.state.current_frame = player.get_current_frame();
                    }
                }
            }
            Message::SeekBackward5s => {
                if let Some(ref mut player) = self.state.player {
                    if let Err(e) = player.seek_backward(5.0) {
                        self.state.status = format!("跳转失败: {}", e);
                    } else {
                        self.state.position_ms = player.get_position_ms();
                        self.state.current_frame = player.get_current_frame();
                    }
                }
            }
            Message::FrameStep => {
                if let Some(ref mut player) = self.state.player {
                    if let Err(e) = player.frame_step() {
                        self.state.status = format!("步进失败: {}", e);
                    } else {
                        self.state.current_frame = player.get_current_frame();
                        self.state.position_ms = player.get_position_ms();
                    }
                }
            }
            Message::FrameBackStep => {
                if let Some(ref mut player) = self.state.player {
                    if let Err(e) = player.frame_back_step() {
                        self.state.status = format!("步进失败: {}", e);
                    } else {
                        self.state.current_frame = player.get_current_frame();
                        self.state.position_ms = player.get_position_ms();
                    }
                }
            }
            Message::SetVolume(volume) => {
                if let Some(ref mut player) = self.state.player {
                    player.set_volume(volume);
                    self.state.volume = volume;
                }
            }
            Message::ToggleMute => {
                if let Some(ref mut player) = self.state.player {
                    let new_muted = !self.state.is_muted;
                    player.set_mute(new_muted);
                    self.state.is_muted = new_muted;
                }
            }
            Message::SetSpeed(speed) => {
                if let Some(ref mut player) = self.state.player {
                    player.set_speed(speed);
                    self.state.speed = speed;
                }
            }
            Message::Tick => {
                // 定时同步播放状态和更新视频帧
                if let Some(ref player) = self.state.player {
                    if player.is_playing() {
                        self.state.is_playing = true;
                        
                        // 更新视频帧
                        if let Some(frame) = player.current_frame() {
                            // 从帧数据中获取帧号和时间
                            self.state.current_frame = frame.frame_number;
                            self.state.position_ms = (frame.frame_number as f64 / player.get_fps() * 1000.0) as u64;
                            
                            let handle = image::Handle::from_rgba(
                                frame.width,
                                frame.height,
                                frame.data,
                            );
                            self.state.video_frame_handle = Some(handle);
                        }
                    } else {
                        self.state.is_playing = false;
                    }
                }
            }
            Message::UpdateVideoFrame => {
                // 手动更新视频帧（用于seek等操作后）
                if let Some(ref player) = self.state.player {
                    if let Some(frame) = player.current_frame() {
                        let handle = image::Handle::from_rgba(
                            frame.width,
                            frame.height,
                            frame.data,
                        );
                        self.state.video_frame_handle = Some(handle);
                    }
                }
            }
        }
        iced::Task::none()
    }

    pub fn view(&self) -> Element<'_, Message> {
        column![
            self.view_menu_bar(),
            self.view_toolbar(),
            self.view_pane_grid(),
            self.view_status_bar(),
        ]
        .width(Fill)
        .height(Fill)
        .into()
    }

    pub fn subscription(&self) -> Subscription<Message> {
        // 如果正在播放，每 16ms 同步一次状态和更新视频帧 (约 60fps)
        if self.state.is_playing {
            iced::time::every(Duration::from_millis(16))
                .map(|_| Message::Tick)
        } else {
            Subscription::none()
        }
    }

    pub fn theme(&self) -> Theme {
        Theme::Dark
    }

    // ── 菜单栏 ──────────────────────────────────────────────────────

    fn view_menu_bar(&self) -> Element<'_, Message> {
        let panel_btn = |pane: Pane, visible: bool| {
            let label = match pane {
                Pane::Video => "视频",
                Pane::Waveform => "波形",
                Pane::AxisCards => "轴卡片",
                Pane::Translation => "翻译",
            };
            button(
                text(label)
                    .font(if visible { FONT_BOLD } else { FONT })
                    .size(13)
                    .color(if visible { TEXT_ACTIVE } else { TEXT_SECONDARY }),
            )
            .on_press(Message::TogglePanel(pane))
            .padding([6, 12])
            .style(move |_, status| {
                let base = button::Style {
                    background: Some(if visible { Color::from_rgba(0.35, 0.55, 0.85, 0.15) } else { Color::TRANSPARENT }.into()),
                    text_color: if visible { TEXT_ACTIVE } else { TEXT_SECONDARY },
                    border: iced::Border {
                        width: 1.0,
                        color: if visible { Color::from_rgba(0.35, 0.55, 0.85, 0.3) } else { Color::TRANSPARENT },
                        radius: 4.0.into(),
                    },
                    ..Default::default()
                };
                match status {
                    button::Status::Hovered => button::Style {
                        background: Some(BG_SURFACE.into()),
                        border: iced::Border { width: 1.0, color: ACCENT, radius: 4.0.into() },
                        ..base
                    },
                    _ => base,
                }
            })
        };

        container(
            row![
                menu_btn("导入视频").on_press(Message::ImportVideo),
                menu_btn("导入字幕").on_press(Message::ImportSubtitle),
                menu_btn("导出字幕").on_press(Message::ExportSubtitle),
                horizontal_space(),
                panel_btn(Pane::Video, self.state.show_video),
                panel_btn(Pane::Waveform, self.state.show_waveform),
                panel_btn(Pane::AxisCards, self.state.show_axis_cards),
                panel_btn(Pane::Translation, self.state.show_translation),
            ]
            .align_y(Center)
            .spacing(4)
            .padding([4, 8]),
        )
        .width(Fill)
        .style(|_| container::Style {
            background: Some(BG_DARK.into()),
            ..Default::default()
        })
        .into()
    }

    // ── 工具栏 ──────────────────────────────────────────────────────

    fn view_toolbar(&self) -> Element<'_, Message> {
        let time_str = if self.state.duration_ms > 0 {
            format!(
                "{} / {}",
                player::format_time_hms(self.state.position_ms as f64 / 1000.0),
                player::format_time_hms(self.state.duration_ms as f64 / 1000.0)
            )
        } else {
            "00:00:00 / 00:00:00".to_string()
        };

        let frame_str = format!("帧 {}", self.state.current_frame);

        let time_display = container(
            row![
                text(frame_str).font(FONT).size(13).color(TEXT_SECONDARY),
                text(" | ").font(FONT).size(13).color(BORDER),
                text(time_str).font(FONT).size(13).color(TEXT_PRIMARY),
            ]
            .align_y(Center)
            .spacing(4),
        )
        .padding([4, 12])
        .style(|_| container::Style {
            background: Some(BG_SURFACE.into()),
            border: iced::Border { radius: 4.0.into(), ..Default::default() },
            ..Default::default()
        });

        // 音量按钮
        let volume_btn = button(
            text(if self.state.is_muted { "🔇" } else { "🔊" })
                .font(FONT).size(14).color(TEXT_PRIMARY)
        )
        .on_press(Message::ToggleMute)
        .padding([6, 8])
        .style(|_, status| {
            let base = button::Style {
                background: Some(Color::TRANSPARENT.into()),
                text_color: TEXT_PRIMARY,
                border: iced::Border { radius: 4.0.into(), ..Default::default() },
                ..Default::default()
            };
            match status {
                button::Status::Hovered => button::Style { background: Some(BG_SURFACE.into()), ..base },
                _ => base,
            }
        });

        container(
            row![
                time_display,
                horizontal_space(),
                tool_btn("|<").on_press(Message::FrameBackStep),
                tool_btn("<<").on_press(Message::SeekBackward5s),
                button(
                    text(if self.state.is_playing { "⏸" } else { "▶" })
                        .font(FONT_BOLD).size(16).color(Color::WHITE)
                )
                .on_press(Message::TogglePlayPause)
                .padding([8, 20])
                .style(accent_btn),
                tool_btn(">>").on_press(Message::SeekForward5s),
                tool_btn(">|").on_press(Message::FrameStep),
                volume_btn,
            ]
            .align_y(Center)
            .spacing(6)
            .padding([6, 10]),
        )
        .width(Fill)
        .style(|_| container::Style {
            background: Some(BG_DARK.into()),
            ..Default::default()
        })
        .into()
    }

    // ── PaneGrid ────────────────────────────────────────────────────

    fn view_pane_grid(&self) -> Element<'_, Message> {
        // 如果没有可见面板，显示占位提示
        if !self.state.has_visible_panes() {
            return container(
                column![
                    text("请选择要显示的面板").font(FONT_BOLD).size(20).color(TEXT_SECONDARY),
                    text("点击上方菜单栏的 [视频] [波形] [轴卡片] [翻译] 按钮").font(FONT).size(14).color(TEXT_SECONDARY),
                    text("来显示对应的面板").font(FONT).size(14).color(TEXT_SECONDARY),
                ]
                .align_x(Center)
                .spacing(12),
            )
            .center_x(Fill)
            .center_y(Fill)
            .style(|_| container::Style {
                background: Some(BG_PANEL.into()),
                ..Default::default()
            })
            .into();
        }

        let focus = self.state.focus;

        let pane_grid = PaneGrid::new(&self.state.panes, |id, pane, is_maximized| {
            let is_focused = focus == Some(id);

            let close_btn = button(text("x").font(FONT).size(11).color(TEXT_SECONDARY))
                .on_press(Message::TogglePanel(*pane))
                .padding([2, 6])
                .style(|_, status| {
                    let base = button::Style {
                        background: Some(Color::TRANSPARENT.into()),
                        text_color: TEXT_SECONDARY,
                        border: iced::Border { radius: 3.0.into(), ..Default::default() },
                        ..Default::default()
                    };
                    match status {
                        button::Status::Hovered => button::Style {
                            background: Some(DANGER.into()),
                            text_color: Color::WHITE,
                            ..base
                        },
                        _ => base,
                    }
                });

            let maximize_btn = if is_maximized {
                button(text("还原").font(FONT).size(11).color(TEXT_SECONDARY))
                    .on_press(Message::PaneRestore)
                    .padding([2, 6])
                    .style(pane_ctrl_btn)
            } else {
                button(text("最大化").font(FONT).size(11).color(TEXT_SECONDARY))
                    .on_press(Message::PaneMaximize(id))
                    .padding([2, 6])
                    .style(pane_ctrl_btn)
            };

            // 获取面板标题
            let pane_title = if *pane == Pane::Video {
                if let Some(ref path) = self.state.video_path {
                    // 显示视频文件名（截断到20个字符）
                    let filename = std::path::Path::new(path)
                        .file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .to_string();
                    let chars: Vec<char> = filename.chars().collect();
                    if chars.len() > 20 {
                        let truncated: String = chars[..17].iter().collect();
                        format!("{}...", truncated)
                    } else {
                        filename
                    }
                } else {
                    pane.title().to_string()
                }
            } else {
                pane.title().to_string()
            };

            let title_bar = pane_grid::TitleBar::new(
                row![
                    text(pane_title).font(FONT_BOLD).size(13)
                        .color(if is_focused { ACCENT } else { TEXT_PRIMARY }),
                    horizontal_space(),
                    maximize_btn,
                    close_btn,
                ]
                .align_y(Center)
                .spacing(2),
            )
            .padding([6, 10])
            .style(move |_| container::Style {
                background: Some(if is_focused { TITLE_BAR_FOCUSED } else { TITLE_BAR_BG }.into()),
                ..Default::default()
            });

            pane_grid::Content::new(self.view_pane_content(*pane))
                .title_bar(title_bar)
                .style(move |_| container::Style {
                    background: Some(BG_PANEL.into()),
                    border: iced::Border {
                        width: 1.0,
                        color: if is_focused { ACCENT } else { BORDER },
                        ..Default::default()
                    },
                    ..Default::default()
                })
        })
        .width(Fill)
        .height(Fill)
        .spacing(2)
        .on_click(Message::PaneClicked)
        .on_drag(Message::PaneDragged)
        .on_resize(10, Message::PaneResized);

        container(pane_grid)
            .width(Fill)
            .height(Fill)
            .padding(2)
            .style(|_| container::Style {
                background: Some(BG_DARK.into()),
                ..Default::default()
            })
            .into()
    }

    fn view_pane_content(&self, pane: Pane) -> Element<'_, Message> {
        match pane {
            Pane::Video => self.view_video_panel(),
            _ => {
                let (title, sub) = match pane {
                    Pane::Waveform => ("音频波形", "Canvas 绘制波形"),
                    Pane::AxisCards => ("轴卡片列表", "水平滚动卡片容器"),
                    Pane::Translation => ("翻译区 / 术语库", "双轴并排编辑"),
                    Pane::Video => unreachable!(),
                };
                container(
                    column![
                        text(title).font(FONT_BOLD).size(16).color(TEXT_SECONDARY),
                        text(sub).font(FONT).size(12).color(TEXT_SECONDARY),
                    ]
                    .align_x(Center).spacing(8),
                )
                .center_x(Fill).center_y(Fill)
                .style(|_| container::Style {
                    background: Some(Color::from_rgb(0.08, 0.08, 0.10).into()),
                    ..Default::default()
                })
                .into()
            }
        }
    }

    // ── 视频面板 ────────────────────────────────────────────────────

    fn view_video_panel(&self) -> Element<'_, Message> {
        let has_video = self.state.video_path.is_some();

        if has_video {
            // 视频容器 - 显示当前帧
            let video_container: Element<'_, Message> = if let Some(ref handle) = self.state.video_frame_handle {
                // 显示视频帧
                iced::widget::image(handle.clone())
                    .width(Fill)
                    .height(Fill)
                    .content_fit(ContentFit::Contain)
                    .into()
            } else {
                // 没有帧数据时显示加载提示
                container(
                    text("视频加载中...").font(FONT).size(14).color(TEXT_SECONDARY)
                )
                .center_x(Fill)
                .center_y(Fill)
                .into()
            };

            container(video_container)
                .width(Fill)
                .height(Fill)
                .style(|_| container::Style {
                    background: Some(Color::from_rgb(0.08, 0.08, 0.10).into()),
                    border: iced::Border { width: 1.0, color: BORDER, ..Default::default() },
                    ..Default::default()
                })
                .into()
        } else {
            // 没有视频时显示提示
            container(
                column![
                    text("视频播放器").font(FONT_BOLD).size(16).color(TEXT_SECONDARY),
                    text("点击 [导入视频] 按钮打开视频文件").font(FONT).size(12).color(TEXT_SECONDARY),
                    text("支持格式: MP4, MKV, AVI, MOV, WebM").font(FONT).size(11).color(TEXT_SECONDARY),
                ]
                .align_x(Center).spacing(8),
            )
            .center_x(Fill).center_y(Fill)
            .style(|_| container::Style {
                background: Some(Color::from_rgb(0.08, 0.08, 0.10).into()),
                border: iced::Border { width: 1.0, color: BORDER, ..Default::default() },
                ..Default::default()
            })
            .into()
        }
    }

    // ── 状态栏 ──────────────────────────────────────────────────────

    fn view_status_bar(&self) -> Element<'_, Message> {
        container(
            row![
                container(text(" ").size(8)).width(8).height(8)
                    .style(|_| container::Style {
                        background: Some(ACCENT.into()),
                        border: iced::Border { radius: 4.0.into(), ..Default::default() },
                        ..Default::default()
                    }),
                text(&self.state.status).font(FONT).size(12).color(TEXT_SECONDARY),
                horizontal_space(),
                text("Chestnut Studio v0.2.0").font(FONT).size(11).color(TEXT_SECONDARY),
            ]
            .align_y(Center)
            .spacing(6)
            .padding([2, 0]),
        )
        .width(Fill)
        .padding([4, 10])
        .style(|_| container::Style {
            background: Some(BG_DARK.into()),
            ..Default::default()
        })
        .into()
    }
}

// ── 组件工厂 ────────────────────────────────────────────────────────

fn menu_btn(label: &str) -> button::Button<'_, Message> {
    button(text(label).font(FONT).size(13).color(TEXT_PRIMARY))
        .padding([6, 12])
        .style(|_, status| {
            let base = button::Style {
                background: Some(Color::TRANSPARENT.into()),
                text_color: TEXT_PRIMARY,
                border: iced::Border { radius: 4.0.into(), ..Default::default() },
                ..Default::default()
            };
            match status {
                button::Status::Hovered => button::Style { background: Some(BG_SURFACE.into()), ..base },
                button::Status::Pressed => button::Style { background: Some(BORDER.into()), ..base },
                _ => base,
            }
        })
}

fn tool_btn(label: &str) -> button::Button<'_, Message> {
    button(text(label).font(FONT).size(13).color(TEXT_PRIMARY))
        .padding([6, 14])
        .style(|_, status| {
            let base = button::Style {
                background: Some(BG_SURFACE.into()),
                text_color: TEXT_PRIMARY,
                border: iced::Border { width: 1.0, color: BORDER, radius: 6.0.into() },
                ..Default::default()
            };
            match status {
                button::Status::Hovered => button::Style {
                    border: iced::Border { width: 1.0, color: ACCENT, radius: 6.0.into() },
                    ..base
                },
                button::Status::Pressed => button::Style {
                    background: Some(Color::from_rgb(0.20, 0.20, 0.22).into()),
                    ..base
                },
                _ => base,
            }
        })
}

fn accent_btn(_theme: &Theme, status: button::Status) -> button::Style {
    let base = button::Style {
        background: Some(ACCENT.into()),
        text_color: Color::WHITE,
        border: iced::Border { radius: 8.0.into(), ..Default::default() },
        ..Default::default()
    };
    match status {
        button::Status::Hovered => button::Style { background: Some(ACCENT_HOVER.into()), ..base },
        button::Status::Pressed => button::Style { background: Some(Color::from_rgb(0.30, 0.48, 0.75).into()), ..base },
        _ => base,
    }
}

fn pane_ctrl_btn(_theme: &Theme, status: button::Status) -> button::Style {
    let base = button::Style {
        background: Some(Color::TRANSPARENT.into()),
        text_color: TEXT_SECONDARY,
        border: iced::Border { radius: 3.0.into(), ..Default::default() },
        ..Default::default()
    };
    match status {
        button::Status::Hovered => button::Style { background: Some(BG_SURFACE.into()), text_color: TEXT_PRIMARY, ..base },
        _ => base,
    }
}
