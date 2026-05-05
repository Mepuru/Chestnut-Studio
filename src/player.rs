use anyhow::Result;
use std::path::Path;

#[cfg(feature = "mpv")]
use libmpv2::Mpv;

/// 视频播放器封装
pub struct VideoPlayer {
    #[cfg(feature = "mpv")]
    mpv: Mpv,
    /// 视频总时长(秒)
    duration: f64,
    /// 帧率
    fps: f64,
    /// 视频宽度
    width: u32,
    /// 视频高度
    height: u32,
}

impl std::fmt::Debug for VideoPlayer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("VideoPlayer")
            .field("duration", &self.duration)
            .field("fps", &self.fps)
            .field("width", &self.width)
            .field("height", &self.height)
            .finish()
    }
}

#[cfg(feature = "mpv")]
impl VideoPlayer {
    /// 创建新的播放器实例
    pub fn new() -> Result<Self> {
        let mpv = Mpv::new()
            .map_err(|e| anyhow::anyhow!("无法创建 mpv 实例: {}", e))?;

        // 配置 mpv 选项（部分选项可能不支持，忽略错误）
        let _ = mpv.set_property("keep-open", true);
        let _ = mpv.set_property("video-sync", "audio");
        let _ = mpv.set_property("hr-seek", "yes");
        let _ = mpv.set_property("input-default-bindings", false);
        let _ = mpv.set_property("input-vo-keyboard", false);

        Ok(Self {
            mpv,
            duration: 0.0,
            fps: 30.0,
            width: 0,
            height: 0,
        })
    }

    /// 加载视频文件
    pub fn load_file(&mut self, path: &Path) -> Result<()> {
        let path_str = path.to_str()
            .ok_or_else(|| anyhow::anyhow!("视频路径包含无效字符"))?;

        self.mpv.command("loadfile", &[path_str])
            .map_err(|e| anyhow::anyhow!("加载视频文件失败: {}", e))?;

        // 等待视频加载完成并获取属性
        std::thread::sleep(std::time::Duration::from_millis(200));

        self.update_properties();

        Ok(())
    }

    /// 更新视频属性
    fn update_properties(&mut self) {
        if let Ok(duration) = self.mpv.get_property::<f64>("duration") {
            self.duration = duration;
        }
        if let Ok(fps) = self.mpv.get_property::<f64>("container-fps") {
            self.fps = fps;
        }
        if let Ok(width) = self.mpv.get_property::<i64>("width") {
            self.width = width as u32;
        }
        if let Ok(height) = self.mpv.get_property::<i64>("height") {
            self.height = height as u32;
        }
    }

    /// 获取当前播放位置(秒)
    pub fn get_position(&self) -> f64 {
        self.mpv.get_property::<f64>("time-pos").unwrap_or(0.0)
    }

    /// 获取当前帧号
    pub fn get_current_frame(&self) -> u64 {
        let pos = self.get_position();
        (pos * self.fps) as u64
    }

    /// 获取视频时长(秒)
    pub fn get_duration(&self) -> f64 {
        self.duration
    }

    /// 获取视频时长(毫秒)
    pub fn get_duration_ms(&self) -> u64 {
        (self.duration * 1000.0) as u64
    }

    /// 获取当前播放位置(毫秒)
    pub fn get_position_ms(&self) -> u64 {
        (self.get_position() * 1000.0) as u64
    }

    /// 获取帧率
    pub fn get_fps(&self) -> f64 {
        self.fps
    }

    /// 获取视频尺寸
    pub fn get_dimensions(&self) -> (u32, u32) {
        (self.width, self.height)
    }

    /// 是否正在播放
    pub fn is_playing(&self) -> bool {
        !self.mpv.get_property::<bool>("pause").unwrap_or(true)
    }

    /// 播放
    pub fn play(&mut self) -> Result<()> {
        self.mpv.set_property("pause", false)
            .map_err(|e| anyhow::anyhow!("设置播放状态失败: {}", e))?;
        Ok(())
    }

    /// 暂停
    pub fn pause(&mut self) -> Result<()> {
        self.mpv.set_property("pause", true)
            .map_err(|e| anyhow::anyhow!("设置暂停状态失败: {}", e))?;
        Ok(())
    }

    /// 切换播放/暂停
    pub fn toggle_play_pause(&mut self) -> Result<()> {
        let is_playing = self.is_playing();
        if is_playing {
            self.pause()?;
        } else {
            self.play()?;
        }
        Ok(())
    }

    /// 精确跳转到指定位置(秒)
    pub fn seek_to(&mut self, time_secs: f64) -> Result<()> {
        self.mpv.command("seek", &[&format!("{:.6}", time_secs), "exact"])
            .map_err(|e| anyhow::anyhow!("跳转失败: {}", e))?;
        Ok(())
    }

    /// 跳转到指定帧
    pub fn seek_to_frame(&mut self, frame: u64) -> Result<()> {
        let time = frame as f64 / self.fps;
        self.seek_to(time)
    }

