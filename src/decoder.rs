use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

/// 视频帧数据
#[derive(Debug, Clone)]
pub struct VideoFrame {
    /// RGBA 像素数据
    pub data: Vec<u8>,
    /// 宽度
    pub width: u32,
    /// 高度
    pub height: u32,
    /// 帧号
    pub frame_number: u64,
}

/// 视频信息
#[derive(Debug, Clone)]
pub struct VideoInfo {
    /// 宽度
    pub width: u32,
    /// 高度
    pub height: u32,
    /// 帧率
    pub fps: f64,
    /// 总时长（秒）
    pub duration: f64,
    /// 总帧数
    pub total_frames: u64,
}

/// 播放器状态
#[derive(Debug, Clone, PartialEq)]
enum PlaybackState {
    Stopped,
    Playing,
    Paused,
}

/// 统一的音视频解码器
pub struct VideoDecoder {
    /// 视频文件路径
    path: PathBuf,
    /// 视频信息
    info: VideoInfo,
    /// 当前帧号（共享状态）
    current_frame: Arc<Mutex<u64>>,
    /// 当前帧数据
    current_frame_data: Arc<Mutex<Option<VideoFrame>>>,
    /// 播放状态
    state: Arc<Mutex<PlaybackState>>,
    /// 视频播放线程句柄
    video_thread: Option<thread::JoinHandle<()>>,
    /// 音频播放线程句柄
    audio_thread: Option<thread::JoinHandle<()>>,
    /// 音频流
    audio_stream: Option<cpal::Stream>,
    /// 音频缓冲区
    audio_buffer: Arc<Mutex<Vec<f32>>>,
    /// 暂停时的帧号
    pause_frame: Arc<Mutex<u64>>,
}

impl std::fmt::Debug for VideoDecoder {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("VideoDecoder")
            .field("path", &self.path)
            .field("info", &self.info)
            .finish()
    }
}

impl VideoDecoder {
    /// 创建新的视频解码器
    pub fn new(path: &Path) -> Result<Self> {
        let info = Self::get_video_info(path)?;
        
        Ok(Self {
            path: path.to_path_buf(),
            info,
            current_frame: Arc::new(Mutex::new(0)),
            current_frame_data: Arc::new(Mutex::new(None)),
            state: Arc::new(Mutex::new(PlaybackState::Stopped)),
            video_thread: None,
            audio_thread: None,
            audio_stream: None,
            audio_buffer: Arc::new(Mutex::new(Vec::new())),
            pause_frame: Arc::new(Mutex::new(0)),
        })
    }
    
    /// 获取视频信息
    fn get_video_info(path: &Path) -> Result<VideoInfo> {
        let output = Command::new("ffprobe")
            .args([
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                path.to_str().unwrap(),
            ])
            .output()
            .context("执行 ffprobe 失败，请确保已安装 ffmpeg")?;
        
        if !output.status.success() {
            anyhow::bail!("ffprobe 执行失败: {}", String::from_utf8_lossy(&output.stderr));
        }
        
        let json_str = String::from_utf8(output.stdout)?;
        let json: serde_json::Value = serde_json::from_str(&json_str)?;
        
        let streams = json["streams"].as_array()
            .ok_or_else(|| anyhow::anyhow!("找不到视频流"))?;
        
        let video_stream = streams.iter()
            .find(|s| s["codec_type"].as_str() == Some("video"))
            .ok_or_else(|| anyhow::anyhow!("找不到视频流"))?;
        
        let width = video_stream["width"].as_u64().unwrap_or(0) as u32;
        let height = video_stream["height"].as_u64().unwrap_or(0) as u32;
        
        let fps_str = video_stream["r_frame_rate"].as_str().unwrap_or("30/1");
        let fps_parts: Vec<&str> = fps_str.split('/').collect();
        let fps = if fps_parts.len() == 2 {
            let num: f64 = fps_parts[0].parse().unwrap_or(30.0);
            let den: f64 = fps_parts[1].parse().unwrap_or(1.0);
            num / den
        } else {
            30.0
        };
        
        let duration = json["format"]["duration"]
            .as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .unwrap_or(0.0);
        
        let total_frames = (duration * fps) as u64;
        
        Ok(VideoInfo {
            width,
            height,
            fps,
            duration,
            total_frames,
        })
    }
    
