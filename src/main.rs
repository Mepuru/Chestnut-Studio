mod app;
mod message;
mod state;

use app::ChestnutStudio;
use iced::Font;

fn main() -> iced::Result {
    tracing_subscriber::fmt::init();

    iced::application(ChestnutStudio::title, ChestnutStudio::update, ChestnutStudio::view)
        .subscription(ChestnutStudio::subscription)
        .theme(ChestnutStudio::theme)
        .default_font(Font::with_name("Microsoft YaHei"))
        .run_with(ChestnutStudio::new)
}
