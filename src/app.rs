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
const ICON: Font = Font::with_name("lucide");

// ── Lucide 图标 ─────────────────────────────────────────────────────

const ICON_PLAY: &str = "\u{e13c}";
const ICON_PAUSE: &str = "\u{e12e}";
const ICON_SKIP_BACK: &str = "\u{e15f}";
const ICON_SKIP_FORWARD: &str = "\u{e160}";
const ICON_REWIND: &str = "\u{e147}";
const ICON_FAST_FORWARD: &str = "\u{e0bd}";
const ICON_FILM: &str = "\u{e0d0}";
const ICON_AUDIO: &str = "\u{e55b}";
const ICON_LIST: &str = "\u{e156}";
const ICON_LANG: &str = "\u{e0fe}";
const ICON_EYE: &str = "\u{e0ba}";
#[allow(dead_code)]
const ICON_EYE_OFF: &str = "\u{e0bb}";
const ICON_FILE: &str = "\u{e0c0}";
const ICON_CHECK: &str = "\u{e06c}";
const ICON_MAXIMIZE: &str = "\u{e112}";
const ICON_MINIMIZE: &str = "\u{e11b}";

// ── 颜色常量 ────────────────────────────────────────────────────────

const BG_DARK: Color = Color::from_rgb(0.11, 0.11, 0.12);
const BG_PANEL: Color = Color::from_rgb(0.15, 0.15, 0.17);
const BG_SURFACE: Color = Color::from_rgb(0.18, 0.18, 0.20);
const BG_DROPDOWN: Color = Color::from_rgb(0.16, 0.16, 0.18);
const ACCENT: Color = Color::from_rgb(0.35, 0.55, 0.85);
const ACCENT_HOVER: Color = Color::from_rgb(0.40, 0.62, 0.92);
const TEXT_PRIMARY: Color = Color::from_rgb(0.90, 0.90, 0.92);
const TEXT_SECONDARY: Color = Color::from_rgb(0.55, 0.55, 0.60);
const BORDER: Color = Color::from_rgb(0.25, 0.25, 0.28);
const TITLE_BAR_BG: Color = Color::from_rgb(0.13, 0.13, 0.15);
const TITLE_BAR_FOCUSED: Color = Color::from_rgb(0.18, 0.25, 0.38);
#[allow(dead_code)]
const CHECKBOX_ON: Color = Color::from_rgb(0.35, 0.55, 0.85);
#[allow(dead_code)]
const CHECKBOX_OFF: Color = Color::from_rgb(0.35, 0.35, 0.38);
#[allow(dead_code)]
const SHADOW: Color = Color::from_rgba(0.0, 0.0, 0.0, 0.3);

// ── 应用 ────────────────────────────────────────────────────────────

pub struct ChestnutStudio {
    state: AppState,
}

impl ChestnutStudio {
    pub fn new() -> (Self, iced::Task<Message>) {
        (
            Self {
                state: AppState::default(),
            },
            iced::Task::none(),
        )
    }

    pub fn title(&self) -> String {
        String::from("Chestnut Studio")
    }

    // ── Update ──────────────────────────────────────────────────────

    pub fn update(&mut self, message: Message) -> iced::Task<Message> {
        match message {
            Message::PaneClicked(pane) => {
                self.state.focus = Some(pane);
                self.state.view_menu_open = false;
            }
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
            Message::TogglePanel(pane) => {
                self.state.toggle_panel(pane);
            }
            Message::ApplyLayout(_) => {}
            Message::ToggleViewMenu => {
                self.state.view_menu_open = !self.state.view_menu_open;
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
            Message::FrameStep => {
                self.state.current_frame = self.state.current_frame.saturating_add(1);
            }
            Message::FrameBackStep => {
                self.state.current_frame = self.state.current_frame.saturating_sub(1);
            }
            Message::OpenFile => {
                self.state.status = "打开文件对话框...".into();
            }
        }
        iced::Task::none()
    }

    // ── View ────────────────────────────────────────────────────────

    pub fn view(&self) -> Element<'_, Message> {
        let menu_bar = self.view_menu_bar();
        let toolbar = self.view_toolbar();
        let pane_grid_view = self.view_pane_grid();
        let status_bar = self.view_status_bar();

        if self.state.view_menu_open {
            let dropdown = self.view_dropdown_overlay();
            column![menu_bar, dropdown, toolbar, pane_grid_view, status_bar,]
                .width(Fill)
                .height(Fill)
                .into()
        } else {
            column![menu_bar, toolbar, pane_grid_view, status_bar,]
                .width(Fill)
                .height(Fill)
                .into()
        }
    }

    pub fn subscription(&self) -> Subscription<Message> {
        Subscription::none()
    }

    pub fn theme(&self) -> Theme {
        Theme::Dark
    }

    // ── 菜单栏 ──────────────────────────────────────────────────────

