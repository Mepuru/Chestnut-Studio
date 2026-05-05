use anyhow::Result;
use std::path::Path;

use crate::decoder::{VideoDecoder, VideoFrame};

/// 视频播放器封装
pub struct VideoPlayer {
    decoder: Option<VideoDecoder>,
    /// 当前播放位置(毫秒)
    position_ms: u64,
    /// 是否正在播放
    is_playing: bool,
    /// 音量 (0-100)
    volume: u32,
    /// 是否静音
    is_muted: bool,
    /// 播放速率
    speed: f64,
}

impl std::fmt::Debug for VideoPlayer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("VideoPlayer")
            .field("has_decoder", &self.decoder.is_some())
            .field("position_ms", &self.position_ms)
            .field("is_playing", &self.is_playing)
            .field("volume", &self.volume)
            .finish()
    }
}

impl VideoPlayer {
    /// 创建新的播放器实例
    pub fn new() -> Result<Self> {
        Ok(Self {
            decoder: None,
            position_ms: 0,
            is_playing: false,
            volume: 100,
            is_muted: false,
            speed: 1.0,
        })
    }

    /// 加载视频文件
    pub fn load_file(&mut self, path: &Path) -> Result<()> {
        let decoder = VideoDecoder::new(path)?;
        self.decoder = Some(decoder);
        self.position_ms = 0;
        self.is_playing = false;
        Ok(())
    }

    /// 获取当前帧数据
    pub fn current_frame(&self) -> Option<VideoFrame> {
        self.decoder.as_ref()?.current_frame_data()
    }

    /// 获取视频宽度
    pub fn width(&self) -> u32 {
        self.decoder.as_ref().map(|d| d.width()).unwrap_or(0)
    }

    /// 获取视频高度
    pub fn height(&self) -> u32 {
        self.decoder.as_ref().map(|d| d.height()).unwrap_or(0)
    }

    /// 获取帧率
    pub fn get_fps(&self) -> f64 {
        self.decoder.as_ref().map(|d| d.fps()).unwrap_or(30.0)
    }

    /// 获取视频时长(毫秒)
    pub fn get_duration_ms(&self) -> u64 {
        self.decoder.as_ref().map(|d| (d.duration() * 1000.0) as u64).unwrap_or(0)
    }

    /// 获取当前播放位置(毫秒)
    pub fn get_position_ms(&self) -> u64 {
        self.position_ms
    }

    /// 获取当前帧号
    pub fn get_current_frame(&self) -> u64 {
        self.decoder.as_ref().map(|d| d.current_frame_number()).unwrap_or(0)
    }

    /// 是否正在播放
    pub fn is_playing(&self) -> bool {
        self.is_playing
    }

    /// 播放
    pub fn play(&mut self) -> Result<()> {
        if let Some(ref mut decoder) = self.decoder {
            decoder.play()?;
            self.is_playing = true;
        }
        Ok(())
    }

    /// 暂停
    pub fn pause(&mut self) {
        if let Some(ref mut decoder) = self.decoder {
            decoder.pause();
            self.is_playing = false;
        }
    }

    /// 切换播放/暂停
    pub fn toggle_play_pause(&mut self) -> Result<()> {
        if self.is_playing {
            self.pause();
        } else {
            self.play()?;
        }
        Ok(())
    }

    /// 跳转到指定帧
    pub fn seek_to_frame(&mut self, frame: u64) -> Result<()> {
        if let Some(ref mut decoder) = self.decoder {
            decoder.seek_to_frame(frame)?;
            self.position_ms = (frame as f64 / decoder.fps() * 1000.0) as u64;
        }
        Ok(())
    }

    /// 跳转到指定时间（秒）
    pub fn seek_to_time(&mut self, time: f64) -> Result<()> {
        if let Some(ref mut decoder) = self.decoder {
            decoder.seek_to_time(time)?;
            self.position_ms = (time * 1000.0) as u64;
        }
        Ok(())
    }

    /// 前进指定秒数
    pub fn seek_forward(&mut self, secs: f64) -> Result<()> {
        if let Some(ref mut decoder) = self.decoder {
            let current_frame = decoder.current_frame_number();
            let fps = decoder.fps();
            let target_frame = current_frame + (secs * fps) as u64;
            decoder.seek_to_frame(target_frame)?;
        }
        Ok(())
    }

    /// 后退指定秒数
    pub fn seek_backward(&mut self, secs: f64) -> Result<()> {
        if let Some(ref mut decoder) = self.decoder {
            let current_frame = decoder.current_frame_number();
            let fps = decoder.fps();
            let target_frame = if current_frame > (secs * fps) as u64 {
                current_frame - (secs * fps) as u64
            } else {
                0
            };
            decoder.seek_to_frame(target_frame)?;
        }
        Ok(())
    }

    /// 前进一帧
    pub fn frame_step(&mut self) -> Result<()> {
        let current = self.get_current_frame();
        self.seek_to_frame(current + 1)
    }

    /// 后退一帧
    pub fn frame_back_step(&mut self) -> Result<()> {
        let current = self.get_current_frame();
        if current > 0 {
            self.seek_to_frame(current - 1)
        } else {
            Ok(())
        }
    }

    /// 设置音量 (0-100)
    pub fn set_volume(&mut self, volume: u32) {
        self.volume = volume.min(100);
    }

    /// 获取音量
    pub fn get_volume(&self) -> u32 {
        self.volume
    }

    /// 设置静音
    pub fn set_mute(&mut self, mute: bool) {
        self.is_muted = mute;
    }

    /// 是否静音
    pub fn is_muted(&self) -> bool {
        self.is_muted
    }

    /// 设置播放速率
    pub fn set_speed(&mut self, speed: f64) {
        self.speed = speed;
    }

    /// 获取播放速率
    pub fn get_speed(&self) -> f64 {
        self.speed
    }
}

/// 格式化时间显示 (HH:MM:SS)
pub fn format_time_hms(time_secs: f64) -> String {
    let total_secs = time_secs as u64;
    let hours = total_secs / 3600;
    let mins = (total_secs % 3600) / 60;
    let secs = total_secs % 60;
    format!("{:02}:{:02}:{:02}", hours, mins, secs)
}
