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
│  time_utils · config                                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 依赖关系

- **UI 层** → 依赖核心层和工具层，依赖 PySide6
- **核心层** → 只依赖工具层，不依赖 PySide6（可独立测试）
- **工具层** → 无外部依赖

---

## 二、模块职责

### 2.1 UI 层 (`chestnut_studio/ui/`)

| 模块 | 职责 |
|------|------|
| `main_window.py` | 主窗口，管理四个 DockWidget 卡片的布局 |
| `menubar.py` | 菜单栏，文件/视图/帮助菜单 |
| `statusbar.py` | 状态栏，三段式显示（状态/视频参数/时间） |
| `cards/player_card.py` | 视频播放卡片（Phase 1 实现） |
| `cards/timeline_card.py` | 打轴编辑卡片（Phase 3 实现） |
| `cards/waveform_card.py` | 音频波形卡片（Phase 2 实现） |
| `cards/translate_card.py` | 翻译面板卡片（Phase 4 实现） |

### 2.2 核心层 (`chestnut_studio/core/`)

| 模块 | 职责 |
|------|------|
| `ffmpeg.py` | FFmpeg 封装，视频信息解析、音轨提取 |
| `audio.py` | 音频数据处理，波形加载、平滑 |
| `subtitle.py` | 字幕数据结构，SubtitleDict 定义、撤销重做 |
| `subtitle_io.py` | 字幕导入导出，SRT/ASS/VTT/LRC 格式 |

### 2.3 工具层 (`chestnut_studio/utils/`)

| 模块 | 职责 |
|------|------|
| `time_utils.py` | 时间格式转换，毫秒与各格式互转 |

---

## 三、数据结构

### 3.1 字幕字典 (SubtitleDict)

```python
# 字幕字典类型
# key: 列号 (0-4)
# value: {start_ms: [duration_ms, "text"], ...}
SubtitleDict = dict[int, dict[int, list]]
```

**示例：**
```python
{
    0: {  # 第 0 列（原文）
        1000: [2000, "你好"],
        4000: [1500, "世界"],
    },
    1: {},  # 第 1 列（翻译）
    2: {},
    3: {},
    4: {},
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
- MainWindow 负责连接各卡片的信号

### 4.2 信号流

```
PlayerCard                    WaveformCard
  │ position_changed ──────────→ update_position
  │                              │
  ▼                              ▼
TimelineCard                  TranslateCard
  │ highlight_row               │ show_subtitle
  │                              │
  └──────────────────────────────┘
```

---

## 五、布局系统

### 5.1 默认布局

```
┌───────────────────────┬───────────────────────┐
│                       │                       │
│    视频播放卡片         │    打轴编辑卡片        │
│    (左 55%)           │    (右 45%)           │
│                       │                       │
├───────────────────────┼───────────────────────┤
│                       │                       │
│    音频波形卡片         │    翻译面板卡片        │
│    高度 200px          │    高度 200px          │
│                       │                       │
└───────────────────────┴───────────────────────┘
```

### 5.2 布局持久化

使用 `QSettings` 保存和恢复布局：
- 保存时机：`closeEvent`
- 恢复时机：`__init__`

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
└── test_subtitle.py      # 字幕数据结构测试
```
