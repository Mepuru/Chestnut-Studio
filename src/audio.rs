use anyhow::{Context, Result};
use std::path::Path;
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::thread;

/// 音频播放器 - 使用 ffplay 播放音频
pub struct AudioPlayer {
    /// 当前播放进程
    process: Arc<Mutex<Option<Child>>>,
    /// 是否正在播放
    is_playing: Arc<Mutex<bool>>,
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
            process: Arc::new(Mutex::new(None)),
            is_playing: Arc::new(Mutex::new(false)),
        }
    }

    /// 是否正在播放
    pub fn is_playing(&self) -> bool {
        *self.is_playing.lock().unwrap_or_else(|e| e.into_inner())
    }

    /// 开始播放音频
    pub fn play(&mut self, path: &Path, start_time: f64) -> Result<()> {
        if self.is_playing() {
            return Ok(());
        }

        // 停止之前的播放
        self.stop();

        *self.is_playing.lock().unwrap() = true;

        let path = path.to_path_buf();
        let process_handle = self.process.clone();
        let is_playing = self.is_playing.clone();

        // 使用 ffplay 播放音频（无窗口模式）
        let child = Command::new("ffplay")
            .args([
                "-nodisp",           // 不显示视频窗口
                "-autoexit",         // 播放完成后自动退出
                "-ss", &format!("{:.6}", start_time),
                "-i", path.to_str().unwrap(),
            ])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn()
            .context("启动 ffplay 播放失败，请确保已安装 ffmpeg")?;

        if let Ok(mut process) = process_handle.lock() {
            *process = Some(child);
        }

        // 启动监控线程
        let process_handle = self.process.clone();
        let is_playing = self.is_playing.clone();
        
        thread::spawn(move || {
            // 等待进程结束
            loop {
                let should_continue = is_playing.lock().unwrap_or_else(|e| e.into_inner()).clone();
                if !should_continue {
                    break;
                }

                let mut process = process_handle.lock().unwrap();
                if let Some(ref mut child) = *process {
                    match child.try_wait() {
                        Ok(Some(_)) => {
                            // 进程已结束
                            *process = None;
                            *is_playing.lock().unwrap() = false;
                            break;
                        }
                        Ok(None) => {
                            // 进程仍在运行
                            drop(process);
                            thread::sleep(std::time::Duration::from_millis(100));
                        }
                        Err(_) => break,
                    }
                } else {
                    break;
                }
            }
        });

        Ok(())
    }

    /// 暂停播放
    pub fn pause(&mut self) {
        self.stop();
    }

    /// 停止播放
    fn stop(&self) {
        *self.is_playing.lock().unwrap() = false;
        
        if let Ok(mut process) = self.process.lock() {
            if let Some(mut child) = process.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }

    /// 同步播放位置（用于seek操作后）
    pub fn sync_position(&mut self, path: &Path, position: f64) -> Result<()> {
        if self.is_playing() {
            self.play(path, position)?;
        }
        Ok(())
    }
}

impl Drop for AudioPlayer {
    fn drop(&mut self) {
        self.stop();
    }
}
