use iced::widget::{
    button, column, container, horizontal_rule, pane_grid, row, text, PaneGrid,
};
use iced::{Center, Element, Fill, Font, Subscription, Theme};

use crate::message::{Message, Pane};
use crate::state::AppState;

/// 中文字体优先列表
const CN_FONT: Font = Font::with_name("Microsoft YaHei");

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

            Message::PaneClose(_pane) => {
                // 主面板不允许关闭
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

        column![
            menu_bar,
            horizontal_rule(1),
            toolbar,
            horizontal_rule(1),
            pane_grid_view,
            horizontal_rule(1),
            status_bar,
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
        container(
            row![
                button(text("文件").font(CN_FONT)).on_press(Message::OpenFile),
                button(text("视图").font(CN_FONT)),
                button(text("工具").font(CN_FONT)),
                button(text("帮助").font(CN_FONT)),
            ]
            .spacing(2)
            .padding(4),
        )
        .width(Fill)
        .into()
    }

    // ── 工具栏 ──────────────────────────────────────────────────────

    fn view_toolbar(&self) -> Element<'_, Message> {
        let time_display = text(format!(
            "帧: {} | {}",
            self.state.current_frame,
            if self.state.is_playing { "▶" } else { "⏸" }
        ))
        .font(CN_FONT);

        container(
            row![
                time_display,
                iced::widget::horizontal_space(),
                button(text("◀帧").font(CN_FONT)).on_press(Message::FrameBackStep),
                button(text("◀5s").font(CN_FONT)).on_press(Message::SeekBackward5s),
                button(
                    text(if self.state.is_playing { "⏸" } else { "▶" }).font(CN_FONT)
                )
                .on_press(Message::TogglePlayPause),
                button(text("5s▶").font(CN_FONT)).on_press(Message::SeekForward5s),
                button(text("帧▶").font(CN_FONT)).on_press(Message::FrameStep),
            ]
            .spacing(6)
            .padding(6)
            .align_y(Center),
        )
        .width(Fill)
        .into()
    }

    // ── PaneGrid ────────────────────────────────────────────────────

    fn view_pane_grid(&self) -> Element<'_, Message> {
        let focus = self.state.focus;

        let pane_grid = PaneGrid::new(&self.state.panes, |id, pane, is_maximized| {
            let is_focused = focus == Some(id);

            let title_bar = pane_grid::TitleBar::new(
                row![
                    text(pane.title()).font(CN_FONT).size(14),
                    iced::widget::horizontal_space(),
                    if is_maximized {
                        button(text("还原").font(CN_FONT).size(12))
                            .on_press(Message::PaneRestore)
                            .padding(2)
                            .style(button::secondary)
                    } else {
                        button(text("最大化").font(CN_FONT).size(12))
                            .on_press(Message::PaneMaximize(id))
                            .padding(2)
                            .style(button::text)
                    }
                ]
                .align_y(Center)
                .spacing(4),
            )
            .padding(6)
            .style(if is_focused {
                title_bar_focused
            } else {
                title_bar_active
            });

            pane_grid::Content::new(self.view_pane_content(*pane, id))
                .title_bar(title_bar)
                .style(if is_focused {
                    pane_focused
                } else {
                    pane_active
                })
        })
        .width(Fill)
        .height(Fill)
        .spacing(4)
        .on_click(Message::PaneClicked)
        .on_drag(Message::PaneDragged)
        .on_resize(10, Message::PaneResized);

        container(pane_grid)
            .width(Fill)
            .height(Fill)
            .padding(4)
            .into()
    }

    /// 渲染面板内容
    fn view_pane_content(
        &self,
        pane: Pane,
        _id: pane_grid::Pane,
    ) -> Element<'_, Message> {
        match pane {
            Pane::Video => self.view_video_pane(),
            Pane::Waveform => self.view_waveform_pane(),
            Pane::AxisCards => self.view_axis_cards_pane(),
            Pane::Translation => self.view_translation_pane(),
        }
    }

    fn view_video_pane(&self) -> Element<'_, Message> {
        container(
            text("视频区域\n(mpv 将嵌入此处)")
                .font(CN_FONT)
                .align_x(Center),
        )
        .center_x(Fill)
        .center_y(Fill)
        .into()
    }

    fn view_waveform_pane(&self) -> Element<'_, Message> {
        container(
            text("音频波形\n(Canvas 绘制)")
                .font(CN_FONT)
                .align_x(Center),
        )
        .center_x(Fill)
        .center_y(Fill)
        .into()
    }

    fn view_axis_cards_pane(&self) -> Element<'_, Message> {
        container(
            text("轴卡片列表\n(水平滚动卡片)")
                .font(CN_FONT)
                .align_x(Center),
        )
        .center_x(Fill)
        .center_y(Fill)
        .into()
    }

    fn view_translation_pane(&self) -> Element<'_, Message> {
        container(
            text("翻译区 / 术语库")
                .font(CN_FONT)
                .align_x(Center),
        )
        .center_x(Fill)
        .center_y(Fill)
        .into()
    }

    // ── 状态栏 ──────────────────────────────────────────────────────

    fn view_status_bar(&self) -> Element<'_, Message> {
        container(text(&self.state.status).font(CN_FONT).size(12))
            .width(Fill)
            .padding([2, 8])
            .into()
    }
}

// ── 面板样式 ────────────────────────────────────────────────────────────

fn title_bar_active(theme: &Theme) -> container::Style {
    let palette = theme.extended_palette();
    container::Style {
        text_color: Some(palette.background.strong.text),
        background: Some(palette.background.strong.color.into()),
        ..Default::default()
    }
}

fn title_bar_focused(theme: &Theme) -> container::Style {
    let palette = theme.extended_palette();
    container::Style {
        text_color: Some(palette.primary.strong.text),
        background: Some(palette.primary.strong.color.into()),
        ..Default::default()
    }
}

fn pane_active(theme: &Theme) -> container::Style {
    let palette = theme.extended_palette();
    container::Style {
        background: Some(palette.background.weak.color.into()),
        border: iced::Border {
            width: 1.0,
            color: palette.background.strong.color,
            ..Default::default()
        }
        .into(),
        ..Default::default()
    }
}

fn pane_focused(theme: &Theme) -> container::Style {
    let palette = theme.extended_palette();
    container::Style {
        background: Some(palette.background.weak.color.into()),
        border: iced::Border {
            width: 2.0,
            color: palette.primary.strong.color,
            ..Default::default()
        }
        .into(),
        ..Default::default()
    }
}