    /// 获取视频宽度
    pub fn width(&self) -> u32 {
        self.info.width
    }
    
    /// 获取视频高度
    pub fn height(&self) -> u32 {
        self.info.height
    }
    
    /// 获取帧率
    pub fn fps(&self) -> f64 {
        self.info.fps
    }
    
    /// 获取总时长（秒）
    pub fn duration(&self) -> f64 {
        self.info.duration
    }
    
    /// 获取总帧数
    pub fn total_frames(&self) -> u64 {
        self.info.total_frames
    }
    
    /// 获取当前帧号
    pub fn current_frame_number(&self) -> u64 {
        *self.current_frame.lock().unwrap()
    }
    
    /// 获取当前帧数据
    pub fn current_frame_data(&self) -> Option<VideoFrame> {
        self.current_frame_data.lock().ok()?.clone()
    }
    
    /// 是否正在播放
    pub fn is_playing(&self) -> bool {
        *self.state.lock().unwrap() == PlaybackState::Playing
    }
    
    /// 停止当前播放
    fn stop_playback(&self) {
        *self.state.lock().unwrap() = PlaybackState::Stopped;
    }
    
    /// 提取指定帧（用于seek操作）
    fn extract_frame(&self, frame_number: u64) -> Result<()> {
        let timestamp = frame_number as f64 / self.info.fps;
        
        // 降低分辨率到640像素宽
        let scale_width = 640;
        let scale_height = (self.info.height as f64 * scale_width as f64 / self.info.width as f64) as u32;
        let scale_height = if scale_height % 2 == 0 { scale_height } else { scale_height + 1 };
        
        let output = Command::new("ffmpeg")
            .args([
                "-ss", &format!("{:.6}", timestamp),
                "-i", self.path.to_str().unwrap(),
                "-vf", &format!("scale={}:{}", scale_width, scale_height),
                "-vframes", "1",
                "-f", "rawvideo",
                "-pix_fmt", "rgba",
                "-",
            ])
            .output()
            .context("执行 ffmpeg 失败")?;
        
        if !output.status.success() {
            anyhow::bail!("ffmpeg 执行失败: {}", String::from_utf8_lossy(&output.stderr));
        }
        
        let data = output.stdout;
        let expected_size = (scale_width * scale_height * 4) as usize;
        
        if data.len() != expected_size {
            // 填充黑色帧
            let mut black_frame = vec![0u8; expected_size];
            for i in (3..expected_size).step_by(4) {
                black_frame[i] = 255;
            }
            
            let frame = VideoFrame {
                data: black_frame,
                width: scale_width,
                height: scale_height,
                frame_number,
            };
            
            if let Ok(mut current) = self.current_frame_data.lock() {
                *current = Some(frame);
            }
            
            return Ok(());
        }
        
        let frame = VideoFrame {
            data,
            width: scale_width,
            height: scale_height,
            frame_number,
        };
        
        if let Ok(mut current) = self.current_frame_data.lock() {
            *current = Some(frame);
        }
        
        Ok(())
    }
    
    /// 跳转到指定帧
    pub fn seek_to_frame(&mut self, frame: u64) -> Result<()> {
        let was_playing = self.is_playing();
        
        // 停止当前播放
        if was_playing {
            self.stop_playback();
            if let Some(handle) = self.video_thread.take() {
                let _ = handle.join();
            }
            if let Some(handle) = self.audio_thread.take() {
                let _ = handle.join();
            }
        }
        
        // 边界检查
        let max_frame = self.info.total_frames.saturating_sub(1);
        let target_frame = frame.min(max_frame);
        
        // 更新当前帧号
        *self.current_frame.lock().unwrap() = target_frame;
        *self.pause_frame.lock().unwrap() = target_frame;
        
        // 提取单帧
        self.extract_frame(target_frame)?;
        
        // 如果之前在播放，从新位置继续播放
        if was_playing {
            self.play()?;
        }
        
        Ok(())
    }
    