    fn view_menu_bar(&self) -> Element<'_, Message> {
        let view_btn = button(
            row![
                icon(ICON_EYE, 14),
                text("视图").font(FONT).size(13),
            ]
            .spacing(4)
            .align_y(Center)
        )
        .on_press(Message::ToggleViewMenu)
        .padding([6, 10])
        .style(|_, s| menu_btn_style(s, false));

        container(
            row![
                icon_btn(ICON_FILE, 14).on_press(Message::OpenFile),
                view_btn,
                icon_btn_placeholder(),
                icon_btn_placeholder(),
            ]
            .align_y(Center)
            .spacing(2)
            .padding([4, 8]),
        )
        .width(Fill)
        .style(|_| container::Style {
            background: Some(BG_DARK.into()),
            ..Default::default()
        })
        .into()
    }

    // ── 下拉菜单 overlay ────────────────────────────────────────────

    fn view_dropdown_overlay(&self) -> Element<'_, Message> {
        container(
            column![
                view_toggle_item(ICON_FILM, "视频播放器", Pane::Video, self.state.show_video),
                view_toggle_item(ICON_AUDIO, "音频波形", Pane::Waveform, self.state.show_waveform),
                view_toggle_item(ICON_LIST, "轴卡片列表", Pane::AxisCards, self.state.show_axis_cards),
                view_toggle_item(ICON_LANG, "翻译区", Pane::Translation, self.state.show_translation),
            ]
            .spacing(1)
            .padding(4)
            .width(180),
        )
        .style(|_| container::Style {
            background: Some(BG_DROPDOWN.into()),
            border: iced::Border {
                width: 1.0,
                color: BORDER,
                radius: 6.0.into(),
            },
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
            border: iced::Border {
                radius: 4.0.into(),
                ..Default::default()
            },
            ..Default::default()
        });

        let play_icon = if self.state.is_playing { ICON_PAUSE } else { ICON_PLAY };

        container(
            row![
                time_display,
                horizontal_space(),
                tool_icon_btn(ICON_SKIP_BACK).on_press(Message::FrameBackStep),
                tool_icon_btn(ICON_REWIND).on_press(Message::SeekBackward5s),
                button(icon_text(play_icon, 18, Color::WHITE))
                    .on_press(Message::TogglePlayPause)
                    .padding([8, 16])
                    .style(accent_btn_style),
                tool_icon_btn(ICON_FAST_FORWARD).on_press(Message::SeekForward5s),
                tool_icon_btn(ICON_SKIP_FORWARD).on_press(Message::FrameStep),
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

        let pane_grid =
            PaneGrid::new(&self.state.panes, |id, pane, is_maximized| {
                let is_focused = focus == Some(id);

                let maximize_icon = if is_maximized { ICON_MINIMIZE } else { ICON_MAXIMIZE };
                let maximize_msg = if is_maximized { Message::PaneRestore } else { Message::PaneMaximize(id) };

                let title_bar = pane_grid::TitleBar::new(
                    row![
                        icon_text(pane.icon(), 13, if is_focused { ACCENT } else { TEXT_SECONDARY }),
                        text(pane.title())
                            .font(FONT_BOLD)
                            .size(13)
                            .color(if is_focused { ACCENT } else { TEXT_PRIMARY }),
                        horizontal_space(),
                        button(icon_text(maximize_icon, 12, TEXT_SECONDARY))
                            .on_press(maximize_msg)
                            .padding([3, 6])
                            .style(pane_ctrl_btn_style),
                    ]
                    .align_y(Center)
                    .spacing(6),
                )
                .padding([6, 10])
                .style(move |_| container::Style {
                    background: Some(
                        if is_focused { TITLE_BAR_FOCUSED } else { TITLE_BAR_BG }.into(),
                    ),
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
            Pane::Video => {
                responsive(move |size| {
                    let w = size.width;
                    let h = w * 9.0 / 16.0;
                    container(
                        column![
                            icon_text(ICON_FILM, 32, TEXT_SECONDARY),
                            text("视频播放器").font(FONT_BOLD).size(14).color(TEXT_SECONDARY),
                            text(format!("{}x{}", w as u32, h as u32))
                                .font(FONT).size(11).color(TEXT_SECONDARY),
                        ]
                        .align_x(Center)
                        .spacing(8),
                    )
                    .width(Fill)
                    .height(h)
                    .center_x(Fill)
                    .center_y(Fill)
                    .style(|_| container::Style {
                        background: Some(Color::from_rgb(0.08, 0.08, 0.10).into()),
                        border: iced::Border { width: 1.0, color: BORDER, ..Default::default() },
                        ..Default::default()
                    })
                    .into()
                })
                .into()
            }
            _ => {
                let (icon, title) = match pane {
                    Pane::Waveform => (ICON_AUDIO, "音频波形"),
                    Pane::AxisCards => (ICON_LIST, "轴卡片列表"),
                    Pane::Translation => (ICON_LANG, "翻译区 / 术语库"),
                    Pane::Video => unreachable!(),
                };
                container(
                    column![
                        icon_text(icon, 32, TEXT_SECONDARY),
                        text(title).font(FONT_BOLD).size(14).color(TEXT_SECONDARY),
                    ]
                    .align_x(Center)
                    .spacing(8),
                )
                .center_x(Fill)
                .center_y(Fill)
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
                container(text(" ").size(8))
                    .width(8).height(8)
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

// ── 图标辅助 ────────────────────────────────────────────────────────

fn icon(unicode: &str, size: u16) -> iced::widget::Text<'_> {
    text(unicode).font(ICON).size(size)
}

fn icon_text(unicode: &str, size: u16, color: Color) -> iced::widget::Text<'_> {
    text(unicode).font(ICON).size(size).color(color)
}

fn icon_btn(unicode: &str, size: u16) -> button::Button<'_, Message> {
    button(icon_text(unicode, size, TEXT_PRIMARY))
        .padding([6, 10])
        .style(|_, s| menu_btn_style(s, false))
}

fn icon_btn_placeholder() -> button::Button<'static, Message> {
    button(text(" ").font(FONT).size(13))
        .padding([6, 10])
        .style(|_, _| button::Style {
            background: Some(Color::TRANSPARENT.into()),
            ..Default::default()
        })
}

fn tool_icon_btn(unicode: &str) -> button::Button<'_, Message> {
    button(icon_text(unicode, 16, TEXT_PRIMARY))
        .padding([6, 12])
        .style(|_, s| tool_btn_style(s))
}

// ── 样式函数 ────────────────────────────────────────────────────────

fn menu_btn_style(status: button::Status, active: bool) -> button::Style {
    let base = button::Style {
        background: Some(if active { BG_SURFACE } else { Color::TRANSPARENT }.into()),
        text_color: if active { ACCENT } else { TEXT_PRIMARY },
        border: iced::Border { radius: 4.0.into(), ..Default::default() },
        ..Default::default()
    };
    match status {
        button::Status::Hovered => button::Style {
            background: Some(BG_SURFACE.into()),
            ..base
        },
        _ => base,
    }
}

fn tool_btn_style(status: button::Status) -> button::Style {
    let base = button::Style {
        background: Some(BG_SURFACE.into()),
        text_color: TEXT_PRIMARY,
        border: iced::Border { width: 1.0, color: BORDER, radius: 6.0.into() },
        ..Default::default()
    };
    match status {
        button::Status::Hovered => button::Style {
            background: Some(BORDER.into()),
            border: iced::Border { width: 1.0, color: ACCENT, radius: 6.0.into() },
            ..base
        },
        button::Status::Pressed => button::Style {
            background: Some(Color::from_rgb(0.20, 0.20, 0.22).into()),
            ..base
        },
        _ => base,
    }
}

fn accent_btn_style(_theme: &Theme, status: button::Status) -> button::Style {
    let base = button::Style {
        background: Some(ACCENT.into()),
        text_color: Color::WHITE,
        border: iced::Border { radius: 8.0.into(), ..Default::default() },
        ..Default::default()
    };
    match status {
        button::Status::Hovered => button::Style { background: Some(ACCENT_HOVER.into()), ..base },
        button::Status::Pressed => button::Style {
            background: Some(Color::from_rgb(0.30, 0.48, 0.75).into()),
            ..base
        },
        _ => base,
    }
}

fn pane_ctrl_btn_style(_theme: &Theme, status: button::Status) -> button::Style {
    let base = button::Style {
        background: Some(Color::TRANSPARENT.into()),
        text_color: TEXT_SECONDARY,
        border: iced::Border { radius: 3.0.into(), ..Default::default() },
        ..Default::default()
    };
    match status {
        button::Status::Hovered => button::Style {
            background: Some(BG_SURFACE.into()),
            text_color: TEXT_PRIMARY,
            ..base
        },
        _ => base,
    }
}

fn view_toggle_item<'a>(icon: &'a str, label: &'a str, pane: Pane, visible: bool) -> button::Button<'a, Message> {
    let check_icon = if visible { ICON_CHECK } else { " " };
    let check_font = if visible { ICON } else { FONT };
    let check_color = if visible { ACCENT } else { Color::TRANSPARENT };

    button(
        row![
            text(check_icon).font(check_font).size(13).color(check_color),
            icon_text(icon, 14, TEXT_SECONDARY),
            text(label).font(FONT).size(13).color(TEXT_PRIMARY),
        ]
        .spacing(8)
        .align_y(Center)
    )
    .on_press(Message::TogglePanel(pane))
    .width(Fill)
    .padding([6, 10])
    .style(|_, s| menu_btn_style(s, false))
}
