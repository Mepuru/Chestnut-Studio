mod app;
mod audio;
mod decoder;
mod message;
mod player;
mod state;

use app::ChestnutStudio;
use iced::Font;

/// 嵌入 HarmonyOS Sans SC Regular 字体
const HARMONY_OS_SANS: &[u8] =
    include_bytes!("../fonts/HarmonyOS_Sans_SC_Regular.ttf");

/// 嵌入 HarmonyOS Sans SC Bold 字体
const HARMONY_OS_SANS_BOLD: &[u8] =
    include_bytes!("../fonts/HarmonyOS_Sans_SC_Bold.ttf");

fn main() -> iced::Result {
    tracing_subscriber::fmt::init();

    iced::application(ChestnutStudio::title, ChestnutStudio::update, ChestnutStudio::view)
        .subscription(ChestnutStudio::subscription)
        .theme(ChestnutStudio::theme)
        .default_font(Font::with_name("HarmonyOS Sans SC"))
        .font(HARMONY_OS_SANS)
        .font(HARMONY_OS_SANS_BOLD)
        .run_with(ChestnutStudio::new)
}
