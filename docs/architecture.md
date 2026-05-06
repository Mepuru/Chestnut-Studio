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
| `main_window.py` | 主窗口，管理四个 DockWidget 卡片的布局，连接各组件信号，处理全局快捷键 |
| `toolbar.py` | 工具栏，播放控制（播放/暂停、跳转、倍速、帧号显示、AB 循环） |
| `menubar.py` | 菜单栏，文件/视图/帮助菜单 |
| `statusbar.py` | 状态栏，三段式显示（状态/视频参数/当前时间/总时间） |
| `cards/player_card.py` | 视频播放卡片，QMediaPlayer + 拖放打开 + 字幕叠加 + AB 循环 |
| `cards/timeline_card.py` | 时间轴列表卡片，显示已打轴的字幕条（编号 + 起止时间 + 查看/编辑/锁定） |
| `cards/waveform_card.py` | 音频波形卡片，波形显示 + 包络线 + AB 循环区域 + 滚轮缩放 + Shift 拖动 + 打轴功能 |
| `cards/translate_card.py` | 翻译面板卡片，填写源语言和目标语言内容（Phase 4 实现） |

### 2.2 核心层 (`chestnut_studio/core/`)

| 模块 | 职责 |
|------|------|
| `ffmpeg.py` | FFmpeg 封装，视频信息解析、音轨提取 |
| `audio.py` | 音频数据处理，波形加载、包络计算、人声增强 |
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
ToolBar                          MainWindow                         PlayerCard
  │ play_clicked ──────────────→ play_pause ───────────────────→ QMediaPlayer
  │ skip_forward ──────────────→ _on_skip_forward ──────────────→ set_position
  │ ab_loop_a_clicked ─────────→ _on_ab_loop_set_a ────────────→ set_ab_loop_a
  │ ab_loop_b_clicked ─────────→ _on_ab_loop_set_b ────────────→ set_ab_loop_b
  │ ab_loop_clear_clicked ─────→ _on_ab_loop_clear ────────────→ clear_ab_loop
  │ ←───────────────────────── update_position ←──────────────── position_changed
  │ ←───────────────────────── set_duration ←─────────────────── duration_changed
  │ ←───────────────────── update_ab_loop_state ←─────────────── ab_loop_changed
                              │
                              ├──→ WaveformCard.update_position
                              ├──→ WaveformCard.set_ab_loop_region
                              ├──→ TimelineCard.set_player_position
                              └──→ StatusBar.set_time

WaveformCard
  │ position_clicked ──────────→ PlayerCard.set_position
  │ subtitle_created ──────────→ TimelineCard.add_subtitle

TimelineCard
  │ subtitle_selected ─────────→ TranslateCard.show_subtitle
  │ subtitle_changed ──────────→ WaveformCard.refresh_overlay
  │ jump_to_position ──────────→ PlayerCard.set_position

TranslateCard
  │ translation_saved ─────────→ TimelineCard.update_translation
```

### 4.3 AB 循环流程

1. 用户按 `[` 或点击 A 按钮 → `PlayerCard.set_ab_loop_a()`
2. 用户按 `]` 或点击 B 按钮 → `PlayerCard.set_ab_loop_b()`
3. `PlayerCard.ab_loop_changed` 发射 → 更新工具栏按钮样式 + 波形图循环区域
4. 播放时 `_on_position_changed` 检测位置 → 超过 B 点自动跳回 A 点
5. 用户按 `\` 或点击 × 按钮 → `PlayerCard.clear_ab_loop()` 清除循环

---

## 五、布局系统

### 5.1 默认布局

比例：左 39% 右 61%，上 56% 下 44%，窗口缩放时保持比例不变。

```
┌──────────────────┬───────────────────────────────┐
│                  │                               │
│  Player          │  Timeline (打轴)              │
│                  │                               │
├──────────────────┼───────────────────────────────┤
│  Waveform        │  Translation (翻译)           │
│                  │                               │
└──────────────────┴───────────────────────────────┘
```

布局通过 `addDockWidget` 显式指定左右区域，`splitDockWidget` 在区域内垂直分割，`resizeDocks` 动态计算尺寸。`resizeEvent` 中按固定比例维护。

### 5.2 布局持久化

使用 `QSettings` 保存和恢复布局：
- 保存时机：`closeEvent`
- 恢复时机：`__init__`（开发阶段跳过）

### 5.3 布局调试

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
