# Chestnut Studio — 变更日志

> 记录项目重要变更和里程碑

---

## 2026-05-05 — Phase 2 完成 + 功能增强

### Phase 2: 音频波形

- 实现 WaveformCard 音频波形卡片（pyqtgraph）
- 实现波形显示：包络线 + 原始波形叠加
- 实现红线跟随播放位置
- 实现视窗滑动跟随播放位置
- 实现点击波形跳转到对应时间
- 实现滚轮缩放（以鼠标位置为中心）
- 实现 Shift+左键拖动平移视窗
- 实现时间刻度显示（mm:ss 格式）
- 实现缩放倍数显示
- 新增 19 个 Phase 2 测试用例（59 个总计）

### 音频处理增强

- 新增 `compute_envelope()` 包络线计算函数
- 新增 `compute_envelope_fast()` 快速包络线计算（下采样版本）
- 新增 `downsample_waveform()` 波形下采样函数
- `load_waveform()` 新增 `vocal_enhance` 参数，支持人声增强
  - 立体声：提取中心声道，抑制两侧背景音乐
  - 单声道：高通滤波去除低频噪音

### AB 循环功能

- PlayerCard 新增 AB 循环功能
  - `set_ab_loop_a()` 设置 A 点
  - `set_ab_loop_b()` 设置 B 点
  - `clear_ab_loop()` 清除循环
  - 播放时自动在 A-B 区间循环
- ToolBar 新增 AB 循环按钮（A / B / ×）
- WaveformCard 新增 AB 循环区域显示（半透明橙色）
- MainWindow 新增全局快捷键
  - `[` 设置 A 点
  - `]` 设置 B 点
  - `\` 清除 AB 循环
  - `Space` 播放/暂停（解决焦点问题）

### UI 改进

- 视频加载后自动铺满卡片（nativeSizeChanged 信号）
- 隐藏波形图左下角 Auto Range 按钮
- 波形图 Y 轴居中显示
- 工具栏 AB 循环按钮激活时变蓝色高亮

### 技术决策

1. **包络线 + 波形叠加** - 包络线显示能量轮廓，波形线显示细节
2. **下采样到 5000 点** - 保留峰值特征的同时提升绘图性能
3. **PlotCurveItem fillLevel** - 替代 FillBetweenItem，性能更好
4. **MainWindow.keyPressEvent** - 全局快捷键，解决焦点问题
5. **AB 循环信号机制** - PlayerCard 发射信号，ToolBar 和 WaveformCard 响应

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
- 创建 CLAUDE.md AI 开发指南

### 修正内容

- 修正项目结构：`src/` → `chestnut_studio/`
- 修正导入路径：`from src.core...` → `from chestnut_studio.core...`
- 修正依赖管理：`requirements.txt` → `uv.lock`
- 修正工具链命令：`uv run ruff check src/` → `uv run ruff check chestnut_studio/`
