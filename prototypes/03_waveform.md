# 音频波形模块

## 1. 模块概述

音频波形模块负责显示视频的音频波形，包括主音轨波形和AI分离后的人声/背景声波形。波形图支持交互操作，可用于定位和打轴。

## 2. 功能清单

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 主音轨波形 | 显示原始视频音频波形 | P0 |
| 人声波形 | 显示AI分离的人声波形 | P1 |
| 背景声波形 | 显示AI分离的背景声波形 | P1 |
| 播放位置指示 | 红色竖线显示当前播放位置 | P0 |
| 字幕轴叠加 | 在波形上显示字幕时间段 | P0 |
| 波形缩放 | 支持时间轴缩放 | P2 |
| 点击跳转 | 点击波形跳转到对应时间 | P1 |
| 右键菜单 | 导出音频文件 | P2 |

## 3. 数据模型

```rust
/// 波形数据
pub struct WaveformData {
    /// 时间点列表(毫秒)
    pub timestamps: Vec<u64>,
    /// 振幅值列表
    pub amplitudes: Vec<i16>,
    /// 采样率
    pub sample_rate: u32,
}

/// 波形显示状态
pub struct WaveformState {
    /// 主音轨波形数据
    pub main_wave: Option<WaveformData>,
    /// 人声波形数据
    pub vocal_wave: Option<WaveformData>,
    /// 背景声波形数据
    pub bgm_wave: Option<WaveformData>,
    /// 平滑波形数据(用于显示)
    pub smooth_wave: Option<Vec<f64>>,
    /// 当前显示的波形类型
    pub display_type: WaveformType,
    /// 时间轴缩放系数
    pub scale: f64,
    /// 时间轴偏移量
    pub offset: f64,
    /// Y轴范围
    pub y_range: (f64, f64),
}

/// 波形类型
pub enum WaveformType {
    /// 主音轨
    Main,
    /// 人声
    Vocal,
    /// 背景声
    Bgm,
}
```

## 4. 波形生成流程

```
┌─────────────────────────────────────────────────────────────┐
│                    波形生成流程                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  读取视频文件 │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  ffmpeg提取   │
                    │  音频为WAV    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  降采样处理   │
                    │  (1000Hz)     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  计算峰值     │
                    │  每ms一个点   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  平滑处理     │
                    │  移动平均     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  缓存数据     │
                    └───────────────┘
```

## 5. 核心算法

### 5.1 波形提取

```python
# 使用ffmpeg提取音频并降采样
cmd = ['ffmpeg', '-y', '-i', video_path, '-vn', '-ar', '1000', output.wav]
# 1000Hz采样率 = 每毫秒一个样本点

# 读取WAV文件
f = wave.open(audio_path, 'rb')
params = f.getparams()
nchannels, _, framerate, nframes = params[:4]
strData = f.readframes(nframes)
wave = np.fromstring(strData, dtype=np.int16)
```

### 5.2 波形平滑

```python
# 移动平均平滑 (窗口大小11)
wave_smooth = wave[:5]
for i in range(5, len(wave) - 5):
    wave_smooth.append(np.mean(wave[i-5:i+6]))
wave_smooth += wave[-5:]
```

### 5.3 光谱衰减计算

```python
# librosa计算光谱衰减
x, sr = librosa.load(audio_path, sr=None)
spectral_rolloffs = librosa.feature.spectral_rolloff(x + 0.1, sr=sr)[0]

# 插值到毫秒级
frames = range(len(spectral_rolloffs))
t = list(map(lambda x: x * 500, librosa.frames_to_time(frames)))
rolloffs_vocal = np.interp(list(range(len(timestamps))), t, spectral_rolloffs)
```

## 6. 波形绘制

### 6.1 绘制参数

```rust
/// 波形绘制配置
pub struct WaveformStyle {
    /// 背景色
    pub background: Color,
    /// 波形颜色
    pub wave_color: Color,
    /// 人声颜色
    pub vocal_color: Color,
    /// 背景声颜色
    pub bgm_color: Color,
    /// 字幕轴颜色(半透明)
    pub subtitle_brush: Color,
    /// 播放位置线颜色
    pub cursor_color: Color,
    /// 播放位置线宽度
    pub cursor_width: f32,
}
```

### 6.2 Iced Canvas绘制

