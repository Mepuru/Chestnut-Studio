"""音频数据处理

提供波形加载、包络计算、人声增强等功能。
"""

import wave

import numpy as np


def load_waveform(wav_path: str, vocal_enhance: bool = True) -> tuple[list[float], list[int]]:
    """加载 WAV 文件，返回波形数据

    Args:
        wav_path: WAV 文件路径
        vocal_enhance: 是否启用人声增强（立体声时提取中心声道，单声道时带通滤波）

    Returns:
        (time_list, amplitude_list)
        - time_list: 时间轴 (ms)
        - amplitude_list: 振幅值 (int16)
    """
    with wave.open(wav_path, "rb") as f:
        params = f.getparams()
        nchannels, _, framerate, nframes = params[:4]
        str_data = f.readframes(nframes)

    w = np.frombuffer(str_data, dtype=np.int16)

    if nchannels == 2 and vocal_enhance:
        # 立体声：提取中心声道（人声通常在中心）
        # 中心声道 = (左声道 + 右声道) / 2 - (左声道 - 右声道) * 0.5
        # 简化版：直接用左右声道的差异部分（背景音乐通常在两侧）
        w = np.reshape(w, [nframes, 2])
        left = w[:, 0].astype(np.float32)
        right = w[:, 1].astype(np.float32)

        # 方法：提取中心声道（人声）= 左右声道的共同部分
        # 同时减去两侧声道（背景音乐）
        center = (left + right) / 2  # 中心部分
        sides = (left - right) / 2   # 两侧部分（背景）

        # 人声增强：加强中心，减弱两侧
        vocal = center - sides * 0.5
        vocal = np.clip(vocal, -32768, 32767).astype(np.int16)
        amplitude_list = list(map(int, vocal))
    elif nchannels > 1:
        w = np.reshape(w, [nframes, nchannels])
        amplitude_list = list(map(int, w[:, 0]))
    else:
        amplitude_list = list(map(int, w))

    # 单声道或处理后：应用带通滤波增强人声
    if vocal_enhance:
        amplitude_list = _bandpass_vocal(amplitude_list, framerate)

    time_list = [x * 1000 / framerate for x in range(nframes)]

    return time_list, amplitude_list


def _bandpass_vocal(amplitude: list[int], sample_rate: int) -> list[int]:
    """带通滤波，保留人声频率范围 (200Hz - 4kHz)

    人声的主要频率范围：
    - 男声：85Hz - 180Hz（基频）+ 泛音到 4kHz
    - 女声：165Hz - 255Hz（基频）+ 泛音到 4kHz
    - 保留 200Hz-4kHz 可以很好地保留人声，去除低频噪音和高频嘶声

    Args:
        amplitude: 振幅列表
        sample_rate: 采样率

    Returns:
        滤波后的振幅列表
    """
    arr = np.array(amplitude, dtype=np.float32)

    # 如果采样率太低，跳过滤波
    if sample_rate < 1000:
        return amplitude

    # 使用简单的移动平均来近似低通/高通滤波
    # 这不是真正的带通滤波，但计算快，效果还可以接受

    # 低通滤波（去除高频，截止约 4kHz）
    # 对于 1kHz 采样率，奈奎斯特频率是 500Hz，已经很低了
    # 所以我们主要做高通滤波（去除低频噪音）

    # 高通滤波：去除低于 200Hz 的成分
    # 使用简单的差分近似
    if sample_rate >= 1000:
        # 计算窗口大小（对应约 200Hz 的周期）
        window = max(int(sample_rate / 200), 2)
        kernel = np.ones(window) / window
        low_freq = np.convolve(arr, kernel, mode="same")
        # 减去低频成分
        arr = arr - low_freq * 0.7

    # 归一化到原始范围
    max_val = np.max(np.abs(arr))
    if max_val > 0:
        arr = arr / max_val * 32767

    return list(map(int, np.clip(arr, -32768, 32767)))


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
    smoothed = np.convolve(arr, kernel, mode="same")
    return smoothed.tolist()


def compute_envelope(amplitude: list[int], window: int = 50) -> tuple[list[float], list[float]]:
    """计算音频包络线（优化版本）

    使用滑动窗口最大值提取峰值包络，效果更明显。

    Args:
        amplitude: 原始振幅值列表
        window: 平滑窗口大小（采样点数）
                采样率 1kHz 时，window=50 约 50ms

    Returns:
        (upper_envelope, lower_envelope)
        - upper_envelope: 上包络线（正值）
        - lower_envelope: 下包络线（负值）
    """
    arr = np.array(amplitude, dtype=np.float32)

    # 取绝对值
    abs_arr = np.abs(arr)

    # 使用滑动窗口最大值（比平均值更能提取峰值）
    n = len(abs_arr)
    envelope = np.zeros(n, dtype=np.float32)

    # 优化：用步进方式计算最大值
    half_win = window // 2
    for i in range(n):
        start = max(0, i - half_win)
        end = min(n, i + half_win + 1)
        envelope[i] = np.max(abs_arr[start:end])

    # 轻微平滑（消除毛刺）
    smooth_kernel = np.ones(3) / 3
    envelope = np.convolve(envelope, smooth_kernel, mode="same")

    # 生成上下包络
    upper = envelope.tolist()
    lower = (-envelope).tolist()

    return upper, lower


def compute_envelope_fast(amplitude: list[int], window: int = 50, target_points: int = 5000) -> tuple[list[float], list[float]]:
    """快速计算音频包络线（下采样版本）

    对于长音频，先下采样再计算包络，大幅提升性能。

    Args:
        amplitude: 原始振幅值列表
        window: 平滑窗口大小（采样点数）
        target_points: 目标数据点数（下采样后的点数）

    Returns:
        (upper_envelope, lower_envelope)
        - upper_envelope: 上包络线（正值）
        - lower_envelope: 下包络线（负值）
    """
    arr = np.array(amplitude, dtype=np.float32)
    n = len(arr)

    # 如果数据点不多，直接用原方法
    if n <= target_points * 2:
        return compute_envelope(amplitude, window)

    # 下采样：每个采样窗口取最大值
    step = n // target_points
    downsampled = np.zeros(target_points, dtype=np.float32)

    for i in range(target_points):
        start = i * step
        end = min(start + step, n)
        downsampled[i] = np.max(np.abs(arr[start:end]))

    # 平滑
    smooth_window = max(window // step, 3)
    smooth_kernel = np.ones(smooth_window) / smooth_window
    envelope = np.convolve(downsampled, smooth_kernel, mode="same")

    # 生成上下包络
    upper = envelope.tolist()
    lower = (-envelope).tolist()

    return upper, lower


def downsample_waveform(times: list[float], amplitudes: list[int], target_points: int = 5000) -> tuple[list[float], list[float]]:
    """下采样波形数据

    保留峰值特征的同时减少数据点，提升绘图性能。

    Args:
        times: 时间列表 (ms)
        amplitudes: 振幅列表
        target_points: 目标数据点数

    Returns:
        (downsampled_times, downsampled_amplitudes)
    """
    n = len(amplitudes)
    if n <= target_points:
        return times, [float(a) for a in amplitudes]

    step = n // target_points
    new_times = []
    new_amps = []

    arr = np.array(amplitudes, dtype=np.float32)

    for i in range(target_points):
        start = i * step
        end = min(start + step, n)

        # 取时间中点
        mid = (start + end) // 2
        new_times.append(times[mid])

        # 取窗口内的最大绝对值（保留峰值）
        max_idx = start + np.argmax(np.abs(arr[start:end]))
        new_amps.append(float(amplitudes[max_idx]))

    return new_times, new_amps
