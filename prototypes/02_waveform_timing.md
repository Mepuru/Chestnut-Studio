# 波形打轴模块 (手动)

## 1. 模块概述

波形打轴模块是MVP的核心功能，通过Shift+鼠标拖拽在波形区域直接创建字幕轴，实现直观、高效的打轴操作。

## 2. 功能清单

| 功能 | 说明 | 优先级 |
|------|------|--------|
| Shift+左键拖拽 | 在波形上创建新轴 | P0 |
| 拖拽实时预览 | 显示选区范围 | P0 |
| 视频跟随 | 拖拽时视频实时预览 | P0 |
| 右键删除轴 | 右键点击轴区域删除 | P0 |
| 轴颜色区分 | 不同轴使用不同颜色 | P1 |
| 拖拽调整 | 拖拽后可调整边界 | P2 |

## 3. 交互流程

### 3.1 创建轴流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Shift+拖拽打轴流程                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  按住Shift键  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  左键按下     │
                    │  记录起始帧   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  拖拽移动     │
                    │  更新选区     │
                    │  视频跟随预览 │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  释放鼠标     │
                    │  创建新轴     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  添加到轴列表 │
                    │  刷新界面     │
                    └───────────────┘
```

### 3.2 删除轴流程

```
右键点击波形
    ↓
检测点击位置是否在某个轴区域
    ↓
┌─────────────────────────────────┐
│  在轴区域内 → 弹出确认菜单     │
│  不在轴区域 → 无操作           │
└─────────────────────────────────┘
    ↓
确认删除
    ↓
从轴列表移除
    ↓
刷新界面
```

## 4. 数据模型

```rust
/// 波形打轴状态
pub struct WaveformTimingState {
    /// 是否按住Shift键
    pub shift_held: bool,
    /// 拖拽状态
    pub drag_state: DragState,
    /// 临时选区显示
    pub temp_selection: Option<Selection>,
}

/// 拖拽状态
pub enum DragState {
    /// 无拖拽
    None,
    /// 拖拽中
    Dragging {
        /// 起始帧
        start_frame: u64,
        /// 当前帧
        current_frame: u64,
    },
}

/// 选区范围
pub struct Selection {
    /// 起始帧
    pub start_frame: u64,
    /// 结束帧
    pub end_frame: u64,
}
```

## 5. 核心算法

### 5.1 帧号计算

```rust
/// 根据鼠标X坐标计算帧号
fn x_to_frame(x: f32, bounds: &Rectangle, waveform: &WaveformData) -> u64 {
    let relative_x = (x - bounds.x) / bounds.width;
    let frame = (relative_x * waveform.total_frames as f64) as u64;
    frame.max(0).min(waveform.total_frames - 1)
}

/// 根据帧号计算X坐标
fn frame_to_x(frame: u64, bounds: &Rectangle, waveform: &WaveformData) -> f32 {
    let relative_x = frame as f64 / waveform.total_frames as f64;
    bounds.x + (relative_x * bounds.width as f64) as f32
}
```

### 5.2 重叠检测

```rust
/// 检测帧位置是否在某个轴区域内
fn find_axis_at_frame(frame: u64, axes: &[Axis]) -> Option<u64> {
    for axis in axes {
        for segment in &axis.segments {
            if frame >= segment.start_frame && frame < segment.end_frame {
                return Some(axis.id);
            }
        }
    }
    None
}

/// 检测新选区是否与现有轴重叠
fn check_overlap(new_start: u64, new_end: u64, axes: &[Axis]) -> bool {
    for axis in axes {
        for segment in &axis.segments {
            if new_start < segment.end_frame && new_end > segment.start_frame {
                return true;
            }
        }
    }
    false
}
```

### 5.3 创建轴

```rust
/// 创建新轴
fn create_axis(
    start_frame: u64,
    end_frame: u64,
    axes: &mut Vec<Axis>,
    next_id: &mut u64,
) -> Axis {
    let axis = Axis {
        id: *next_id,
        index: axes.len() + 1,
        name: format!("轴{}", axes.len() + 1),
        color: get_axis_color(axes.len()),
        locked: false,
        segments: vec![Segment {
            id: *next_id,
            start_frame,
            end_frame,
            text: String::new(),
        }],
    };
    *next_id += 1;
    axes.push(axis.clone());
    axis
}

