# 视频打轴与翻译协作平台 —— Iced + mpv 完整技术方案

## 1. 方案概述
本方案采用纯 Rust 技术栈，以 **Iced** 作为原生 GUI 框架，**libmpv** 作为视频后端，构建一个具备帧级精确控制、多面板联动、轴区间编辑与翻译功能的高性能桌面应用。所有模块运行于同一进程，通过中心化状态和确定性消息循环实现高效、低延迟的交互体验。

## 2. 技术栈

| 层次          | 技术选型                                | 说明                                                        |
| ------------- | --------------------------------------- | ----------------------------------------------------------- |
| GUI 框架      | [Iced](https://github.com/iced-rs/iced) | 基于 Elm 架构的模块化原生 GUI，支持复杂弹性布局与自定义绘制 |
| 视频播放      | `mpv` crate (libmpv)                    | 成熟的播放器库，支持 `seek_exact`、`frame_step` 等帧级控制  |
| 窗口嵌入      | `winit` (Iced 依赖)                     | mpv 可渲染到 winit 窗口上，实现视频区域的原生集成           |
| 音频波形      | `ffmpeg-next` 或 `symphonia`            | 从视频中提取音频，计算波形峰值数据                          |
| 自定义绘制    | Iced `Canvas`                           | 绘制音频波形、轴区域色块                                    |
| 轴列表/编辑器 | Iced `List` + `TextInput`               | 高性能虚拟列表显示轴段，支持就地编辑                        |
| 状态管理      | Elm 架构 (Model-View-Update)            | 中心化 `AppState`，明确的消息类型，调试友好                 |
| 持久化        | `serde` + `serde_json` / `ron`          | 项目保存/加载                                               |
| 术语库        | `sled` 或 `rusqlite` (可扩展)           | 目前占位，预留接口                                          |
| 语言          | Rust                                    | 零开销抽象，内存安全                                        |

## 3. 核心数据模型

### 3.1 项目结构
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub media_path: String,
    pub frame_rate: f64,
    pub total_frames: u64,
    pub axes: Vec<Axis>,
    pub translation_axis_ids: Vec<AxisId>,  // 在翻译区显示的轴ID，最多2个
}
```

### 3.2 轴
```rust
pub type AxisId = u64;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Axis {
    pub id: AxisId,
    pub index: usize,           // 自动递增的序号，如 1,2,3...
    pub name: String,           // 自动生成 "轴1"
    pub axis_type: AxisType,
    pub color: Color,           // 使用 Iced 的 Color 类型
    pub locked: bool,
    pub segments: Vec<Segment>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AxisType { Source, Target, Note }
```

### 3.3 片段
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Segment {
    pub id: u64,
    pub start_frame: u64,    // 包含
    pub end_frame: u64,      // 不包含，保证 end_frame > start_frame
    pub text: String,
}
```
**约束**：同一轴内 segments 按 `start_frame` 升序，且 `prev.end_frame <= next.start_frame`，即轴内不重叠。不同轴之间允许任意重叠。

### 3.4 术语库条目
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlossaryEntry {
    pub id: u64,
    pub source_term: String,
    pub target_term: String,
    pub note: Option<String>,
}
```

## 4. 界面布局设计

整个窗口使用 `PaneGrid` 管理面板分割，允许用户拖拽调整大小、拖拽重排、最大化/关闭面板。每个面板是一个独立模块，带有标题栏。

### 4.1 PaneGrid 模块化布局

```
┌─────────────────────────────────────────────────────────────┐
│  菜单栏 (文件 / 视图 / 工具 / 帮助)                           │
├─────────────────────────────────────────────────────────────┤
│  项目工具栏 (视频名 | 时间显示 | 播放控制)                      │
├──────────────────────────────┬──────────────────────────────┤
│  [ 视频播放器 ]     [最大化] │  [ 轴卡片列表 ]       [最大化] │
│  ┌────────────────────────┐  │  ┌────────────────────────┐  │
│  │   (嵌入 mpv 视频)      │  │  │  ┌──┬──┬──┬──┐       │  │
│  │   16:9 自适应          │  │  │  │轴│轴│轴│轴│       │  │
│  └────────────────────────┘  │  │  │1 │2 │3 │4 │       │  │
│  ↔ 拖拽调整左右比例          │  │  └──┴──┴──┴──┘       │  │
│  [ 音频波形 ]        [最大化] │  └────────────────────────┘  │
│  ┌────────────────────────┐  │  [ 翻译区 ]           [最大化] │
│  │  ▁▂▃█▅▇▃▂▁▂▃█▅▇▃▂    │  │  ┌────────────────────────┐  │
│  │  (可缩放/拖选/打轴)    │  │  │  [翻译 | 术语库]       │  │
│  └────────────────────────┘  │  │  可选双轴并排           │  │
│                              │  └────────────────────────┘  │
├──────────────────────────────┴──────────────────────────────┤
│  状态栏                                                      │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 PaneGrid 面板模块

| 面板ID | 名称 | 默认位置 | 可关闭 | 说明 |
|--------|------|----------|--------|------|
| video | 视频播放器 | 左上 | 否 | 嵌入mpv，16:9比例 |
| waveform | 音频波形 | 左下 | 否 | Canvas绘制，支持缩放拖选 |
| axis_cards | 轴卡片列表 | 右上 | 否 | 水平滚动卡片容器 |
| translation | 翻译区 | 右下 | 否 | TAB切换翻译/术语库 |

### 4.3 面板交互

- **拖拽分割线**：调整相邻面板的比例
- **拖拽标题栏**：重排面板位置
- **双击标题栏**：最大化/还原面板
- **右键标题栏**：上下文菜单（重置布局等）
- **视图菜单**：控制面板可见性

### 4.4 字体配置

- 默认使用系统中文字体（Windows: Microsoft YaHei, macOS: PingFang SC）
- 通过 `Font::with_name()` 指定优先字体
- 回退到 iced 内置字体

```
┌──────────────────────────────────────────────┐
│  菜单栏 (文件 / 视图 / 工具 / 帮助)            │
├──────────────────────────────────────────────┤
│  项目工具栏 (视频名 | 时间显示 | ◀5s ⏸️ ▶5s 🔁) │
├──────────────────────┬───────────────────────┤
│  左侧面板             │  右侧面板             │
│ ┌──────────────────┐ │  ┌──────────────────┐ │
│ │  视频区域        │ │  │  轴卡片区 (上)   │ │
│ │  (嵌入 mpv)      │ │  │  水平滚动        │ │
│ │  16:9 自适应     │ │  │  ┌──┬──┬──┬──┐  │ │
│ └──────────────────┘ │  │  │轴│轴│轴│轴│  │ │
│ ┌──────────────────┐ │  │  │1 │2 │3 │4 │  │ │
│ │  音频波形        │ │  │  │..│..│..│..│  │ │
│ │  (可缩放/拖选)   │ │  │  └──┴──┴──┴──┘  │ │
│ └──────────────────┘ │  │  垂直滚动        │ │
│    (分隔条可调高度)  │  └──────────────────┘ │
│                      │  ┌──────────────────┐ │
│                      │  │  翻译区 (下)     │ │
│                      │  │  [翻译｜术语库]  │ │
│                      │  │  可选双轴并排    │ │
│                      │  └──────────────────┘ │
└──────────────────────┴───────────────────────┘
```

- **菜单栏**：文件操作、面板可见性切换、设置。
- **工具栏**：视频文件名、当前时间/总时长（格式 `HH:MM:SS.frame`）、播放控制按钮。
- **左侧面板**：
  - 视频区：固定 16:9 比例，宽度自适应，高度可根据需求与波形区分配。
  - 波形区：显示整个音频波形，支持缩放和时间定位，轴上区域用半透明色块标记。
- **右侧面板**：
  - 轴卡片区：水平滚动容器，并排显示所有轴卡片，每个卡片内部垂直滚动，展示该轴的所有片段条目。
  - 翻译区：TAB 切换翻译工作区和术语库。翻译区双轴模式下左右并排显示两个轴的全部分段，支持文本编辑。

所有面板之间的分割线均可拖拽调整比例。菜单“视图”中可以勾选/取消勾选面板的显示。

## 5. 核心功能详细设计

### 5.1 视频播放与帧级控制

#### 5.1.1 mpv 集成
- 使用 `mpv` crate（通过 `libmpv` 系统库）。
- 配置选项：
  ```rust
  mpv.set_property("keep-open", true)?;
  mpv.set_property("no-osd", true)?;
  mpv.set_property("no-border", true)?;
  mpv.set_property("input-default-bindings", false)?;
  mpv.set_property("video-sync", "audio")?;  // 保持音画同步
  mpv.set_property("hr-seek", "yes")?;       // 高精度 seek
  ```
- 视频嵌入方案：  
  - **推荐**：将 mpv 的输出直接渲染到 Iced 窗口的指定区域。Iced 基于 `winit`，可通过 `MpvHandler::set_wid` 传入窗口句柄。在实际实现中，可以创建一块 `winit::window::Window` 的子区域，或利用 Iced 的 `Canvas` 作为渲染目标（更复杂）。简单方式：使用一个 `container` 并通过 `window_handle` 获取原生窗口 ID，然后调用 `mpv.set_wid(..)`，mpv 会在此区域上覆盖绘制。确保在布局中为该容器预留空间，并跟随调整大小事件更新 mpv 的渲染区域。
- 帧精确 API：
  ```rust
  mpv.command("seek", &[&format!("{:.6}", time_secs), "exact"])?;  // 精确 seek
  mpv.command("frame-step")?;   // 下一帧
  mpv.command("frame-back-step")?; // 上一帧
  ```
- 时间获取：通过 `mpv.get_property("time-pos")` 获得当前播放时间（秒），可换算为帧号。

#### 5.1.2 播放联动
**中心状态**：
```rust
pub struct AppState {
    pub current_frame: u64,       // 当前帧号
    pub is_playing: bool,
    pub is_dragging: bool,        // 用户正在拖拽选区，暂停 Tick 同步
    // ... 其他项目数据
}
```

**消息流**：
- `Tick` 消息：通过 `Application::subscription` 定时产生（每 16ms），在 `update` 中处理：
  ```rust
  Message::Tick => {
      if !self.is_dragging {
          if let Ok(time) = self.mpv.get_property::<f64>("time-pos") {
              self.current_frame = time_to_frame(time, self.project.frame_rate);
          }
      }
  }
  ```
- 用户交互（波形点击、轴卡片点击、工具栏按钮）产生 `Message::SeekTo(frame)` 消息：
  ```rust
  Message::SeekTo(frame) => {
      let time = frame_to_time(frame, self.project.frame_rate);
      self.mpv.command("seek", &[&format!("{:.6}", time), "exact"]).ok();
      self.current_frame = frame;   // 立即更新 UI 状态
  }
  ```
- 播放/暂停切换：`Message::TogglePlayPause` 调用 `mpv.set_property("pause", !self.is_playing)` .

#### 5.1.3 拖拽期间的联动保护
在调用 `Message::DragStart` 时设置 `is_dragging = true`，`Tick` 消息会跳过时间同步。`DragMove` 直接更新 `current_frame` 并 seek mpv。`DragEnd` 后恢复 `is_dragging = false`。

### 5.2 音频波形与打轴

#### 5.2.1 波形生成
- 使用 `ffmpeg-next` 或直接调用系统 `ffmpeg` 提取音频为 PCM (`ffmpeg -i input.mp4 -f s16le -ac 1 -ar 44100 -`)，读取数据并计算峰值数组（每 N 个样本取最大值）。
- 峰值数据保存到项目文件中，避免重复计算。
- 使用 Iced `Canvas` 绘制波形：遍历峰值数组，绘制竖线，支持缩放（调整时间窗口）和平移（滚动条或拖拽）。
- 叠加显示现有轴的 Region：通过 `Frame::fill_rectangle` 在半透明区域绘制轴色彩。

#### 5.2.2 打轴交互 (Shift 修饰)
**进入/退出选区模式**：通过全局键盘事件监听 Shift 键状态，在 `AppState` 中维护 `shift_held` 标志。

**Shift+左键拖选创建轴**：
1. 在波形 Canvas 上监听鼠标事件（`Canvas::on_mouse_down` 等），当 `shift_held && event.button() == Left` 时启动拖拽。
2. `DragStart`：记录起始时间（根据点击位置换算），并创建临时选区显示。
3. `DragMove`：不断更新结束时间，同时调用 `Message::SeekTo` 实时更新视频预览。波形上绘制临时选区矩形。
4. `DragEnd`：获取 `start_frame..end_frame` 范围，调用 `create_axis(start, end)` 方法。
5. `create_axis` 逻辑：
   - 生成新 `Axis`：`id` 自增，`index = axes.len() + 1`，`name = format!("轴{}", index)`，随机颜色，`segments = vec![Segment { ... }]`。
   - 插入 `project.axes`。
   - 重叠检查：**不需要**与其他轴检查，因为不同轴可重叠；若需轴内插入新片段，则按顺序插入并确保重叠检查。

**Shift+右键删除轴**：
- 在波形 Canvas 上点击右键，检测是否命中了某个轴的 Region（通过轴颜色映射确定轴 ID）。
- 如果是，弹出确认对话框（或直接删除），删除该轴并刷新界面。

**非 Shift 下的轴管理**：
- 右键点击轴卡片头部：弹出上下文菜单（删除、重命名、锁定、颜色、在翻译区显示等）。

### 5.3 帧级表格选择（辅助打轴）
为满足“像 Excel 一样选择轴帧”的需求，可以在波形图下方或轴卡片区域旁边提供一个“时间轴列表”视图（可隐藏）。该视图以固定间隔（如每帧或每10帧）列出时间码，支持：
- 单击定位帧。
- Shift+左键拖选或 Ctrl+单击多选（范围选择），最终生成轴片段。
- 此功能作为可选辅助，开发阶段可推后。

### 5.4 轴卡片区域
- 使用水平 `Scrollable` 包裹一个 `Row`，每个轴卡片是一个 `Column`，内部使用 `List`（虚拟滚动）显示片段条目。
- 条目内容：片段序号（如 `轴2-3`）、时间码范围、文本预览。
- 高亮当前帧所在片段：通过 `current_frame` 判断是否在 `[start, end)` 区间，高亮背景。
- 点击片段 → 发送 `SeekTo(segment.start_frame)` 消息。
- 双击文本 → 进入编辑模式，通过 `TextInput` 修改文本，失焦后更新 `segment.text` 并发送 `SegmentUpdated` 消息。
- 每个轴卡片头部显示轴名称、颜色条、锁定图标；右键菜单（非 Shift）执行管理操作。
- 翻译区显示控制：通过右键菜单将轴 ID 加入/移出 `translation_axis_ids`。

### 5.5 翻译区
- 使用 `Tab` 组件切换【翻译区｜术语库】。
- **翻译区**：
  - 双轴/单轴模式切换按钮。
  - 双轴模式下，左右两个 `Scrollable` 分别显示两个轴的全部分段（从 `translation_axis_ids` 获取轴数据）。每个分段旁标注所属轴和序号，支持点击跳帧、双击编辑文本。
  - 当前播放帧所在分段高亮。
- **术语库区**：占位，展示静态提示信息。数据存储预留，未来可通过 IndexedDB 或嵌入数据库实现。

### 5.6 快捷键与工具栏
- 全局快捷键（通过 Iced 键盘事件）：
  - `Space`：播放/暂停
  - `Left Arrow`：回退5秒 (`seek -5s`)
  - `Right Arrow`：前进5秒 (`seek +5s`)
  - `L`：AB循环（先记录A点，再记录B点，循环播放AB区间）
  - `Shift`：进入/退出选区模式（波形打轴）
- 工具栏显示对应按钮，并支持点击触发。

## 6. 状态管理与消息架构

### 6.1 中心状态
```rust
pub struct MyApp {
    pub state: AppState,
    pub mpv: Option<MpvHandler>,
    // 其他运行时字段
}

pub struct AppState {
    pub project: Project,
    pub current_frame: u64,
    pub is_playing: bool,
    pub is_dragging: bool,
    pub shift_held: bool,
    pub waveform_scale: f64,         // 波形缩放系数
    pub waveform_offset: f64,        // 波形平移
    pub selected_axis_for_menu: Option<AxisId>,
    // 临时选区数据（波形拖拽）
    pub drag_start_frame: Option<u64>,
    pub drag_end_frame: Option<u64>,
}
```

### 6.2 消息枚举
```rust
#[derive(Debug, Clone)]
pub enum Message {
    // 应用循环
    Tick,
    // 视频控制
    TogglePlayPause,
    SeekForward5s,
    SeekBackward5s,
    SeekTo(u64),
    // 按键
    KeyDown(Key),
    KeyUp(Key),
    // 波形交互
    WaveformMouseDown { x: f32, y: f32 },
    WaveformMouseMove { x: f32, y: f32 },
    WaveformMouseUp { x: f32, y: f32 },
    WaveformRightClick { x: f32, y: f32 },
    // 轴管理
    AxisRightClick { axis_id: AxisId, action: AxisAction },
    SegmentClick { axis_id: AxisId, segment_id: u64 },
    SegmentDoubleClick { axis_id: AxisId, segment_id: u64 },
    SegmentTextChanged { axis_id: AxisId, segment_id: u64, text: String },
    // 翻译区
    TranslationTabChanged(Tab),
    TranslationAxisSelected { slot: usize, axis_id: AxisId },
    // 项目/文件
    OpenProject,
    SaveProject,
    // 其他 UI 事件
    LayoutChanged(PaneGridDragEvent),
}
```

## 7. 开发依赖清单 (Crates)

```toml
[dependencies]
# GUI
iced = { version = "0.13", features = ["canvas", "wgpu", "multi-window"] }  # 需根据实际情况
iced_aw = { version = "0.9", features = ["split"] }  # 可能需要的额外组件
# 视频
mpv = "0.37"  # 或最新的 mpv-rs
# 音频处理
ffmpeg-next = "7.0"  # 或 symphonia = "0.5"
# 状态与序列化
serde = { version = "1", features = ["derive"] }
serde_json = "1"
ron = "0.8"
# 时间/数学
chrono = "0.4"
# 颜色
palette = "0.7"
# 可选术语库存储
sled = "0.34"
# 错误处理
anyhow = "1"
thiserror = "1"
# 日志
tracing = "0.1"
tracing-subscriber = "0.3"
```

## 8. 开发路线图

| 阶段                  | 目标                                                         | 关键交付               |
| --------------------- | ------------------------------------------------------------ | ---------------------- |
| **P1 基础播放**       | 搭建 Iced 窗口，集成 mpv 并显示视频，实现播放/暂停、时间戳显示。 | 可播放视频，看见画面。 |
| **P2 精确控制与波形** | 实现 `seek_exact`、逐帧步进；提取音频并绘制静态波形，点击波形跳转。 | 波形联动跳帧。         |
| **P3 打轴核心**       | Shift 拖选创建轴，视频实时跟随，右键删除轴，轴数据管理。     | 可通过波形打轴。       |
| **P4 轴卡片**         | 右侧卡片列表，片段显示、高亮、编辑、右键菜单。               | 多轴可视化与管理。     |
| **P5 翻译区**         | 双轴选择，并排文本编辑，联动高亮，术语库占位。               | 翻译工作区。           |
| **P6 界面完善**       | 菜单栏、工具栏、面板拖拽(PaneGrid)、快捷键、主题。           | 完整桌面体验。         |
| **P7 持久化与优化**   | 项目保存/加载，性能优化，错误处理，打包发布。                | Alpha 可分发版本。     |

## 9. 关键技术细节补充

### 9.1 mpv 窗口嵌入步骤
1. 创建 Iced 窗口后，获取原生窗口句柄 (`window_handle`)。在 Iced 中可通过 `Application::new` 提供的 `Settings` 或 `window::Id` 间接获得，实际实现可能需要扩展 Iced 的 `Compositor` 或使用 `raw-window-handle` crate。
2. 初始化 mpv 并设置 `wid`：
   ```rust
   let mpv = MpvHandler::new()?;
   mpv.set_property("wid", window_id)?;  // window_id 从 raw-window-handle 获取
   ```
3. 在 Iced 布局中为视频预留空间，当窗口大小变化时，调用 mpv 的 `geometry` 调整渲染区域。

更优雅的方式是使用 `mpv` 的 OpenGL 渲染回调，将帧纹理直接绘制到 Iced 的 `Canvas` 上，但实现较复杂。对于初始原型，子窗口方式即可。

### 9.2 波形性能优化
- 预计算峰值时降采样，每个屏幕像素对应一个峰值数据点。
- 波形 Canvas 的 `draw` 方法只绘制当前可视范围的线段，利用 Iced 的裁剪区域。
- 轴区域绘制同样只处理可见范围，避免遍历所有 segments。

### 9.3 帧表格选择（可选）
如需实现，可用 Iced 的 `Grid` 或自定义 Widget，每行代表一帧，Shift+点击选择范围，再转换为 segment。此功能可推迟到 P3 之后作为增强。

## 10. 总结
本方案基于 Iced + mpv，提供了一个完全原生、高性能、帧精确的视频打轴应用骨架。其 Elm 架构保证了复杂交互下的状态可预测性，libmpv 提供了生产级的视频控制能力。开发路径清晰，模块解耦，非常适合用 Rust 逐步实现并持续迭代。