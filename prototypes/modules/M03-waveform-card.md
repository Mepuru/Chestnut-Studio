# M03 — 音频波形卡片

> `src/ui/cards/waveform_card.py`　｜　Phase 2　｜　波形显示 + 交互

---

## 职责

- 显示主音轨波形曲线
- 波形上叠加字幕条覆盖（半透明色块）
- 红色时间线跟随播放位置
- 点击波形跳转到对应时间
- 视窗跟随播放位置滑动

---

## 类设计

```python
class WaveformCard(QDockWidget):
    """音频波形卡片"""
    
    # 信号
    position_clicked = Signal(int)  # 点击波形，跳转到指定时间 (ms)
    
    def __init__(self, parent=None):
        super().__init__("波形图", parent)
        self._time_data = []        # 时间轴数据 (ms)
        self._wave_data = []        # 波形振幅数据
        self._duration = 0          # 视频总时长 (ms)
        self._current_pos = 0       # 当前播放位置 (ms)
        self._global_interval = 33  # 当前间隔 (ms)
        self._setup_ui()
    
    def _setup_ui(self):
        """初始化 UI"""
        # pyqtgraph PlotWidget
        # 波形曲线 PlotCurveItem
        # 红线 InfiniteLine
        # 字幕覆盖层 PlotCurveItem[]
        ...
    
    def load_waveform(self, time_data: list, wave_data: list):
        """加载波形数据"""
        self._time_data = time_data
        self._wave_data = wave_data
        self._duration = time_data[-1] if time_data else 0
        self._plot_waveform()
    
    def update_position(self, position: int):
        """更新播放位置，刷新红线和视窗"""
        self._current_pos = position
        self._update_red_line()
        self._update_view_range()
    
    def update_subtitle_overlay(self, subtitle_dict: dict):
        """更新字幕条覆盖显示"""
        self._clear_subtitle_overlay()
        self._draw_subtitle_overlay(subtitle_dict)
    
    def _plot_waveform(self):
        """绘制波形曲线"""
        ...
    
    def _update_red_line(self):
        """更新红线位置"""
        self._red_line.setValue(self._current_pos)
    
    def _update_view_range(self):
        """更新视窗范围（跟随播放位置）"""
        # 显示当前位置 ± N个间隔 的范围
        left = self._current_pos - self._red_line_left * self._global_interval
        right = self._current_pos + self._red_line_right * self._global_interval
        self._plot_widget.setXRange(left, right, padding=0)
    
    def mousePressEvent(self, event):
        """点击波形跳转"""
        if event.button() == Qt.LeftButton:
            pos = self._plot_widget.plotItem.vb.mapSceneToView(event.pos())
            ms = int(pos.x())
            if 0 <= ms <= self._duration:
                self.position_clicked.emit(ms)
```

---

## 内部组件

| 组件 | 类型 | 说明 |
|------|------|------|
| `_plot_widget` | PlotWidget | pyqtgraph 绑图容器 |
| `_wave_plot` | PlotCurveItem | 波形曲线 |
| `_red_line` | InfiniteLine | 红色时间线 |
| `_subtitle_plots` | list[PlotCurveItem] | 字幕条覆盖（5列×N条） |

---

## 数据来源

```python
# src/core/ffmpeg.py
def extract_audio(video_path: str, output_path: str) -> bool:
    """从视频提取音轨并降采样"""
    cmd = ['ffmpeg', '-y', '-i', video_path, '-vn', '-ar', '1000', output_path]
    ...

# src/core/audio.py
def load_waveform(wav_path: str) -> tuple[list, list]:
    """加载 WAV 文件，返回 (time_list, amplitude_list)"""
    f = wave.open(wav_path, 'rb')
    params = f.getparams()
    nchannels, _, framerate, nframes = params[:4]
    str_data = f.readframes(nframes)
    f.close()
    w = np.frombuffer(str_data, dtype=np.int16)
    w = np.reshape(w, [nframes, nchannels])
    time_list = [x * 1000 / framerate for x in range(nframes)]
    wave_list = list(map(int, w[:, 0]))
    return time_list, wave_list
```

---

## 刷新机制

| 定时器 | 周期 | 用途 |
|--------|------|------|
| `graphTimer` | 33ms (30FPS) | 刷新红线位置 + 视窗滑动 |

---

## 视窗参数

```python
# 红线在视窗中的位置（百分比）
RED_LINE_LEFT = 50   # 左侧显示 50% 区间
RED_LINE_RIGHT = 50  # 右侧显示 50% 区间
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| pyqtgraph | 波形绘制 |
| numpy | 数据处理 |
| wave (标准库) | WAV 文件读取 |
| src/core/ffmpeg.py | 音轨提取 |
| src/core/audio.py | 波形数据加载 |