/// 获取轴颜色 (循环使用)
fn get_axis_color(index: usize) -> Color {
    const COLORS: [Color; 8] = [
        Color::from_rgb(0.2, 0.6, 0.8),  // 蓝色
        Color::from_rgb(0.8, 0.4, 0.2),  // 橙色
        Color::from_rgb(0.2, 0.8, 0.4),  // 绿色
        Color::from_rgb(0.8, 0.2, 0.6),  // 粉色
        Color::from_rgb(0.6, 0.4, 0.8),  // 紫色
        Color::from_rgb(0.8, 0.8, 0.2),  // 黄色
        Color::from_rgb(0.2, 0.8, 0.8),  // 青色
        Color::from_rgb(0.8, 0.2, 0.2),  // 红色
    ];
    COLORS[index % COLORS.len()]
}
```

## 6. 波形绘制 (Canvas)

```rust
impl canvas::Program<Message> for WaveformCanvas {
    fn draw(
        &self,
        bounds: Rectangle,
        cursor: Cursor,
    ) -> Vec<Geometry> {
        let frame = Frame::new(bounds.size());
        
        // 1. 绘制背景
        frame.fill_rectangle(
            Point::ORIGIN,
            bounds.size(),
            Color::from_rgb(0.14, 0.14, 0.14),
        );
        
        // 2. 绘制波形
        if let Some(waveform) = &self.waveform {
            for i in 0..waveform.amplitudes.len() {
                let x = frame_to_x(i as u64, &bounds, waveform);
                let y = map_amplitude(waveform.amplitudes[i]);
                frame.fill_rectangle(
                    Rectangle::new(Point::new(x, y), Size::new(1.0, 1.0)),
                    Color::from_rgb(0.8, 0.8, 0.8),
                );
            }
        }
        
        // 3. 绘制现有轴区域
        for axis in &self.axes {
            for segment in &axis.segments {
                let x = frame_to_x(segment.start_frame, &bounds, waveform);
                let width = frame_to_x(segment.end_frame, &bounds, waveform) - x;
                frame.fill_rectangle(
                    Rectangle::new(Point::new(x, 0.0), Size::new(width, bounds.height)),
                    axis.color.scale_alpha(0.3),
                );
            }
        }
        
        // 4. 绘制临时选区 (拖拽中)
        if let DragState::Dragging { start_frame, current_frame } = &self.drag_state {
            let x1 = frame_to_x(*start_frame, &bounds, waveform);
            let x2 = frame_to_x(*current_frame, &bounds, waveform);
            let (left, right) = if x1 < x2 { (x1, x2) } else { (x2, x1) };
            frame.fill_rectangle(
                Rectangle::new(Point::new(left, 0.0), Size::new(right - left, bounds.height)),
                Color::from_rgba(1.0, 1.0, 1.0, 0.2),
            );
        }
        
        // 5. 绘制播放位置线
        let cursor_x = frame_to_x(self.current_frame, &bounds, waveform);
        frame.fill_rectangle(
            Rectangle::new(Point::new(cursor_x - 1.0, 0.0), Size::new(2.0, bounds.height)),
            Color::from_rgb(0.85, 0.24, 0.19),
        );
        
        vec![frame.into_geometry()]
    }
}
```

## 7. 消息处理

```rust
/// 处理波形鼠标事件
fn handle_waveform_event(
    state: &mut AppState,
    event: WaveformEvent,
) -> Option<Message> {
    match event {
        WaveformEvent::MouseDown { x, button, modifiers } => {
            if modifiers.shift && button == MouseButton::Left {
                // Shift+左键: 开始拖拽
                let frame = x_to_frame(x, &state.bounds, &state.waveform);
                state.drag_state = DragState::Dragging {
                    start_frame: frame,
                    current_frame: frame,
                };
                Some(Message::WaveformMouseDown { frame })
            } else if button == MouseButton::Right {
                // 右键: 检测是否在轴区域
                let frame = x_to_frame(x, &state.bounds, &state.waveform);
                if let Some(axis_id) = find_axis_at_frame(frame, &state.axes) {
                    Some(Message::WaveformRightClick { frame })
                } else {
                    None
                }
            } else {
                None
            }
        }
        
        WaveformEvent::MouseMove { x } => {
            if let DragState::Dragging { start_frame, .. } = &mut state.drag_state {
                let frame = x_to_frame(x, &state.bounds, &state.waveform);
                state.drag_state = DragState::Dragging {
                    start_frame: *start_frame,
                    current_frame: frame,
                };
                // 更新视频预览位置
                Some(Message::SeekTo(frame))
            } else {
                None
            }
        }
        
        WaveformEvent::MouseUp { x, button } => {
            if button == MouseButton::Left {
                if let DragState::Dragging { start_frame, current_frame } = &state.drag_state {
                    let (min_frame, max_frame) = if start_frame < current_frame {
                        (start_frame, current_frame)
                    } else {
                        (current_frame, start_frame)
                    };
                    
                    // 最小长度检查 (至少10帧)
                    if max_frame - min_frame >= 10 {
                        state.drag_state = DragState::None;
                        Some(Message::CreateAxis { start_frame: min_frame, end_frame: max_frame })
                    } else {
                        state.drag_state = DragState::None;
                        None
                    }
                } else {
                    None
                }
            } else {
                None
            }
        }
    }
}
```

## 8. 快捷键

| 快捷键 | 功能 |
|--------|------|
| Shift | 进入打轴模式 (按住) |
| Shift+左键拖拽 | 创建新轴 |
| 右键 | 删除轴 (在轴区域内) |

## 9. 与原版差异

| 功能 | DD_KaoRou2 (AI打轴) | MVP (手动打轴) |
|------|---------------------|----------------|
| 打轴方式 | AI自动识别人声 | Shift+拖拽手动创建 |
| 精度 | 依赖AI算法 | 用户精确控制 |
| 速度 | 自动批量 | 手动逐条 |
| 依赖 | Spleeter/TensorFlow | 无额外依赖 |
| 适用场景 | 长视频批量处理 | 精确短片段打轴 |
