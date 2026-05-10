# Chestnut Studio — 架构文档

> 项目架构、模块职责、数据流设计

---

## 一、整体架构

### 1.1 分层设计

```
┌─────────────────────────────────────────────────────────────┐
│                      UI 层 (ui/)                            │
│  MainWindow · MenuBar · StatusBar · Cards · Dialogs         │
├─────────────────────────────────────────────────────────────┤
│                    核心层 (core/)                            │
│  FFmpeg · Audio · Subtitle · SubtitleIO                     │
├─────────────────────────────────────────────────────────────┤
│                    工具层 (utils/)                           │
│  time_utils                                                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 依赖关系

- **UI 层** → 依赖核心层和工具层，依赖 PySide6
- **核心层** → 只依赖工具层，不依赖 PySide6（可独立测试）
- **工具层** → 无外部依赖

### 1.3 设计原则

- **职责分离**：每层只负责自己的功能，不越界
- **信号通信**：卡片间通过信号通信，不直接引用
- **纯函数设计**：工具函数无状态无副作用
- **可测试性**：核心层可独立测试，无需 UI 环境

---

## 二、模块职责

### 2.1 UI 层 (`chestnut_studio/ui/`)

| 模块 | 职责 |
|------|------|
| `main_window.py` | 主窗口，初始化和协调各组件 |
| `signal_manager.py` | 信号管理器，集中管理所有信号连接（声明式 + 中转） |
| `layout_config.py` | 布局配置数据类，从 JSON 加载布局 |
| `layout_engine.py` | 布局应用引擎，根据配置自动布局 |
| `auto_menu.py` | 菜单自动生成，从注册表构建视图菜单 |
| `toolbar.py` | 工具栏，播放控制（播放/暂停、跳转、倍速、帧号显示、AB 循环） |
| `menubar.py` | 菜单栏，文件/视图/帮助菜单 |
| `statusbar.py` | 状态栏，三段式显示（状态/视频参数/当前时间/总时间） |
| `drag_overlay.py` | 拖放覆盖层，全局文件拖放、类型识别、视觉反馈 |
| `cards/base_card.py` | BaseCard 基类，所有卡片的统一父类，提供生命周期钩子 |
| `cards/registry.py` | 卡片注册表，@register_card 装饰器自动注册 |
| `cards/player_card.py` | 视频播放卡片，QMediaPlayer + 字幕叠加 + AB 循环 |
| `cards/timeline_card.py` | 时间轴列表卡片，显示已打轴的字幕条（编号 + 起止时间 + 查看/编辑/锁定） |
| `cards/waveform_card.py` | 音频波形卡片，波形显示 + 包络线 + AB 循环区域 + 滚轮缩放 + Shift 拖动 + 打轴功能 |
| `cards/translate_card.py` | 翻译面板卡片，编辑当前轨道的字幕文本，支持快速跳转 |
| `dialogs/edit_subtitle_dialog.py` | 字幕编辑对话框，可视化调整字幕起止点 |

**详细文档：**
- [UI 层概述](ui/README.md)
- [主窗口](ui/main_window.md)
- [工具栏](ui/toolbar.md)
- [菜单栏](ui/menubar.md)
- [状态栏](ui/statusbar.md)
- [卡片组件概述](ui/cards/README.md)
- [视频播放卡片](ui/cards/player_card.md)
- [音频波形卡片](ui/cards/waveform_card.md)
- [时间轴列表卡片](ui/cards/timeline_card.md)
- [翻译面板卡片](ui/cards/translate_card.md)
- [字幕编辑对话框](ui/dialogs/edit_subtitle_dialog.md)

---

### 2.2 核心层 (`chestnut_studio/core/`)

| 模块 | 职责 |
|------|------|
| `ffmpeg.py` | FFmpeg 封装，视频信息解析、音轨提取 |
| `audio.py` | 音频数据处理，波形加载、包络计算、人声增强 |
| `subtitle.py` | 字幕数据结构，SubtitleEntry 定义、字幕操作 |
| `subtitle_io.py` | 字幕导入导出，SRT/ASS/VTT/LRC 格式 |

**详细文档：**
- [核心层概述](core/README.md)
- [FFmpeg 封装](core/ffmpeg.md)
- [音频处理](core/audio.md)
- [字幕数据结构](core/subtitle.md)
- [字幕导入导出](core/subtitle_io.md)

---

### 2.3 工具层 (`chestnut_studio/utils/`)

| 模块 | 职责 |
|------|------|
| `time_utils.py` | 时间格式转换，毫秒与各格式互转 |
| `version.py` | 版本号工具，从 pyproject.toml 单源读取 |

**详细文档：**
- [工具层概述](utils/README.md)
- [时间格式转换](utils/time_utils.md)

---

## 三、数据结构

### 3.1 字幕字典 (SubtitleDict)

```python
from chestnut_studio.core.subtitle import SubtitleEntry, SubtitleDict

