use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::path::Path;
use std::process::Command;
use std::sync::{Arc, Mutex};
use std::thread;

/// 音频播放器
pub struct AudioPlayer {
    /// 是否正在播放
    is_playing: Arc<Mutex<bool>>,
    /// 音频线程句柄
    audio_thread: Option<thread::JoinHandle<()>>,
    /// 当前播放位置（秒）
    position: Arc<Mutex<f64>>,
}

impl std::fmt::Debug for AudioPlayer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("AudioPlayer")
            .field("is_playing", &self.is_playing())
            .finish()
    }
}

impl AudioPlayer {
    /// 创建新的音频播放器
    pub fn new() -> Self {
        Self {
            is_playing: Arc::new(Mutex::new(false)),
            audio_thread: None,
            position: Arc::new(Mutex::new(0.0)),
        }
    }

    /// 是否正在播放
    pub fn is_playing(&self) -> bool {
        *self.is_playing.lock().unwrap_or_else(|e| e.into_inner())
    }

    /// 获取当前播放位置（秒）
    pub fn position(&self) -> f64 {
        *self.position.lock().unwrap()
    }

    /// 开始播放音频
    pub fn play(&mut self, path: &Path, start_time: f64) -> Result<()> {
        if self.is_playing() {
            return Ok(());
        }

        *self.is_playing.lock().unwrap() = true;

        let path = path.to_path_buf();
        let is_playing = self.is_playing.clone();
        let position = self.position.clone();

        let handle = thread::spawn(move || {
            if let Err(e) = Self::audio_thread(&path, start_time, is_playing, position) {
                tracing::error!("音频播放线程错误: {}", e);
            }
        });

        self.audio_thread = Some(handle);

        Ok(())
    }

    /// 暂停播放
    pub fn pause(&mut self) {
        *self.is_playing.lock().unwrap() = false;
    }

    /// 音频播放线程
    fn audio_thread(
        path: &Path,
        start_time: f64,
        is_playing: Arc<Mutex<bool>>,
        position: Arc<Mutex<f64>>,
    ) -> Result<()> {
        // 使用 ffmpeg 解码音频并输出到 stdout
        let mut child = Command::new("ffmpeg")
            .args([
                "-ss", &format!("{:.6}", start_time),
                "-i", path.to_str().unwrap(),
                "-f", "f32le",
                "-acodec", "pcm_f32le",
                "-ar", "44100",
                "-ac", "2",
                "-",
            ])
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::null())
            .spawn()
            .context("启动 ffmpeg 音频解码失败")?;

        let stdout = child.stdout.take().unwrap();

        // 初始化音频输出
        let host = cpal::default_host();
        let device = host.default_output_device()
            .ok_or_else(|| anyhow::anyhow!("找不到音频输出设备"))?;

        let config = cpal::StreamConfig {
            channels: 2,
            sample_rate: 44100,
            buffer_size: cpal::BufferSize::Default,
        };

        let is_playing_clone = is_playing.clone();
        let position_clone = position.clone();

        // 创建音频流
        let stream = device.build_output_stream(
            &config,
            move |data: &mut [f32], _: &cpal::OutputCallbackInfo| {
                // 这里需要从ffmpeg读取数据填充到data中
                // 简单实现：填充静音
                for sample in data.iter_mut() {
                    *sample = 0.0;
                }
            },
            |err| {
                tracing::error!("音频流错误: {}", err);
            },
            None,
        )?;

        stream.play()?;

        // 读取ffmpeg输出并播放
        use std::io::Read;
        let mut reader = std::io::BufReader::new(stdout);
        let mut buffer = vec![0u8; 4096];

        while is_playing.lock().unwrap_or_else(|e| e.into_inner()).clone() {
            match reader.read(&mut buffer) {
                Ok(0) => break,
                Ok(_) => {
                    // 更新位置
                    // 这里简化处理，实际需要根据读取的样本数计算
                    let mut pos = position.lock().unwrap();
                    *pos += 4096.0 / (44100.0 * 4.0); // 假设16位立体声
                }
                Err(_) => break,
            }
        }

        let _ = child.kill();

        Ok(())
    }
}

impl Drop for AudioPlayer {
    fn drop(&mut self) {
        *self.is_playing.lock().unwrap() = false;
        if let Some(handle) = self.audio_thread.take() {
            let _ = handle.join();
        }
    }
}
