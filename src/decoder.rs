use anyhow::{Context, Result};
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

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

/// 视频解码器 - 使用 ffmpeg 命令行
pub struct VideoDecoder {
    /// 视频文件路径
    path: PathBuf,
    /// 视频信息
    info: VideoInfo,
    /// 当前帧号（共享状态）
    current_frame: Arc<Mutex<u64>>,
    /// 当前帧数据
    current_frame_data: Arc<Mutex<Option<VideoFrame>>>,
    /// 是否正在播放（共享状态）
    is_playing: Arc<Mutex<bool>>,
    /// 解码线程句柄
    decode_thread: Option<thread::JoinHandle<()>>,
    /// 当前 ffmpeg 子进程
    current_process: Arc<Mutex<Option<Child>>>,
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
        // 获取视频信息
        let info = Self::get_video_info(path)?;
        
        Ok(Self {
            path: path.to_path_buf(),
            info,
            current_frame: Arc::new(Mutex::new(0)),
            current_frame_data: Arc::new(Mutex::new(None)),
            is_playing: Arc::new(Mutex::new(false)),
            decode_thread: None,
            current_process: Arc::new(Mutex::new(None)),
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
        
        // 查找视频流
        let streams = json["streams"].as_array()
            .ok_or_else(|| anyhow::anyhow!("找不到视频流"))?;
        
        let video_stream = streams.iter()
            .find(|s| s["codec_type"].as_str() == Some("video"))
            .ok_or_else(|| anyhow::anyhow!("找不到视频流"))?;
        
        let width = video_stream["width"].as_u64().unwrap_or(0) as u32;
        let height = video_stream["height"].as_u64().unwrap_or(0) as u32;
        
        // 解析帧率
        let fps_str = video_stream["r_frame_rate"].as_str().unwrap_or("30/1");
        let fps_parts: Vec<&str> = fps_str.split('/').collect();
        let fps = if fps_parts.len() == 2 {
            let num: f64 = fps_parts[0].parse().unwrap_or(30.0);
            let den: f64 = fps_parts[1].parse().unwrap_or(1.0);
            num / den
        } else {
            30.0
        };
        
        // 获取时长
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
        *self.is_playing.lock().unwrap_or_else(|e| e.into_inner())
    }
    
    /// 停止当前播放
    fn stop_playback(&self) {
        // 设置停止标志
        *self.is_playing.lock().unwrap() = false;
        
        // 杀死当前进程
        if let Ok(mut process) = self.current_process.lock() {
            if let Some(mut child) = process.take() {
                let _ = child.kill();
            }
        }
    }
    
    /// 跳转到指定帧
    pub fn seek_to_frame(&mut self, frame: u64) -> Result<()> {
        let was_playing = self.is_playing();
        
        // 停止当前播放
        self.stop_playback();
        
        // 等待播放线程结束
        if let Some(handle) = self.decode_thread.take() {
            let _ = handle.join();
        }
        
        // 边界检查
        let max_frame = self.info.total_frames.saturating_sub(1);
        let target_frame = frame.min(max_frame);
        
        // 更新当前帧号
        *self.current_frame.lock().unwrap() = target_frame;
        
        // 提取单帧
        self.extract_frame(target_frame)?;
        
        // 如果之前在播放，重新开始播放
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
    
    /// 提取指定帧
    fn extract_frame(&mut self, frame_number: u64) -> Result<()> {
        let timestamp = frame_number as f64 / self.info.fps;
        
        // 使用 ffmpeg 提取单帧到 stdout
        let output = Command::new("ffmpeg")
            .args([
                "-ss", &format!("{:.6}", timestamp),
                "-i", self.path.to_str().unwrap(),
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
        
        // 验证数据大小
        let expected_size = (self.info.width * self.info.height * 4) as usize;
        if data.len() != expected_size {
            anyhow::bail!("帧数据大小不匹配: 期望 {}, 实际 {}", expected_size, data.len());
        }
        
        let frame = VideoFrame {
            data,
            width: self.info.width,
            height: self.info.height,
            frame_number,
        };
        
        if let Ok(mut current) = self.current_frame_data.lock() {
            *current = Some(frame);
        }
        
        Ok(())
    }
    
    /// 开始播放
    pub fn play(&mut self) -> Result<()> {
        if self.is_playing() {
            return Ok(());
        }
        
        // 停止之前的播放（如果有）
        self.stop_playback();
        if let Some(handle) = self.decode_thread.take() {
            let _ = handle.join();
        }
        
        *self.is_playing.lock().unwrap() = true;
        
        let path = self.path.clone();
        let fps = self.info.fps;
        let frame_data = self.current_frame_data.clone();
        let current_frame = self.current_frame.clone();
        let is_playing = self.is_playing.clone();
        let width = self.info.width;
        let height = self.info.height;
        let process_handle = self.current_process.clone();
        
        // 启动解码线程
        let handle = thread::spawn(move || {
            if let Err(e) = Self::playback_thread(
                &path, fps, frame_data, current_frame, is_playing, width, height, process_handle
            ) {
                tracing::error!("视频播放线程错误: {}", e);
            }
        });
        
        self.decode_thread = Some(handle);
        
        Ok(())
    }
    
    /// 暂停播放
    pub fn pause(&mut self) {
        self.stop_playback();
    }
    
    /// 播放线程函数
    fn playback_thread(
        path: &Path,
        fps: f64,
        frame_data: Arc<Mutex<Option<VideoFrame>>>,
        current_frame: Arc<Mutex<u64>>,
        is_playing: Arc<Mutex<bool>>,
        width: u32,
        height: u32,
        process_handle: Arc<Mutex<Option<Child>>>,
    ) -> Result<()> {
        let frame_duration = Duration::from_secs_f64(1.0 / fps);
        let start_frame = *current_frame.lock().unwrap();
        
        // 使用 ffmpeg 持续输出帧
        let mut child = Command::new("ffmpeg")
            .args([
                "-ss", &format!("{:.6}", start_frame as f64 / fps),
                "-i", path.to_str().unwrap(),
                "-f", "rawvideo",
                "-pix_fmt", "rgba",
                "-",
            ])
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::null())
            .spawn()
            .context("启动 ffmpeg 播放失败")?;
        
        // 保存进程句柄
        if let Ok(mut process) = process_handle.lock() {
            *process = Some(child);
        }
        
        // 获取 stdout
        let stdout = if let Ok(mut process) = process_handle.lock() {
            if let Some(ref mut child) = *process {
                child.stdout.take()
            } else {
                None
            }
        } else {
            None
        };
        
        let stdout = stdout.ok_or_else(|| anyhow::anyhow!("无法获取 ffmpeg stdout"))?;
        
        use std::io::Read;
        let mut reader = std::io::BufReader::new(stdout);
        
        let frame_size = (width * height * 4) as usize;
        let mut buffer = vec![0u8; frame_size];
        let mut frame_num = start_frame;
        
        while is_playing.lock().unwrap_or_else(|e| e.into_inner()).clone() {
            match reader.read_exact(&mut buffer) {
                Ok(_) => {
                    let frame = VideoFrame {
                        data: buffer.clone(),
                        width,
                        height,
                        frame_number: frame_num,
                    };
                    
                    if let Ok(mut data) = frame_data.lock() {
                        *data = Some(frame);
                    }
                    
                    // 更新共享的帧号
                    if let Ok(mut cf) = current_frame.lock() {
                        *cf = frame_num;
                    }
                    
                    frame_num += 1;
                    
                    // 控制帧率
                    thread::sleep(frame_duration);
                }
                Err(_) => break,
            }
        }
        
        // 清理进程
        if let Ok(mut process) = process_handle.lock() {
            if let Some(mut child) = process.take() {
                let _ = child.kill();
            }
        }
        
        Ok(())
    }
}

impl Drop for VideoDecoder {
    fn drop(&mut self) {
        self.stop_playback();
        if let Some(handle) = self.decode_thread.take() {
            let _ = handle.join();
        }
    }
}
