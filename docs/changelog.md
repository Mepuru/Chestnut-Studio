# Chestnut Studio — 变更日志

> 记录项目重要变更和里程碑

---

## v1.2.1 — 2026-05-12 — 播放位置同步精度提升

### 修复

- **播放位置同步精度**：用 `QTimer(16ms)` 轮询替代 `QMediaPlayer.positionChanged` 信号，位置更新从 ~250ms 提升至 ~60fps
  - 波形红线平滑连续移动，不再跳跃
  - I/O 打轴误差从 ±250ms 降至 ±16ms
  - 帧号显示刷新率从 ~4fps 提升至 ~60fps
  - AB 循环跳回精度同步提升

### 原因

Qt6 的 `QMediaPlayer.positionChanged` 信号触发频率由后端决定（默认 ~250ms），且 `setPositionUpdateInterval()` 在 PySide6 中不可用。改用 QTimer 主动轮询 `player.position()` 完全绕过此限制。

### 受影响文件

| 文件 | 变更 |
|------|------|
| `ui/cards/player_card.py` | 新增 `_position_timer`（QTimer），移除 `positionChanged` 信号连接，暂停态手动触发位置更新 |

---

## v1.2.0 — 2026-05-11 — 可扩展架构重构

### 重大变更

- **可扩展架构重构**：实现 BaseCard 基类、卡片注册表、声明式信号系统、配置驱动布局、菜单自动生成
- **100% 自动化信号系统**：所有组件通过 `@subscribe`/`@relay` 装饰器或 `listens_to()` 方法声明信号订阅
- **SignalManager 独立模块**：集中管理所有信号连接，MainWindow 不再包含具体业务逻辑

### 新增模块

| 模块 | 文件 | 职责 |
|------|------|------|
| BaseCard | `ui/cards/base_card.py` | 所有卡片的基类，提供生命周期钩子和声明式信号订阅 |
| 卡片注册表 | `ui/cards/registry.py` | @register_card 装饰器，自动发现和注册卡片 |
| 信号管理器 | `ui/signal_manager.py` | 集中管理所有信号连接 |
| 信号装饰器 | `ui/signal_decorator.py` | @subscribe/@relay 装饰器 |
| 布局配置 | `ui/layout_config.py` | LayoutConfig 数据类，从 JSON 加载布局 |
| 布局引擎 | `ui/layout_engine.py` | apply_layout() 布局应用引擎 |
| 菜单自动生成 | `ui/auto_menu.py` | build_card_submenu/build_layout_submenu |

### 新增资源

- `resources/layouts/default.json` — 默认布局配置文件

### 架构改进

| 指标 | 改造前 | 改造后 |
|------|--------|--------|
| 新增卡片改动文件数 | 2-3 个 | 1 个（新文件） |
| 新增卡片改动代码行数 | ~20 行 | 0 行 |
| MainWindow 信号连接 | 手动连接 | 声明式自动连接 |
| 布局配置 | 硬编码 | JSON 配置文件 |
| 菜单维护 | 手动 | 自动生成 |

### 卡片迁移

所有 4 张卡片已迁移到 BaseCard：

| 卡片 | card_id | default_area | default_ratio |
|------|---------|--------------|---------------|
| PlayerCard | `player` | LeftDockWidgetArea | 0.39 |
| WaveformCard | `waveform` | BottomDockWidgetArea | 0.44 |
| TimelineCard | `timeline` | RightDockWidgetArea | 0.56 |
| TranslateCard | `translate` | BottomDockWidgetArea | 0.44 |

### 信号系统

**声明方式**：

```python
# 方式 1：@subscribe 装饰器
@subscribe("player.position_changed")
def update_position(self, ms): ...

# 方式 2：listens_to() 方法
def listens_to(self):
    return {"player.position_changed": "update_position"}

# 方式 3：@relay 装饰器（MainWindow 中转）
@relay("player.video_opened")
def _on_video_opened(self, path): ...
```

### 文档更新

- 新增 7 个架构文档：base_card.md、registry.md、signal_manager.md、signal_decorator.md、layout_config.md、layout_engine.md、auto_menu.md
- 更新 CLAUDE.md：信号连接图、关键路径
- 更新 docs/architecture.md：信号架构、布局系统
- 更新 docs/README.md：文档结构、快速导航
- 更新所有卡片文档：QDockWidget → BaseCard
- 更新开发指南：项目结构

### 测试

- 62 个测试全部通过
- 无回归问题

---

## v1.1.1 — 2026-05-10 — Phase A 性能优化 + 轨道修复

### 新增

