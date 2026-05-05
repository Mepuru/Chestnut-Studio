use iced::widget::{
    button, column, container, horizontal_space, pane_grid,
    responsive, row, text, PaneGrid,
};
use iced::{Center, Color, Element, Fill, Font, Subscription, Theme};

use crate::message::{Message, Pane};
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
        (Self { state: AppState::default() }, iced::Task::none())
    }

    pub fn title(&self) -> String {
        String::from("Chestnut Studio")
    }

    pub fn update(&mut self, message: Message) -> iced::Task<Message> {
        match message {
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
            Message::TogglePlayPause => {
                self.state.is_playing = !self.state.is_playing;
                self.state.status = if self.state.is_playing { "播放中" } else { "已暂停" }.into();
            }
            Message::SeekForward5s => self.state.status = "前进 5 秒".into(),
            Message::SeekBackward5s => self.state.status = "后退 5 秒".into(),
            Message::FrameStep => self.state.current_frame = self.state.current_frame.saturating_add(1),
            Message::FrameBackStep => self.state.current_frame = self.state.current_frame.saturating_sub(1),
            Message::OpenFile => self.state.status = "打开文件对话框...".into(),
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
        Subscription::none()
    }

    pub fn theme(&self) -> Theme {
        Theme::Dark
    }

    // ── 菜单栏 ──────────────────────────────────────────────────────

    fn view_menu_bar(&self) -> Element<'_, Message> {
        // 面板切换按钮
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
                        border: iced::Border {
                            width: 1.0,
                            color: ACCENT,
                            radius: 4.0.into(),
                        },
                        ..base
                    },
                    _ => base,
                }
            })
        };

        container(
            row![
                menu_btn("文件").on_press(Message::OpenFile),
                // 分隔符
                container(text(" ").size(1))
                    .width(1)
                    .height(16)
                    .style(|_| container::Style {
                        background: Some(BORDER.into()),
                        ..Default::default()
                    }),
                text("视图:").font(FONT).size(13).color(TEXT_SECONDARY),
                panel_btn(Pane::Video, self.state.show_video),
                panel_btn(Pane::Waveform, self.state.show_waveform),
                panel_btn(Pane::AxisCards, self.state.show_axis_cards),
                panel_btn(Pane::Translation, self.state.show_translation),
                horizontal_space(),
                menu_btn("工具"),
                menu_btn("帮助"),
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
        let time_display = container(
            text(format!(
                "帧 {} | {}",
                self.state.current_frame,
                if self.state.is_playing { "播放中" } else { "已暂停" }
            ))
            .font(FONT)
            .size(13)
            .color(TEXT_PRIMARY),
        )
        .padding([4, 12])
        .style(|_| container::Style {
            background: Some(BG_SURFACE.into()),
            border: iced::Border { radius: 4.0.into(), ..Default::default() },
            ..Default::default()
        });

        container(
            row![
                time_display,
                horizontal_space(),
                tool_btn("|<").on_press(Message::FrameBackStep),
                tool_btn("<<").on_press(Message::SeekBackward5s),
                button(
                    text(if self.state.is_playing { "||" } else { ">" })
                        .font(FONT_BOLD).size(16).color(Color::WHITE)
                )
                .on_press(Message::TogglePlayPause)
                .padding([8, 20])
                .style(accent_btn),
                tool_btn(">>").on_press(Message::SeekForward5s),
                tool_btn(">|").on_press(Message::FrameStep),
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

            let title_bar = pane_grid::TitleBar::new(
                row![
                    text(pane.title()).font(FONT_BOLD).size(13)
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
            Pane::Video => responsive(move |size| {
                let h = size.width * 9.0 / 16.0;
                container(
                    column![
                        text("视频播放器").font(FONT_BOLD).size(16).color(TEXT_SECONDARY),
                        text("mpv 将嵌入此处").font(FONT).size(12).color(TEXT_SECONDARY),
                        text(format!("{}x{}", size.width as u32, h as u32)).font(FONT).size(11).color(TEXT_SECONDARY),
                    ]
                    .align_x(Center).spacing(8),
                )
                .width(Fill).height(h).center_x(Fill).center_y(Fill)
                .style(|_| container::Style {
                    background: Some(Color::from_rgb(0.08, 0.08, 0.10).into()),
                    border: iced::Border { width: 1.0, color: BORDER, ..Default::default() },
                    ..Default::default()
                })
                .into()
            }).into(),
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
                text("Chestnut Studio v0.1.0").font(FONT).size(11).color(TEXT_SECONDARY),
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

// ── 按钮样式 ────────────────────────────────────────────────────────

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
