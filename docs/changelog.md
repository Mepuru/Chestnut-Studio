# Chestnut Studio — 变更日志

> 记录项目重要变更和里程碑

---

## 2026-05-05 — Phase 0 完成

### 完成内容

- 初始化 Python 项目结构（pyproject.toml、chestnut_studio/ 目录）
- 创建 MainWindow 主窗口，支持四卡片布局
- 实现四个卡片组件：PlayerCard、TimelineCard、WaveformCard、TranslateCard
- 实现 MenuBar 菜单栏（文件/视图/帮助）
- 实现 StatusBar 状态栏（三段式显示）
- 添加暗色主题 style.qss（Tokyo Night 风格）
- 集成 HarmonyOS Sans 字体
- 支持布局保存与恢复（QSettings）
- 禁用 Tab 合并，卡片保持独立
- 添加测试用例（test_phase0.py、test_subtitle.py）

### 技术决策

1. **使用 QDockWidget 实现卡片** - 支持拖拽、停靠、浮动
2. **禁用 Tab 合并** - 每个卡片保持独立，不合并为标签页
3. **使用 Tokyo Night 配色** - 现代极简暗色主题
4. **集成 HarmonyOS Sans 字体** - 更好的中文显示效果

---

## 2026-05-05 — 文档整理

### 完成内容

- 创建 docs/ 目录
- 创建 architecture.md 架构文档
- 创建 development.md 开发指南（修正原 development-guide.md 中的错误）
- 创建 changelog.md 变更日志
- 更新 README.md 项目结构说明

### 修正内容

- 修正项目结构：`src/` → `chestnut_studio/`
- 修正导入路径：`from src.core...` → `from chestnut_studio.core...`
- 修正依赖管理：`requirements.txt` → `uv.lock`
- 修正工具链命令：`uv run ruff check src/` → `uv run ruff check chestnut_studio/`
