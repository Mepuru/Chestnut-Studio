# Chestnut Studio — AI Agent 指令

## 项目概述

Chestnut Studio 是一个视频打轴与翻译协作平台，使用 Rust + Iced 构建。

## 技术栈

- **GUI**: Iced 0.13 (Elm 架构)
- **视频解码**: ffmpeg (命令行)
- **音频播放**: cpal (跨平台)
- **图像显示**: iced::widget::image
- **字体**: HarmonyOS Sans SC (嵌入式)

## 代码结构

```
src/
├── main.rs      # 入口，字体加载，iced::application 启动
├── app.rs       # ChestnutStudio 结构体，UI 布局，样式函数
├── message.rs   # Message 枚举，Pane 枚举
├── state.rs     # AppState 结构体，数据模型
├── player.rs    # VideoPlayer 封装，播放控制
└── decoder.rs   # VideoDecoder，ffmpeg 解码，音视频同步
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

## 阶段二完成事项 (2026-05-05)

- [x] 视频解码器 (decoder.rs)
  - 使用 ffmpeg 命令行解码
  - 支持全格式视频
  - 降低分辨率到 640px 宽提高性能
- [x] 视频播放器 (player.rs)
  - 播放/暂停控制
  - Seek 跳转（快进/后退 5 秒）
  - 逐帧步进
- [x] 音频播放 (cpal)
  - 使用 ffmpeg 解码音频
  - 使用 cpal 输出音频
  - 音视频同步
- [x] 视频帧显示
  - 使用 iced::widget::image
  - RGBA 格式帧数据
- [x] 文件对话框
  - 使用 rfd 库
  - 支持常见视频格式

## 下一阶段：音频波形 (阶段三)

参考 `prototypes/03_waveform.md` 和 `prototypes/prototype.md` 5.2 节。

### 关键任务

1. 使用 ffmpeg 提取音频波形数据
2. 实现 Canvas 波形绘制
3. 实现播放位置红线
4. 实现波形点击跳转

### 依赖

```toml
# 已有依赖，无需新增
```

### 环境要求

- ffmpeg 需要添加到 PATH

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