- **性能优化方案文档**：`docs/performance-optimization.md`，包含瓶颈分析、短期修复方案和长期架构改进规划（SubtitleModel）
- **SubtitleEntry NamedTuple**：替代 bare list，提供类型安全，支持属性访问（`.duration_ms`、`.text`）和索引访问（`[0]`、`[1]`）
- 新增 `test_subtitle_entry_access` 测试用例

### 重构

- **删除 SubtitleManager 中未使用的 undo/redo 代码**：移除 `push_undo()`、`undo()`、`redo()` 方法和 `MAX_UNDO`、`_undo_stack`、`_undo_index`、`_in_undo_mode` 属性（均为死代码，UI 层有独立的撤销系统）
- **subtitle_io.py 消除代码重复**：移除内部重复定义的 `ms_to_srt_time`、`srt_time_to_ms`、`ms_to_ass_time`、`ass_time_to_ms`，改为从 `time_utils.py` 导入
- **TimelineCard 撤销优化**：`_push_undo()` 中 `locked_states` 使用 `set.copy()` 替代 `copy.deepcopy()`；`_undo()`/`_redo()` 恢复快照时使用浅拷贝而非 `copy.deepcopy()`
- **移除 timeline_card.py 中未使用的 `import copy`**

### 优化

- **缓存 track_colors 到实例变量**：
  - `TimelineCard.__init__` 中预计算 `_track_colors_fg` 和 `_track_colors_bg`，`_update_table()` 不再在每行循环内重建 QColor
  - `WaveformCard.__init__` 中预计算 `_track_overlay_colors`，`_draw_subtitle_region()` 不再为每个字幕区域重建颜色列表
- **修复未声明的动态属性**：
  - `WaveformCard._subtitle_full_data` 现在在 `__init__` 中声明，移除 `_update_subtitle_overlay()` 中的 `hasattr` 防御检查

### 修复

- **轨道筛选偏移一位**：`_on_track_filter_changed` 中 `index - 1` 导致轨道 1 显示为空、轨道 2 显示轨道 1 的数据，修正为 `-1 if index == 0 else index`
- **默认轨道数从 4 扩展为 8**：`DEFAULT_TRACK_COUNT` 和 `SubtitleManager` 初始数据均更新为 8 轨道

### 受影响文件

| 文件 | 变更 |
|------|------|
| `core/subtitle.py` | 新增 `SubtitleEntry`，更新类型别名，删除 undo 代码 |
| `core/subtitle_io.py` | 消除重复函数，改用 `SubtitleEntry` 类型 |
| `core/__init__.py` | 导出 `SubtitleEntry` |
| `ui/cards/timeline_card.py` | 缓存颜色、优化撤销、使用 `SubtitleEntry` |
| `ui/cards/waveform_card.py` | 缓存颜色、声明 `_subtitle_full_data`、使用属性访问 |
| `ui/cards/translate_card.py` | `subtitle[1]` → `subtitle.text` |
| `tests/test_subtitle.py` | 适配 `SubtitleEntry`，移除 undo 测试，新增属性访问测试 |

---

## v1.1.0 — 2026-05-10

### 新增

- **全局拖放覆盖层**：拖入文件时显示居中圆角卡片，自动识别视频/字幕类型
- **轨道集中配置**：新增 `core/track_config.py`，统一管理轨道颜色和数量（最多 8 个）
- **时间轴文本列**：导入字幕后文本内容直接在时间轴表格中可见

### 修复

- 拖放视频到播放器窗口后正确加载波形图
- 禁止在未加载视频时导入字幕，避免波形图显示异常
- 禁用视频窗口的鼠标滚轮滚动
- ASS 导出按起始帧排序而非按轨道顺序

### 优化

- 所有 UI 组件统一使用 TrackConfig 管理轨道颜色
- PlayerCard 和 TimelineCard 移除各自的拖放处理，由 MainWindow 统一拦截

---

## 2026-05-08 — 文档结构重组

### 重大调整：文档按模块分层组织

- **文档层级**：将文档按代码模块分层组织，每个模块都有独立的文档
- **导航首页**：创建 `docs/README.md` 作为文档导航中心
- **模块文档**：为每个模块创建详细的接口和用法文档

### 新增文档