    /// 跳转到指定时间（秒）
    pub fn seek_to_time(&mut self, time: f64) -> Result<()> {
        let frame = (time * self.info.fps) as u64;
        self.seek_to_frame(frame)
    }
    
    /// 开始播放
    pub fn play(&mut self) -> Result<()> {
        if self.is_playing() {
            return Ok(());
        }
        
        // 停止之前的播放
        self.stop_playback();
        if let Some(handle) = self.video_thread.take() {
            let _ = handle.join();
        }
        if let Some(handle) = self.audio_thread.take() {
            let _ = handle.join();
        }
        
        *self.state.lock().unwrap() = PlaybackState::Playing;
        
        let path = self.path.clone();
        let fps = self.info.fps;
        let width = self.info.width;
        let height = self.info.height;
        let frame_data = self.current_frame_data.clone();
        let current_frame = self.current_frame.clone();
        let state = self.state.clone();
        let audio_buffer = self.audio_buffer.clone();
        let start_frame = self.current_frame_number();
        
        // 初始化音频
        self.init_audio()?;
        
        // 启动视频播放线程
        let video_handle = thread::spawn(move || {
            if let Err(e) = Self::video_playback_thread(
                &path, fps, width, height, frame_data, current_frame, 
                state.clone(), start_frame
            ) {
                tracing::error!("视频播放线程错误: {}", e);
            }
        });
        
        // 启动音频播放线程
        let path = self.path.clone();
        let state = self.state.clone();
        let audio_buffer = self.audio_buffer.clone();
        let start_time = start_frame as f64 / fps;
        
        let audio_handle = thread::spawn(move || {
            if let Err(e) = Self::audio_playback_thread(
                &path, state, audio_buffer, start_time
            ) {
                tracing::error!("音频播放线程错误: {}", e);
            }
        });
        
        self.video_thread = Some(video_handle);
        self.audio_thread = Some(audio_handle);
        
        Ok(())
    }
    
    /// 初始化音频输出
    fn init_audio(&mut self) -> Result<()> {
        let host = cpal::default_host();
        let device = host.default_output_device()
            .ok_or_else(|| anyhow::anyhow!("找不到音频输出设备"))?;
        
        let config = cpal::StreamConfig {
            channels: 2,
            sample_rate: 44100,
            buffer_size: cpal::BufferSize::Default,
        };
        
        let audio_buffer = self.audio_buffer.clone();
        
        let stream = device.build_output_stream(
            &config,
            move |data: &mut [f32], _: &cpal::OutputCallbackInfo| {
                let mut buffer = audio_buffer.lock().unwrap();
                for sample in data.iter_mut() {
                    if !buffer.is_empty() {
                        *sample = buffer.remove(0);
                    } else {
                        *sample = 0.0;
                    }
                }
            },
            |err| {
                tracing::error!("音频流错误: {}", err);
            },
            None,
        )?;
        
        stream.play()?;
        self.audio_stream = Some(stream);
        
        Ok(())
    }
    
    /// 暂停播放
    pub fn pause(&mut self) {
        if self.is_playing() {
            *self.state.lock().unwrap() = PlaybackState::Paused;
            *self.pause_frame.lock().unwrap() = self.current_frame_number();
            self.stop_playback();
        }
    }
    
