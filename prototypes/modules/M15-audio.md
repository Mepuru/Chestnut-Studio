# M15 — 音频数据处理

> `chestnut_studio/core/audio.py`　｜　Phase 2　｜　纯逻辑，无 UI 依赖
> **注意：部分函数尚未实现（get_waveform_range）**

---

## 职责

- 加载 WAV 文件为 numpy 数组
- 波形数据处理（降采样、平滑）

---

## 函数列表

```python
import wave
import numpy as np

def load_waveform(wav_path: str) -> tuple[list[float], list[int]]:
    """加载 WAV 文件，返回波形数据
    
    Args:
        wav_path: WAV 文件路径
        
    Returns:
        (time_list, amplitude_list)
        - time_list: 时间轴 (ms)
        - amplitude_list: 振幅值 (int16)
    """
    f = wave.open(wav_path, 'rb')
    params = f.getparams()
    nchannels, _, framerate, nframes = params[:4]
    str_data = f.readframes(nframes)
    f.close()
    
    w = np.frombuffer(str_data, dtype=np.int16)
    w = np.reshape(w, [nframes, nchannels])
    
    time_list = [x * 1000 / framerate for x in range(nframes)]
    amplitude_list = list(map(int, w[:, 0]))
    
    return time_list, amplitude_list


def smooth_waveform(amplitude: list[int], window: int = 10) -> list[float]:
    """平滑波形曲线
    
    Args:
        amplitude: 原始振幅
        window: 窗口大小
        
    Returns:
        平滑后的振幅
    """
    arr = np.array(amplitude, dtype=float)
    kernel = np.ones(window) / window
    smoothed = np.convolve(arr, kernel, mode='same')
    return smoothed.tolist()


def get_waveform_range(time_list: list[float], amplitude_list: list[int],
                       center_ms: float, left_ms: float, right_ms: float,
                       step: int = 1) -> tuple[list[float], list[int]]:
    """获取指定范围的波形数据
    
    Args:
        time_list: 完整时间轴
        amplitude_list: 完整振幅
        center_ms: 中心时间点 (ms)
        left_ms: 左侧范围 (ms)
        right_ms: 右侧范围 (ms)
        step: 采样步长
        
    Returns:
        (time_slice, amplitude_slice)
    """
    start_ms = center_ms - left_ms
    end_ms = center_ms + right_ms
    
    start_idx = max(0, int(start_ms))
    end_idx = min(len(time_list), int(end_ms))
    
    time_slice = time_list[start_idx:end_idx:step]
    amplitude_slice = amplitude_list[start_idx:end_idx:step]
    
    return time_slice, amplitude_slice
```

---

## 测试用例

```python
class TestAudio:
    def test_load_waveform(self):
        # 需要测试用 WAV 文件
        time_list, amp_list = load_waveform("test.wav")
        assert len(time_list) == len(amp_list)
        assert time_list[0] == 0
    
    def test_smooth_waveform(self):
        amp = [0, 100, 0, 100, 0]
        smoothed = smooth_waveform(amp, window=3)
        assert len(smoothed) == len(amp)
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| wave (标准库) | WAV 文件读取 |
| numpy | 数据处理 |