```rust
impl canvas::Program<WaveformMessage> for WaveformCanvas {
    fn draw(
        &self,
        bounds: Rectangle,
        cursor: Cursor,
    ) -> Vec<Geometry> {
        let frame = Frame::new(bounds.size());
        
        // 1. 绘制背景
        frame.fill_rectangle(
            Point::ORIGIN,
            bounds.size(),
            self.style.background,
        );
        
        // 2. 绘制波形
        for i in 0..self.data.len() - 1 {
            let x = map_time_to_x(self.timestamps[i]);
            let y = map_amplitude_to_y(self.amplitudes[i]);
            let next_x = map_time_to_x(self.timestamps[i + 1]);
            let next_y = map_amplitude_to_y(self.amplitudes[i + 1]);
            
            frame.fill_rectangle(
                Rectangle::new(Point::new(x, 0.0), Size::new(1.0, y.abs())),
                self.style.wave_color,
            );
        }
        
        // 3. 绘制字幕轴叠加
        for segment in &self.subtitle_segments {
            let x = map_time_to_x(segment.start_ms);
            let width = map_duration_to_width(segment.duration_ms);
            frame.fill_rectangle(
                Rectangle::new(Point::new(x, 0.0), Size::new(width, bounds.height)),
                self.style.subtitle_brush,
            );
        }
        
        // 4. 绘制播放位置线
        let cursor_x = map_time_to_x(self.current_time);
        frame.fill_rectangle(
            Rectangle::new(
                Point::new(cursor_x - self.style.cursor_width / 2.0, 0.0),
                Size::new(self.style.cursor_width, bounds.height),
            ),
            self.style.cursor_color,
        );
        
        vec![frame.into_geometry()]
    }
}
```

## 7. 交互消息

```rust
pub enum WaveformMessage {
    /// 更新波形数据
    UpdateWaveform(WaveformData),
    /// 更新人声波形
    UpdateVocalWave(WaveformData),
    /// 更新背景声波形
    UpdateBgmWave(WaveformData),
    /// 鼠标点击(跳转到时间)
    Click(f64),
    /// 鼠标右键
    RightClick(f64),
    /// 鼠标拖拽开始
    DragStart(f64),
    /// 鼠标拖拽移动
    DragMove(f64),
    /// 鼠标拖拽结束
    DragEnd(f64),
    /// 切换显示波形类型
    SwitchType(WaveformType),
    /// 缩放
    Zoom(f64),
}
```

## 8. 与字幕轴的联动

```rust
// 根据当前字幕数据计算叠加显示
fn calculate_subtitle_overlay(subtitle_dict: &SubtitleDict) -> Vec<SubtitleOverlay> {
    let mut overlays = Vec::new();
    
    for (col, subtitles) in subtitle_dict.iter() {
        for (start, (duration, _)) in subtitles {
            overlays.push(SubtitleOverlay {
                column: *col,
                start_ms: *start,
                end_ms: start + duration,
                color: get_column_color(*col),
            });
        }
    }
    
    overlays
}
```

## 9. 性能优化

### 9.1 数据降采样

```rust
// 屏幕像素级降采样
fn downsample_for_display(data: &[f64], pixel_width: usize) -> Vec<f64> {
    let samples_per_pixel = data.len() / pixel_width;
    let mut result = Vec::with_capacity(pixel_width);
    
    for i in 0..pixel_width {
        let start = i * samples_per_pixel;
        let end = start + samples_per_pixel;
        let max = data[start..end].iter().fold(f64::MIN, |a, &b| a.max(b));
        result.push(max);
    }
    
    result
}
```

### 9.2 可见区域裁剪

```rust
// 只绘制可见区域的波形
fn get_visible_range(&self, bounds: Rectangle) -> (usize, usize) {
    let start_time = self.offset;
    let end_time = self.offset + bounds.width / self.scale;
    let start_idx = self.timestamps.partition_point(|&t| t < start_time as u64);
    let end_idx = self.timestamps.partition_point(|&t| t < end_time as u64);
    (start_idx, end_idx)
}
```

## 10. 与原版差异

| 功能 | DD_KaoRou2 (pyqtgraph) | Rust方案 (Iced Canvas) |
|------|------------------------|------------------------|
| 绑图库 | pyqtgraph | Iced Canvas |
| 数据格式 | numpy数组 | Vec<f64> |
| 交互 | 鼠标信号槽 | 事件驱动消息 |
| 性能 | C++底层 | Rust零开销 |
| 定制性 | 受限于pyqtgraph | 完全自定义 |