# 字幕字典类型
# key: 列号 (1-8)
# value: {start_ms: SubtitleEntry(duration_ms, text), ...}
SubtitleDict = dict[int, dict[int, SubtitleEntry]]
```

**示例：**
```python
{
    1: {  # 第 1 列（原文）
        1000: SubtitleEntry(2000, "你好"),
        4000: SubtitleEntry(1500, "世界"),
    },
    2: {},  # 第 2 列（翻译）
    ...
}
```

### 3.2 视频信息 (VideoInfo)

```python
@dataclass
class VideoInfo:
    duration: int = 0   # 时长 (ms)
    width: int = 0      # 宽度
    height: int = 0     # 高度
    fps: float = 0.0    # 帧率
    bitrate: int = 0    # 码率 (kbps)
```

---

## 四、信号通信

### 4.1 卡片间通信原则

- 卡片间通过 **信号 (Signal)** 通信，不直接引用
- **SignalManager** 集中管理所有信号连接
- 卡片通过 `listens_to()` 声明订阅的信号
- 信号命名：小写 + 下划线，描述事件

### 4.2 信号架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        SignalManager                            │
│                                                                 │
│  卡片声明 @subscribe / listens_to():                            │
│    WaveformCard ← player.position_changed/duration_changed     │
│    TimelineCard ← player.duration_changed                      │
│    TranslateCard ← timeline.subtitle_selected                  │
│    PlayerCard ← waveform.position_clicked                      │
│                ← timeline.jump_to_position                     │
│                ← toolbar.play_clicked/rate_changed/ab_loop_*   │
│                                                                 │
│    ToolBar ← player.position_changed/duration_changed          │
│            ← player.playback_state_changed/ab_loop_changed     │
│                                                                 │
│  中转处理 (@relay 装饰器):                                       │
│    player.video_opened → MainWindow._on_video_opened           │
│    player.ab_loop_changed → MainWindow._on_ab_loop_changed     │
│    waveform.subtitle_created → MainWindow._on_subtitle_created │
│    timeline.subtitle_selected → MainWindow._on_subtitle_selected│
│    translate.jump_to_next/prev → MainWindow._on_jump_to_*      │
│                                                                 │
│  动态订阅 (状态栏等):                                            │
│    player.position_changed → StatusBar.set_time                │
│    player.duration_changed → StatusBar.set_status              │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 AB 循环流程

1. 用户按 `[` 或点击 A 按钮 → `PlayerCard.set_ab_loop_a()`
2. 用户按 `]` 或点击 B 按钮 → `PlayerCard.set_ab_loop_b()`
3. `PlayerCard.ab_loop_changed` 发射 → 更新工具栏按钮样式 + 波形图循环区域
4. 播放时 `_on_position_changed` 检测位置 → 超过 B 点自动跳回 A 点
5. 用户按 `\` 或点击 × 按钮 → `PlayerCard.clear_ab_loop()` 清除循环

---

## 五、布局系统

### 5.1 配置驱动布局

布局配置存储在 `resources/layouts/default.json`，使用 `LayoutConfig` 数据类加载：

```json
{
  "name": "默认布局",
  "description": "左 39% 右 61%，上 56% 下 44%",
  "version": 1,
  "columns": [
    {
      "width_ratio": 0.39,
      "rows": [
        { "card": "player", "height_ratio": 0.56 },
        { "card": "waveform", "height_ratio": 0.44 }
      ]
    },
    {
      "width_ratio": 0.61,
      "rows": [
        { "card": "timeline", "height_ratio": 0.56 },
        { "card": "translate", "height_ratio": 0.44 }
      ]
    }
  ]
}
```

### 5.2 布局引擎

`layout_engine.py` 提供 `apply_layout()` 函数，根据配置自动布局卡片：
- 移除所有现有卡片
- 按列布局，支持多列
- 按比例调整尺寸

### 5.3 布局持久化

使用 `QSettings` 保存和恢复布局：
- 保存时机：`closeEvent`
- 恢复时机：`__init__`（开发阶段跳过）

### 5.4 布局调试

菜单 **视图 > 布局 > 打印当前布局** 可输出各卡片的区域、尺寸、位置到控制台。

---

## 六、主题系统

### 6.1 配色方案 (Tokyo Night)

| 用途 | 颜色 |
|------|------|
| 深色背景 | `#0f0f14` |
| 卡片标题 | `#18181b` |
| 边框 | `#27272a` |
| 强调色 | `#2563eb` |
| 主文字 | `#fafafa` |
| 次要文字 | `#a1a1aa` |

### 6.2 字体

使用 HarmonyOS Sans 字体，位于 `chestnut_studio/resources/fonts/`

---

## 七、测试策略

### 7.1 测试分层

| 层级 | 测试重点 |
|------|---------|
| 核心层 | 必须完整测试（数据结构核心） |
| UI 层 | 可选，优先测试核心逻辑 |

### 7.2 测试文件

```
tests/
├── conftest.py           # 测试配置，共享 fixtures
├── test_phase0.py        # Phase 0 基础设施测试
├── test_phase1.py        # Phase 1 视频播放测试（FFmpeg/PlayerCard/ToolBar）
├── test_phase2.py        # Phase 2 音频波形测试（WaveformCard/WaveformPlotWidget）
└── test_subtitle.py      # 字幕数据结构测试
```

---

## 八、文档结构

```
docs/
├── README.md                    # 文档导航首页
├── architecture.md              # 架构文档（本文件）
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
