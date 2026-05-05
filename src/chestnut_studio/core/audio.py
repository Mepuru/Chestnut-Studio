"""音频数据处理"""

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
    with wave.open(wav_path, "rb") as f:
        params = f.getparams()
        nchannels, _, framerate, nframes = params[:4]
        str_data = f.readframes(nframes)

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
    smoothed = np.convolve(arr, kernel, mode="same")
    return smoothed.tolist()