    /// 前进指定秒数
    pub fn seek_forward(&mut self, secs: f64) -> Result<()> {
        let current = self.get_position();
        let target = (current + secs).min(self.duration).max(0.0);
        self.seek_to(target)
    }

    /// 后退指定秒数
    pub fn seek_backward(&mut self, secs: f64) -> Result<()> {
        let current = self.get_position();
        let target = (current - secs).max(0.0);
        self.seek_to(target)
    }

    /// 前进一帧
    pub fn frame_step(&mut self) -> Result<()> {
        self.mpv.command("frame-step", &[])
            .map_err(|e| anyhow::anyhow!("前进一帧失败: {}", e))?;
        Ok(())
    }

    /// 后退一帧
    pub fn frame_back_step(&mut self) -> Result<()> {
        self.mpv.command("frame-back-step", &[])
            .map_err(|e| anyhow::anyhow!("后退一帧失败: {}", e))?;
        Ok(())
    }

    /// 设置音量 (0-100)
    pub fn set_volume(&mut self, volume: u32) -> Result<()> {
        self.mpv.set_property("volume", volume as i64)
            .map_err(|e| anyhow::anyhow!("设置音量失败: {}", e))?;
        Ok(())
    }

    /// 获取音量
    pub fn get_volume(&self) -> u32 {
        self.mpv.get_property::<i64>("volume").unwrap_or(100) as u32
    }

    /// 设置静音
    pub fn set_mute(&mut self, mute: bool) -> Result<()> {
        self.mpv.set_property("mute", mute)
            .map_err(|e| anyhow::anyhow!("设置静音失败: {}", e))?;
        Ok(())
    }

    /// 是否静音
    pub fn is_muted(&self) -> bool {
        self.mpv.get_property::<bool>("mute").unwrap_or(false)
    }

    /// 设置播放速率
    pub fn set_speed(&mut self, speed: f64) -> Result<()> {
        self.mpv.set_property("speed", speed)
            .map_err(|e| anyhow::anyhow!("设置播放速率失败: {}", e))?;
        Ok(())
    }

    /// 获取播放速率
    pub fn get_speed(&self) -> f64 {
        self.mpv.get_property::<f64>("speed").unwrap_or(1.0)
    }
}

#[cfg(not(feature = "mpv"))]
impl VideoPlayer {
    /// 创建新的播放器实例 (无 mpv 支持)
    pub fn new() -> Result<Self> {
        anyhow::bail!("mpv 功能未启用。请使用 --features mpv 编译以启用视频播放支持。")
    }

    /// 加载视频文件 (无 mpv 支持)
    pub fn load_file(&mut self, _path: &Path) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 获取当前播放位置(秒)
    pub fn get_position(&self) -> f64 {
        0.0
    }

    /// 获取当前帧号
    pub fn get_current_frame(&self) -> u64 {
        0
    }

    /// 获取视频时长(毫秒)
    pub fn get_duration_ms(&self) -> u64 {
        0
    }

    /// 获取当前播放位置(毫秒)
    pub fn get_position_ms(&self) -> u64 {
        0
    }

    /// 获取帧率
    pub fn get_fps(&self) -> f64 {
        30.0
    }

    /// 是否正在播放
    pub fn is_playing(&self) -> bool {
        false
    }

    /// 播放
    pub fn play(&mut self) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 暂停
    pub fn pause(&mut self) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 切换播放/暂停
    pub fn toggle_play_pause(&mut self) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 精确跳转到指定位置(秒)
    pub fn seek_to(&mut self, _time_secs: f64) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 跳转到指定帧
    pub fn seek_to_frame(&mut self, _frame: u64) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 前进指定秒数
    pub fn seek_forward(&mut self, _secs: f64) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 后退指定秒数
    pub fn seek_backward(&mut self, _secs: f64) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 前进一帧
    pub fn frame_step(&mut self) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 后退一帧
    pub fn frame_back_step(&mut self) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 设置音量 (0-100)
    pub fn set_volume(&mut self, _volume: u32) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 设置静音
    pub fn set_mute(&mut self, _mute: bool) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }

    /// 设置播放速率
    pub fn set_speed(&mut self, _speed: f64) -> Result<()> {
        anyhow::bail!("mpv 功能未启用")
    }
}

/// 将时间(秒)转换为帧号
pub fn time_to_frame(time_secs: f64, fps: f64) -> u64 {
    (time_secs * fps) as u64
}

/// 将帧号转换为时间(秒)
pub fn frame_to_time(frame: u64, fps: f64) -> f64 {
    frame as f64 / fps
}

/// 格式化时间显示 (MM:SS.ms)
pub fn format_time(time_secs: f64) -> String {
    let mins = (time_secs / 60.0) as u64;
    let secs = time_secs % 60.0;
    format!("{:02}:{:05.2}", mins, secs)
}

/// 格式化时间显示 (HH:MM:SS)
pub fn format_time_hms(time_secs: f64) -> String {
    let total_secs = time_secs as u64;
    let hours = total_secs / 3600;
    let mins = (total_secs % 3600) / 60;
    let secs = total_secs % 60;
    format!("{:02}:{:02}:{:02}", hours, mins, secs)
}
