# 工具栏

> `chestnut_studio/ui/toolbar.py`
> `ToolBar(QToolBar)` — 播放控制工具栏，实现 `listens_to()` 声明式信号订阅。

---

## 职责

- 播放控制（播放/暂停、前进/后退 5 秒）
- AB 循环控制（设置 A 点、B 点、清除循环）
- 倍速选择（0.5x - 2.0x）
- 帧号显示

---

## 声明式信号订阅

ToolBar 实现 `listens_to()` 方法，自动订阅 PlayerCard 的信号：

```python
class ToolBar(QToolBar):
    def listens_to(self) -> dict[str, str]:
        """声明本组件关心的外部信号"""
        return {
            "player.position_changed": "update_position",
            "player.duration_changed": "set_duration",
            "player.playback_state_changed": "set_playing",
            "player.ab_loop_changed": "update_ab_loop_state",
        }
```

---

## 布局

```
[帧号] | [后退5秒] [播放/暂停] [前进5秒] | 循环 [A] [B] [×] | [倍速]
```

- 左侧：当前帧号（`Frame: 123` 格式，等宽字体）
- 中央：播放控制按钮组（弹性空间居中）
- 中右：AB 循环按钮组
- 右侧：倍速下拉选择

---

## 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `play_clicked` | 无 | 播放/暂停按钮点击 |
| `skip_forward(ms)` | `int` | 前进毫秒 |
| `skip_backward(ms)` | `int` | 后退毫秒 |
| `rate_changed(rate)` | `float` | 倍速变化 |
| `ab_loop_a_clicked` | 无 | 设置 A 点 |
| `ab_loop_b_clicked` | 无 | 设置 B 点 |
| `ab_loop_clear_clicked` | 无 | 清除 AB 循环 |

---

## 公有方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_fps(fps)` | `float` | 设置视频帧率（用于帧号计算） |
| `set_duration(ms)` | `int` | 设置视频总时长 |
| `update_position(ms)` | `int` | 更新当前播放位置，刷新帧号 |
| `set_playing(playing)` | `bool` | 切换播放/暂停按钮文字 |
| `set_playback_rate(rate)` | `float` | 设置倍速下拉框选中项 |
| `update_ab_loop_state(a, b)` | `int, int` | 更新 AB 循环按钮状态和样式 |

---

## 用法示例

```python
from chestnut_studio.ui.toolbar import ToolBar

# 创建工具栏
toolbar = ToolBar()

# 连接信号
toolbar.play_clicked.connect(self.on_play)
toolbar.skip_forward.connect(self.on_skip_forward)
toolbar.rate_changed.connect(self.on_rate_changed)

# 更新状态
toolbar.set_fps(29.97)
toolbar.set_duration(300000)  # 5 分钟
toolbar.update_position(15000)  # 15 秒
toolbar.set_playing(True)
toolbar.set_playback_rate(1.0)
toolbar.update_ab_loop_state(10000, 20000)
```

---

## AB 循环按钮

### 按钮样式

- 按钮文本：`A` / `B` / `×`（28×28 像素）
- 未激活：灰色背景
- 激活后：蓝色高亮背景，鼠标悬停显示时间点
- 清除按钮初始禁用，设置循环后启用

### 状态更新

```python
# 设置 A 点
toolbar.update_ab_loop_state(10000, -1)  # A=10s, B=未设置

# 设置 B 点
toolbar.update_ab_loop_state(10000, 20000)  # A=10s, B=20s

# 清除循环
toolbar.update_ab_loop_state(-1, -1)  # 都未设置
```

---

## 帧号计算

```python
frame = int(ms * fps / 1000)
```

**示例：**
- 30fps 视频，15000ms 位置 → Frame: 450
- 29.97fps 视频，15000ms 位置 → Frame: 449

---

## 倍速选择

### 支持的倍速

| 倍速 | 说明 |
|------|------|
| 0.5x | 半速 |
| 0.75x | 3/4 速 |
| 1.0x | 正常速度 |
| 1.25x | 1.25 倍速 |
| 1.5x | 1.5 倍速 |
| 2.0x | 2 倍速 |

### 信号处理

```python
def on_rate_changed(self, rate: float):
    """处理倍速变化"""
    self.player_card.set_playback_rate(rate)
```

---

## 注意事项

### 按钮状态同步

- 播放/暂停按钮文字需要与播放状态同步
- AB 循环按钮样式需要与循环状态同步
- 倍速下拉框需要与当前倍速同步

### 帧号显示

- 使用等宽字体确保数字对齐
- 帧号格式：`Frame: 123`
- 视频未加载时显示 `Frame: ---`

---

## 依赖

- PySide6: `QToolBar`, `QPushButton`, `QComboBox`, `QLabel`
- chestnut_studio.utils.time_utils: `split_time`
