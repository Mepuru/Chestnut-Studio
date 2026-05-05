# Chestnut Studio — 变更日志

> 记录项目重要变更和里程碑

---

## 2026-05-05 — Phase 1 完成

### 完成内容

- 实现 PlayerCard 视频播放卡片（QMediaPlayer + QGraphicsVideoItem）
- 实现 ToolBar 工具栏（播放/暂停、跳转5秒、倍速选择、帧号显示）
- 视频画面自动铺满卡片（fitInView 保持宽高比）
- 支持拖放打开视频文件
- FFmpeg 增强：码率解析、多字节编码修复、attached pic 流跳过
- PlayerCard 空状态提示（未加载视频时显示操作引导）
- 状态栏时间改为 MM:SS / MM:SS 格式
- 默认布局：左 39% 右 61%，上 56% 下 44%，窗口缩放保持比例
- 菜单 视图 > 布局 > 默认布局 可重置布局
- 菜单 视图 > 布局 > 打印当前布局 输出调试信息
- 新增 24 个 Phase 1 测试用例（40 个总计）

### 技术决策

1. **QGraphicsVideoItem 渲染视频** - 配合 fitInView 自动缩放居中
2. **工具栏统一控制播放** - PlayerCard 不再包含播放按钮，只负责渲染
3. **addDockWidget 显式指定区域** - splitDockWidget 会让第二个 widget 进入同一区域，无法创建左右分栏
4. **QTimer.singleShot 延迟 show()** - 窗口渲染完成后再显示卡片，避免不可见
5. **resizeEvent 维护比例** - 动态计算卡片尺寸，窗口缩放时比例不变

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
