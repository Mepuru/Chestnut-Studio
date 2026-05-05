# Chestnut Studio — AI Agent 指令

## 项目概述

Chestnut Studio 是一个视频打轴与翻译协作平台，使用 Rust + Iced 构建。

## 技术栈

- **GUI**: Iced 0.13 (Elm 架构)
- **视频**: libmpv (待集成)
- **音频**: ffmpeg (待集成)
- **字体**: HarmonyOS Sans SC (嵌入式)

## 代码结构

```
src/
├── main.rs      # 入口，字体加载，iced::application 启动
├── app.rs       # ChestnutStudio 结构体，UI 布局，样式函数
├── message.rs   # Message 枚举，Pane 枚举
└── state.rs     # AppState 结构体，数据模型 (Project/Axis/Segment)
```

## 架构模式

采用 **Elm 架构 (Model-View-Update)**:

- `AppState` = Model (状态)
- `Message` = Msg (消息)
- `update()` = Update (状态更新)
- `view()` = View (UI 渲染)

## 开发约定

1. **面板系统**: 使用 `PaneGrid` 管理可调整大小的面板
2. **字体**: 使用 `FONT` 和 `FONT_BOLD` 常量
3. **颜色**: 使用 `app.rs` 中定义的颜色常量
4. **按钮样式**: 使用 `menu_btn()`、`tool_btn()`、`accent_btn()` 工厂函数

## 阶段一完成事项 (2026-05-05)

- [x] Iced 应用框架搭建
- [x] PaneGrid 模块化布局
- [x] 面板显隐切换
- [x] HarmonyOS Sans 字体嵌入
- [x] 暗色主题 UI
- [x] 菜单栏按钮布局

## 下一阶段：视频播放 (阶段二)

参考 `prototypes/01_video_player.md` 和 `prototypes/prototype.md` 5.1 节。

### 关键任务

1. 集成 `mpv` crate
2. 实现视频加载
3. 嵌入视频到 Iced 窗口
4. 实现播放/暂停控制
5. 实现进度条拖拽
6. 实现时间显示
7. 实现 seek 功能

### 依赖

```toml
mpv = "0.37"
```

### 参考代码

- `DD_KaoRou2/main.py` — 入口结构
- `DD_KaoRou2/utils/main_ui.py` — 播放器部分

## 红线

- 不要修改 `prototypes/` 目录的设计文档（除非用户要求）
- 不要引入新的 GUI 框架
- 保持 Elm 架构的纯粹性

## 运行命令

```bash
cargo run              # 开发运行
cargo build --release  # 生产构建
cargo build            # 检查编译
```
