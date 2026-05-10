# 状态栏

> `chestnut_studio/ui/statusbar.py`
> `StatusBar(QStatusBar)` — 三段式状态栏。

---

## 职责

- 显示应用状态信息
- 显示视频参数（分辨率、帧率、码率）
- 显示当前播放时间和总时长

---

## 布局

```
[就绪]  [1920×1080 · 60fps · 2000kbps]  [01:32 / 05:30]  [v1.1.1]
 左1            中2（拉伸）                  右1           右侧永久
```

- 左侧：状态信息（就绪、加载中、错误等）
- 中间：视频参数（分辨率、帧率、码率）
- 右侧：时间显示（当前时间 / 总时长）
- 右侧永久：版本号（从 `pyproject.toml` 读取，灰色小字）

---

## 公有方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_status(text)` | `str` | 设置左侧状态信息 |
| `set_video_info(resolution, fps, bitrate)` | `str, str, str` | 设置中间视频参数（空参数不显示） |
| `set_time(current, total)` | `str, str` | 设置右侧时间（`"MM:SS" / "MM:SS"`） |
| `clear_video_info()` | 无 | 清除视频参数 |

---

## 用法示例

```python
from chestnut_studio.ui.statusbar import StatusBar

# 创建状态栏
status_bar = StatusBar()

# 设置状态信息
status_bar.set_status("就绪")
status_bar.set_status("加载中...")
status_bar.set_status("错误：文件不存在")

# 设置视频参数
status_bar.set_video_info("1920×1080", "60fps", "2000kbps")

# 设置时间
status_bar.set_time("01:32", "05:30")

# 清除视频参数
status_bar.clear_video_info()
```

---

## 状态信息

### 常见状态

| 状态 | 说明 |
|------|------|
| `就绪` | 应用就绪，等待操作 |
| `加载中...` | 正在加载视频或音频 |
| `打轴中` | 正在打轴操作 |
| `错误：xxx` | 显示错误信息 |

### 状态更新时机

- 应用启动时：`就绪`
- 打开视频时：`加载中...`
- 视频加载完成：`就绪`
- 发生错误时：`错误：xxx`

---

## 视频参数

### 参数格式

| 参数 | 格式 | 示例 |
|------|------|------|
| 分辨率 | `宽×高` | `1920×1080` |
| 帧率 | `数字fps` | `60fps` |
| 码率 | `数字kbps` | `2000kbps` |

### 参数更新时机

- 视频加载完成时：从 FFmpeg 获取视频信息
- 视频关闭时：清除参数

---

## 时间显示

### 时间格式

- 格式：`MM:SS`
- 当前时间：`01:32`
- 总时长：`05:30`
- 显示：`01:32 / 05:30`

### 时间更新时机

- 播放位置变化时：更新当前时间
- 视频加载完成时：更新总时长
- 视频关闭时：清除时间

---

## 信号连接

### MainWindow 连接

```python
# 位置变化时更新时间
self.player_card.position_changed.connect(
    lambda ms: self.status_bar.set_time(
        split_time(ms), 
        split_time(self.player_card.get_duration())
    )
)

# 视频加载完成时更新视频信息
self.player_card.video_opened.connect(
    lambda path: self.status_bar.set_video_info(
        f"{info.width}×{info.height}",
        f"{info.fps}fps",
        f"{info.bitrate}kbps"
    )
)
```

---

## 注意事项

### 布局拉伸

- 中间区域使用拉伸因子，确保视频参数居中显示
- 左侧和右侧固定宽度

### 参数为空

- 视频未加载时，中间区域不显示
- 使用 `clear_video_info()` 清除参数

### 时间格式

- 使用 `split_time()` 函数转换毫秒为 `MM:SS` 格式
- 确保时间字符串宽度固定，避免布局跳动

---

## 依赖

- PySide6: `QStatusBar`, `QLabel`
- chestnut_studio.utils.time_utils: `split_time`
- chestnut_studio.utils.version: `get_version`