    /// 视频播放线程
    fn video_playback_thread(
        path: &Path,
        fps: f64,
        width: u32,
        height: u32,
        frame_data: Arc<Mutex<Option<VideoFrame>>>,
        current_frame: Arc<Mutex<u64>>,
        state: Arc<Mutex<PlaybackState>>,
        start_frame: u64,
    ) -> Result<()> {
        let frame_duration = Duration::from_secs_f64(1.0 / fps);
        
        // 降低分辨率到640像素宽，保持宽高比
        let scale_width = 640;
        let scale_height = (height as f64 * scale_width as f64 / width as f64) as u32;
        let scale_height = if scale_height % 2 == 0 { scale_height } else { scale_height + 1 };
        
        let video_frame_size = (scale_width * scale_height * 4) as usize;
        
        // 使用 ffmpeg 解码视频，降低分辨率提高性能
        let mut child = Command::new("ffmpeg")
            .args([
                "-ss", &format!("{:.6}", start_frame as f64 / fps),
                "-i", path.to_str().unwrap(),
                "-vf", &format!("scale={}:{}", scale_width, scale_height),
                "-f", "rawvideo",
                "-pix_fmt", "rgba",
                "-r", &format!("{}", fps),
                "-",
            ])
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .context("启动 ffmpeg 视频解码失败")?;
        
        let stdout = child.stdout.take().unwrap();
        let mut reader = std::io::BufReader::with_capacity(video_frame_size * 2, stdout);
        let mut video_buffer = vec![0u8; video_frame_size];
        
        let mut frame_num = start_frame;
        let mut last_frame_time = Instant::now();
        
        loop {
            // 检查播放状态
            if *state.lock().unwrap() != PlaybackState::Playing {
                break;
            }
            
            // 读取视频帧
            match reader.read_exact(&mut video_buffer) {
                Ok(_) => {
                    let frame = VideoFrame {
                        data: video_buffer.clone(),
                        width: scale_width,
                        height: scale_height,
                        frame_number: frame_num,
                    };
                    
                    if let Ok(mut data) = frame_data.lock() {
                        *data = Some(frame);
                    }
                    
                    if let Ok(mut cf) = current_frame.lock() {
                        *cf = frame_num;
                    }
                    
                    frame_num += 1;
                    
                    // 精确帧率控制
                    let elapsed = last_frame_time.elapsed();
                    if elapsed < frame_duration {
                        thread::sleep(frame_duration - elapsed);
                    }
                    last_frame_time = Instant::now();
                }
                Err(_) => break,
            }
        }
        
        let _ = child.kill();
        
        Ok(())
    }
    
    /// 音频播放线程
    fn audio_playback_thread(
        path: &Path,
        state: Arc<Mutex<PlaybackState>>,
        audio_buffer: Arc<Mutex<Vec<f32>>>,
        start_time: f64,
    ) -> Result<()> {
        // 使用 ffmpeg 解码音频
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
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .context("启动 ffmpeg 音频解码失败")?;
        
        let stdout = child.stdout.take().unwrap();
        let mut reader = std::io::BufReader::with_capacity(44100 * 4 * 2, stdout);
        let mut audio_buffer_temp = vec![0u8; 44100 * 4 * 2 / 30]; // 约1帧的音频数据
        
        loop {
            // 检查播放状态
            if *state.lock().unwrap() != PlaybackState::Playing {
                break;
            }
            
            // 检查音频缓冲区大小，避免缓冲区过大导致延迟
            let buffer_size = audio_buffer.lock().unwrap().len();
            if buffer_size > 44100 * 2 * 2 { // 最多缓冲0.5秒的音频
                thread::sleep(Duration::from_millis(10));
                continue;
            }
            
            // 读取音频数据
            match reader.read(&mut audio_buffer_temp) {
                Ok(0) => break,
                Ok(n) => {
                    // 将音频数据转换为f32并添加到缓冲区
                    let samples: Vec<f32> = audio_buffer_temp[..n]
                        .chunks_exact(4)
                        .map(|chunk| {
                            let bytes = [chunk[0], chunk[1], chunk[2], chunk[3]];
                            f32::from_le_bytes(bytes)
                        })
                        .collect();
                    
                    if let Ok(mut buffer) = audio_buffer.lock() {
                        buffer.extend_from_slice(&samples);
                    }
                }
                Err(_) => break,
            }
        }
        
        let _ = child.kill();
        
        Ok(())
    }
}

impl Drop for VideoDecoder {
    fn drop(&mut self) {
        self.stop_playback();
        if let Some(handle) = self.video_thread.take() {
            let _ = handle.join();
        }
        if let Some(handle) = self.audio_thread.take() {
            let _ = handle.join();
        }
    }
}
