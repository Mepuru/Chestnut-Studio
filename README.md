# Chestnut Studio

视频打轴与翻译协作平台 — 基于 Rust + Iced 的原生桌面应用。

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| GUI | Iced 0.13 | Elm 架构原生 GUI |
| 视频 | libmpv (TODO) | 帧级精确控制 |
| 音频 | ffmpeg (TODO) | 波形提取 |
| 字体 | HarmonyOS Sans SC | 嵌入式中文支持 |
| 语言 | Rust 2024 Edition | 零开销抽象 |

## 快速开始

```bash
# 克隆仓库
git clone https://gitee.com/kurikana/chestnut-studio.git
cd chestnut-studio

# 运行
cargo run

# 构建 release
cargo build --release
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
├── prototypes/          # 设计文档
├── docs/                # 项目文档
├── Cargo.toml           # 依赖配置
└── .cargo/config.toml   # Aliyun 镜像源
```

## 功能状态

| 功能 | 状态 | 说明 |
|------|------|------|
| PaneGrid 布局 | ✅ 完成 | 可拖拽调整、最大化、关闭 |
| 面板显隐 | ✅ 完成 | 菜单栏切换 |
| 暗色主题 | ✅ 完成 | 自定义配色 |
| 中文字体 | ✅ 完成 | HarmonyOS Sans 嵌入 |
| 视频播放 | ⏳ 待实现 | 阶段二：集成 mpv |
| 音频波形 | ⏳ 待实现 | 阶段三：Canvas 绘制 |
| 波形打轴 | ⏳ 待实现 | 阶段四：Shift+拖拽 |
| 轴卡片 | ⏳ 待实现 | 阶段五 |
| 文本编辑 | ⏳ 待实现 | 阶段六 |
| 字幕导出 | ⏳ 待实现 | 阶段七 |

## 开发文档

- [架构设计](docs/architecture.md)
- [开发指南](docs/development-guide.md)
- [MVP 路线图](prototypes/MVP_ROADMAP.md)
- [完整技术方案](prototypes/prototype.md)

## 许可证

MIT
