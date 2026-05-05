mod app;
mod message;
mod state;

use app::ChestnutStudio;

fn main() -> iced::Result {
    tracing_subscriber::fmt::init();

    iced::application(ChestnutStudio::title, ChestnutStudio::update, ChestnutStudio::view)
        .subscription(ChestnutStudio::subscription)
        .theme(ChestnutStudio::theme)
        .run_with(ChestnutStudio::new)
}
