# Chestnut Studio 开发指南

## 环境要求

- Rust 2024 Edition (1.80+)
- Cargo
- Windows/macOS/Linux

## 快速开始

```bash
# 克隆仓库
git clone https://gitee.com/kurikana/chestnut-studio.git
cd chestnut-studio

# 运行
cargo run

# 检查编译
cargo build
```

## 项目结构

```
chestnut-studio/
├── src/
│   ├── main.rs          # 入口，字体加载
│   ├── app.rs           # UI 布局与事件处理
│   ├── message.rs       # 消息枚举
│   └── state.rs         # 应用状态与数据模型
├── fonts/               # 嵌入式字体
│   ├── HarmonyOS_Sans_SC_Regular.ttf
│   ├── HarmonyOS_Sans_SC_Bold.ttf
│   └── lucide.ttf       # 图标字体 (备用)
├── prototypes/          # 设计文档
├── docs/                # 项目文档
├── Cargo.toml           # 依赖配置
└── .cargo/config.toml   # Aliyun 镜像源
```

## 代码规范

### 命名约定

- 结构体: `PascalCase` (如 `AppState`, `ChestnutStudio`)
- 枚举: `PascalCase` (如 `Message`, `Pane`)
- 函数: `snake_case` (如 `view_menu_bar`, `toggle_panel`)
- 常量: `SCREAMING_SNAKE_CASE` (如 `BG_DARK`, `ACCENT`)

### 模块组织

- `app.rs` — UI 相关代码
- `message.rs` — 消息定义
- `state.rs` — 状态和数据模型

### 样式函数

使用工厂函数创建按钮样式：

```rust
fn menu_btn(label: &str) -> button::Button<'_, Message> {
    button(text(label).font(FONT).size(13).color(TEXT_PRIMARY))
        .padding([6, 12])
        .style(|_, status| {
            // 样式定义
        })
}
```

## 添加新功能

### 1. 添加新消息

在 `message.rs` 的 `Message` 枚举中添加新变体：

```rust
pub enum Message {
    // 现有消息...
    NewFeature,
}
```

### 2. 处理消息

在 `app.rs` 的 `update()` 方法中添加处理逻辑：

```rust
fn update(&mut self, message: Message) -> iced::Task<Message> {
    match message {
        // 现有处理...
        Message::NewFeature => {
            // 处理逻辑
        }
    }
    iced::Task::none()
}
```

### 3. 添加 UI 元素

在 `app.rs` 的 `view()` 方法中添加 UI 元素：

```rust
fn view(&self) -> Element<'_, Message> {
    column![
        // 现有元素...
        new_widget(),
    ].into()
}
```

### 4. 添加新面板

在 `message.rs` 的 `Pane` 枚举中添加新变体：

```rust
pub enum Pane {
    Video,
    Waveform,
    AxisCards,
    Translation,
    NewPanel,  // 新面板
}
```

然后在 `state.rs` 中更新 `rebuild_panes()` 方法。

## 调试技巧

### 日志

使用 `tracing` 输出日志：

```rust
tracing::info!("操作完成");
tracing::warn!("警告信息");
tracing::error!("错误信息");
```

### 状态检查

在 `view()` 中显示状态信息：

```rust
text(format!("状态: {:?}", self.state))
    .font(FONT)
    .size(12)
```

## 测试

```bash
# 运行测试
cargo test

# 检查代码风格
cargo clippy

# 格式化代码
cargo fmt
```

## 构建发布

```bash
# Debug 构建
cargo build

# Release 构建
cargo build --release
```

## 常见问题

### 编译错误：字体文件找不到

确保 `fonts/` 目录包含所有字体文件。

### 运行时警告：字体加载失败

某些系统字体可能不存在，这是正常的。应用会使用嵌入的字体。

### 性能问题

- 使用 `cargo build --release` 进行优化构建
- 检查是否有不必要的重绘

## 下一步

参考 `prototypes/MVP_ROADMAP.md` 了解后续开发计划。

当前阶段：**阶段二 - 视频播放**

需要集成 `mpv` crate 实现视频播放功能。
