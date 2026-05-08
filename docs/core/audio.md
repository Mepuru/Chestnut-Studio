# 音频处理

> `chestnut_studio/core/audio.py`
> 加载 WAV 文件并提供波形数据，用于波形图显示。

---

## 职责

- 加载 WAV 文件并解析音频数据
- 计算音频包络线（上下包络）
- 支持人声增强（立体声提取中心声道，单声道高通滤波）
- 波形下采样和数据压缩

---

## 函数列表

### load_waveform

加载波形数据，返回时间和振幅列表。

```python
def load_waveform(wav_path: str, vocal_enhance: bool = False) -> tuple[list[float], list[int]]:
    """加载波形数据
    
    Args:
        wav_path: WAV 文件路径
        vocal_enhance: 是否启用人声增强
        
    Returns:
        (time_list, amplitude_list)
        - time_list: 毫秒时间轴（1kHz 采样率时每 1ms 一个点）
        - amplitude_list: int16 振幅值（取第一个声道）
    """
```

**用法示例：**

```python
from chestnut_studio.core.audio import load_waveform

# 基本加载
times, amps = load_waveform("output.wav")
# times: [0.0, 1.0, 2.0, ...] (ms)
# amps: [123, -456, 789, ...] (int16 振幅)

# 启用人声增强
times, amps = load_waveform("output.wav", vocal_enhance=True)
```

---

### smooth_waveform

平滑波形曲线，减少噪点。

```python
def smooth_waveform(amplitude: list[float], window: int = 10) -> list[float]:
    """平滑波形曲线
    
    Args:
        amplitude: 振幅列表
        window: 滑动平均窗口大小
        
    Returns:
        平滑后的振幅列表
    """
```

**用法示例：**

```python
from chestnut_studio.core.audio import smooth_waveform

smoothed = smooth_waveform(amps, window=10)
```

---

### compute_envelope

计算音频包络线（上下包络）。

```python
def compute_envelope(amplitude: list[float], window: int = 50) -> tuple[list[float], list[float]]:
    """计算音频包络线
    
    Args:
        amplitude: 振幅列表
        window: 滑动窗口大小（采样率 1kHz 时，50 约对应 50ms）
        
    Returns:
        (upper, lower)
        - upper: 上包络（正值）
        - lower: 下包络（负值）
    """
```

**用法示例：**

```python
from chestnut_studio.core.audio import compute_envelope

upper, lower = compute_envelope(amps, window=50)
# upper: [0.0, 123.5, 456.2, ...] (上包络，正值)
# lower: [0.0, -123.5, -456.2, ...] (下包络，负值)
```

---

### compute_envelope_fast

快速计算包络线（下采样版本，适用于长音频）。

```python
def compute_envelope_fast(
    amplitude: list[float], 
    window: int = 50, 
    target_points: int = 5000
) -> tuple[list[float], list[float]]:
    """快速计算包络线
    
    Args:
        amplitude: 振幅列表
        window: 滑动窗口大小
        target_points: 目标点数（自动下采样）
        
    Returns:
        (upper, lower)
    """
```

**用法示例：**

```python
from chestnut_studio.core.audio import compute_envelope_fast

# 适用于长音频，自动下采样到 5000 点
upper, lower = compute_envelope_fast(amps, window=50, target_points=5000)
```

---

### downsample_waveform

下采样波形数据，保留峰值特征。

```python
def downsample_waveform(
    times: list[float], 
    amplitudes: list[float], 
    target_points: int = 5000
) -> tuple[list[float], list[float]]:
    """下采样波形数据
    
    Args:
        times: 时间列表
        amplitudes: 振幅列表
        target_points: 目标点数
        
    Returns:
        (times, amps) 下采样后的数据
    """
```

**用法示例：**

```python
from chestnut_studio.core.audio import downsample_waveform

ds_times, ds_amps = downsample_waveform(times, amps, target_points=5000)
```

---

## 人声增强算法

### 立体声

提取中心声道，抑制两侧背景音乐：

```python
center = (L + R) / 2
side = (L - R) / 2
enhanced = center - side * 0.5
```

### 单声道

高通滤波去除低于 200Hz 的低频噪音：

```python
# 使用 scipy.signal.butter 设计高通滤波器
# 截止频率 200Hz，采样率 1kHz
```

---

## 数据格式

| 字段 | 类型 | 说明 |
|------|------|------|
| `time_list` | `list[float]` | 毫秒时间轴，与采样率对应（1kHz → 每 1ms 一个点） |
| `amplitude_list` | `list[int]` | int16 振幅值，取第一个声道 |

---

## 性能考虑

### 下采样策略

- `compute_envelope_fast` 先下采样再计算，适用于长音频
- `downsample_waveform` 保留峰值特征的同时减少数据点
- 默认目标点数 5000，在绘图性能和细节之间取得平衡

### 内存使用

- 1kHz 采样率时，1 分钟音频约 60,000 个数据点
- 下采样后约 5,000 个数据点，内存占用减少 90%

---

## 依赖

- Python 标准库：`wave`, `struct`
- numpy（用于数组操作）
- scipy（可选，用于高通滤波）