- `docs/README.md` - 文档导航首页
- `docs/core/README.md` - 核心层概述
- `docs/core/ffmpeg.md` - FFmpeg 封装文档
- `docs/core/audio.md` - 音频处理文档
- `docs/core/subtitle.md` - 字幕数据结构文档
- `docs/core/subtitle_io.md` - 字幕导入导出文档
- `docs/ui/README.md` - UI 层概述
- `docs/ui/main_window.md` - 主窗口文档
- `docs/ui/toolbar.md` - 工具栏文档
- `docs/ui/menubar.md` - 菜单栏文档
- `docs/ui/statusbar.md` - 状态栏文档
- `docs/ui/cards/README.md` - 卡片组件概述
- `docs/ui/cards/player_card.md` - 视频播放卡片文档
- `docs/ui/cards/waveform_card.md` - 音频波形卡片文档
- `docs/ui/cards/timeline_card.md` - 时间轴列表卡片文档
- `docs/ui/cards/translate_card.md` - 翻译面板卡片文档
- `docs/ui/dialogs/README.md` - 弹窗概述
- `docs/ui/dialogs/edit_subtitle_dialog.md` - 字幕编辑对话框文档
- `docs/utils/README.md` - 工具层概述
- `docs/utils/time_utils.md` - 时间格式转换文档

### 文档结构

```
docs/
├── README.md                    # 文档导航首页
├── architecture.md              # 架构文档
├── development.md               # 开发指南
├── changelog.md                 # 变更日志
├── core/                        # 核心层模块文档
│   ├── README.md                # 核心层概述
│   ├── ffmpeg.md                # FFmpeg 封装
│   ├── audio.md                 # 音频处理
│   ├── subtitle.md              # 字幕数据结构
│   └── subtitle_io.md           # 字幕导入导出
├── ui/                          # UI 层模块文档
│   ├── README.md                # UI 层概述
│   ├── main_window.md           # 主窗口
│   ├── toolbar.md               # 工具栏
│   ├── menubar.md               # 菜单栏
│   ├── statusbar.md             # 状态栏
│   ├── cards/                   # 卡片组件文档
│   │   ├── README.md            # 卡片组件概述
│   │   ├── player_card.md       # 视频播放卡片
│   │   ├── waveform_card.md     # 音频波形卡片
│   │   ├── timeline_card.md     # 时间轴列表卡片
│   │   └── translate_card.md    # 翻译面板卡片
│   └── dialogs/                 # 弹窗文档
│       ├── README.md            # 弹窗概述
│       └── edit_subtitle_dialog.md  # 字幕编辑对话框
└── utils/                       # 工具层模块文档
    ├── README.md                # 工具层概述
    └── time_utils.md            # 时间格式转换
```

### 设计原则

- **模块对应**：文档结构与代码模块结构一一对应
- **详细接口**：每个模块文档包含完整的接口说明
- **用法示例**：提供代码示例方便开发者理解
- **注意事项**：列出使用时需要注意的问题

---

## 2026-05-07 — Phase 4 完成（翻译面板 + 字幕导入导出）

### 数据结构优化

- 回归简单数据结构 `[duration, text]`，每个轨道独立存储一种语言
- 移除之前的 `[duration, source_text, target_text]` 设计

### 新增功能

- **复制轴功能**：支持将一个轨道的字幕复制到另一个轨道
  - 底部工具栏添加源轨道/目标轨道选择和复制按钮
  - 复制时覆盖目标轨道数据，需要用户确认
- **ASS 导出**：支持多轨道 ASS 文件导出
  - 样式名根据轨道自动命名（轨道 1、轨道 2 等）
  - 不同样式自动分配不同颜色
- **字幕导入**：支持导入 SRT 和 ASS 格式字幕文件
- **翻译面板改进**：
  - Ctrl+Enter 保存并跳转下一条字幕
  - Shift+Enter 跳转到上一条字幕
  - 编辑字幕时高亮时间轴对应行
  - 禁用用户手动选中行，仅翻译区域高亮时启用

### 信号变更

- `TimelineCard.subtitle_selected` 参数从 `(start_ms)` 改为 `(col, start_ms)`
- `TranslateCard` 移除 `translation_saved` 信号，新增：
  - `text_saved(col, start_ms, text)` — 文本保存
  - `jump_to_next(col, start_ms)` — 跳转下一条
  - `jump_to_prev(col, start_ms)` — 跳转上一条
  - `editing_subtitle(col, start_ms)` — 正在编辑的字幕

### 菜单集成

- 文件 → 导入字幕：支持 SRT/ASS 格式
- 文件 → 导出字幕：导出多轨道 ASS 文件

### 文档更新

- 更新 CLAUDE.md：项目进度、快捷键、信号连接图
- 更新 README.md：核心特性、开发路线、快捷键
- 更新 docs/ui.md：TimelineCard 和 TranslateCard 接口
- 更新 docs/core.md：SubtitleManager 和 SubtitleIO 接口
- 更新 docs/changelog.md：添加本次变更记录

---

## 2026-05-06 — Phase 3 重新设计（打轴功能）

### 重大调整：打轴功能重新设计

