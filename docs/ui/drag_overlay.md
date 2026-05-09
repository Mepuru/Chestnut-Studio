# 拖放覆盖层

> `chestnut_studio/ui/drag_overlay.py`
> `DragOverlay(QWidget)` — 全局文件拖放覆盖层，统一处理视频和字幕文件的拖放导入。

---

## 职责

- 拦截 MainWindow 上的所有文件拖放事件
- 显示全屏半透明覆盖层，提供视觉反馈
- 根据文件后缀自动识别类型（视频/字幕）
- 高亮对应的拖放区域
- 将文件分发到正确的处理流程

---

## 设计理念

### 统一拖放入口

不再让各卡片分别处理拖放事件，而是由 MainWindow 统一拦截：

- 避免视频区域和字幕区域的拖放事件冲突
- 提供一致的用户体验
- 集中管理文件类型判断逻辑

### 自动识别

根据文件后缀自动判断类型，无需用户手动选择：

| 后缀 | 类型 | 处理方式 |
|------|------|----------|
| `.mp4` `.avi` `.flv` `.mkv` `.mov` `.wmv` | 视频 | 加载到播放器 |
| `.mp3` `.wav` `.aac` `.flac` `.ogg` | 音频 | 加载到播放器 |
| `.srt` `.ass` `.vtt` `.lrc` | 字幕 | 导入字幕数据 |
| 其他 | 未知 | 忽略 |

---

## 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `video_dropped(str)` | `path` | 视频/音频文件被放下 |
| `subtitle_dropped(str)` | `path` | 字幕文件被放下 |

---

## 布局

```
┌─────────────────────────────────────────────┐
│                                             │
│    ┌───────────────────────────────────┐    │
│    │                                   │    │
│    │      拖放文件到此处                │    │  ← 默认状态（灰色虚线）
│    │                                   │    │
│    │      🎬 放开以加载视频             │    │  ← 拖入视频（蓝色虚线）
│    │                                   │    │
│    │      📝 放开以导入字幕             │    │  ← 拖入字幕（绿色虚线）
│    │                                   │    │
│    │      不支持的文件格式              │    │  ← 其他文件（红色虚线）
│    │                                   │    │
│    └───────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
```

居中圆角卡片，深色背景 `#18181b`，虚线边框根据文件类型切换颜色。

---

## 工作流程

```
用户拖入文件
    │
    ▼
MainWindow.eventFilter(DragEnter)
    │
    ├─ 检查后缀是否支持
    │   ├─ 不支持 → 忽略
    │   └─ 支持 → 显示覆盖层，高亮对应区域
    │
    ▼
用户释放文件
    │
    ▼
MainWindow.eventFilter(Drop)
    │
    ├─ DragOverlay.handle_drop(paths)
    │   ├─ 视频 → emit video_dropped(path)
    │   └─ 字幕 → emit subtitle_dropped(path)
    │
    ▼
MainWindow 接收信号
    ├─ video_dropped → _open_video_file(path)
    └─ subtitle_dropped → _import_subtitle_file(path)
```

---

## 内部方法

| 方法 | 说明 |
|------|------|
| `update_for_files(paths)` | 根据文件类型切换卡片样式（颜色和文字） |
| `handle_drop(paths)` | 处理放下事件，分发信号 |
| `_apply_style(border, color, text)` | 应用卡片样式 |

---

## 用法示例

```python
from chestnut_studio.ui.drag_overlay import DragOverlay

# 创建覆盖层（通常由 MainWindow 创建）
overlay = DragOverlay(main_window)

# 连接信号
overlay.video_dropped.connect(on_video_dropped)
overlay.subtitle_dropped.connect(on_subtitle_dropped)

# 由 MainWindow 的 eventFilter 自动调用
# 手动使用：
overlay.update_for_files(["/path/to/video.mp4"])
overlay.show()

overlay.handle_drop(["/path/to/video.mp4"])
```

---

## 事件过滤器

MainWindow 通过 `installEventFilter` 安装全局事件过滤器，
在 `eventFilter` 方法中拦截 `DragEnter`、`DragLeave`、`Drop` 事件：

| 事件 | 处理 |
|------|------|
| `DragEnter` | 检查后缀 → 显示覆盖层 → accept |
| `DragLeave` | 隐藏覆盖层 |
| `Drop` | 调用 `handle_drop` → accept |

---

## 依赖

- PySide6: `QWidget`, `QLabel`, `QVBoxLayout`
- chestnut_studio.ui.main_window: 信号接收方