- **打轴位置**：从时间轴卡片移到音频波形区
- **时间轴卡片**：从打轴工具改为字幕列表显示
- **工作流程**：用户在音频波形区打轴 → 时间轴列表显示

### 新的设计理念

- **音频波形区**：用户通过 `I`/`O` 快捷键打轴（标记开始/结束点）
- **时间轴列表**：显示已打轴的字幕条（编号 + 起止时间 + 操作按钮）
- **操作按钮**：查看（跳转起始点）、编辑（调整区间）、锁定

### 文档更新

- 重写 prototypes/modules/M04-timeline-card.md，改为时间轴列表卡片
- 重写 prototypes/modules/M05-translate-card.md，更新翻译面板设计
- 更新 prototypes/prototype.md，更新卡片设计和信号连接
- 更新 prototypes/roadmap.md，调整 Phase 3 和 Phase 4 描述
- 更新 CLAUDE.md，更新项目概述、快捷键清单和信号连接图
- 更新 README.md，更新核心特性、界面布局和快捷键
- 更新 docs/ui.md，更新时间轴卡片和音频波形卡片接口

---

## 2026-05-06 — Phase 3 简化设计

### 简化：移除双轴系统，改为单轴打轴 + 翻译面板双区域

- 移除时间轴卡片中的双轴显示，改为单轴打轴
- 移除工具栏中的轴选择按钮和同步锁定按钮
- 翻译面板分为源语言区和目标语言区
- 源语言和目标语言共享相同的时间点

### 设计理念

- **时间轴卡片**：只负责打轴（设置字幕的开始/结束时间），不负责填写内容
- **翻译面板**：分为源语言区和目标语言区，用户在这里填写内容
- **数据同步**：打轴时，源语言和目标语言共享相同的时间点

### 文档更新

- 更新 prototypes/modules/M04-timeline-card.md，简化为单轴打轴
- 更新 prototypes/modules/M05-translate-card.md，分为源语言区和目标语言区
- 更新 prototypes/prototype.md，移除双轴系统说明
- 更新 prototypes/roadmap.md，调整 Phase 3 和 Phase 4 描述
- 更新 CLAUDE.md，更新项目概述和信号连接图
- 更新 docs/ui.md，简化双轴系统接口说明

---

## 2026-05-06 — Phase 3 双轴系统设计

### 新增：双轴时间轴系统

- 设计双轴时间轴系统（源轴 + 译文轴）
- 轴1（源轴）：输入源语言字幕
- 轴2（译文轴）：输入翻译后的字幕
- 支持同步调整：调整轴1时间时轴2自动跟随
- 支持独立模式：可解除同步，独立调整各轴时间

### 工具栏增强

- 新增轴选择按钮：`[1]` `[2]` 用于切换当前活动轴
- 新增同步锁定按钮：`[🔒]` 用于切换同步状态
- 按钮样式：选中轴高亮蓝色，未选中灰色

### ASS 文件生成

- 支持生成包含双轴的 ASS 文件
- 源轴使用 `Default` 样式
- 译文轴使用 `Translation` 样式
- 支持选择性导出（可只导出一个轴）

### 文档更新

- 更新 prototypes/modules/M04-timeline-card.md，添加双轴系统设计
- 更新 prototypes/modules/M05-translate-card.md，集成双轴系统
- 更新 prototypes/prototype.md，添加双轴系统说明
- 更新 prototypes/roadmap.md，调整 Phase 3 和 Phase 4 描述
- 更新 CLAUDE.md，更新项目概述和信号连接图
- 更新 docs/ui.md，添加双轴系统接口说明

---

## 2026-05-06 — Phase 3 重构

### 重大调整：移除打轴功能，改为字幕列表

- 移除 timeline_card.py 中的打轴功能（虚拟滚动、拖动选择、轴管理等）
- 简化为字幕列表显示，只保留基本的编辑功能
- 移除 toolbar.py 中的打轴相关按钮（新建、合并、切割、撤销、重做）
- 移除 main_window.py 中的打轴相关信号连接
- 主窗口标题从 "Chestnut Studio - 打轴工具" 改为 "Chestnut Studio"

### 新的交互方式

- 字幕列表显示所有字幕条目（只读表格）
- 右键菜单编辑字幕（编辑文本、删除、创建）
- 撤销/重做支持（Ctrl+Z/Y）
- 位置调整通过音频图完成

### 文档更新

- 更新 README.md，移除打轴相关描述
- 更新 prototypes/roadmap.md，调整 Phase 3 描述
- 更新 CLAUDE.md，更新项目概述
- 更新 docs/architecture.md、ui.md、development.md

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
