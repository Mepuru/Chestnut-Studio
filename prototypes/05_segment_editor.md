# 字幕编辑模块

## 1. 模块概述

字幕编辑模块是DD_KaoRou2的核心交互模块，提供表格化的字幕编辑界面，支持多轨道字幕管理、合并/切割/拆分等操作，以及撤销/重做功能。

## 2. 功能清单

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 字幕表格 | 5列字幕轨道，时间行显示 | P0 |
| 双击编辑 | 双击单元格编辑字幕文本 | P0 |
| 合并字幕 | 合并选中的多个单元格 | P0 |
| 切割字幕 | 在光标位置切割字幕 | P0 |
| 拆分字幕 | 将字幕拆分为等间隔片段 | P1 |
| 复制/粘贴 | 字幕内容复制粘贴 | P1 |
| 剪切/删除 | 字幕剪切和删除 | P1 |
| 撤销/重做 | Ctrl+Z撤销，Ctrl+Y重做 | P0 |
| 行号跳转 | 点击行号跳转到对应时间 | P1 |
| 样式名编辑 | 点击表头修改样式名 | P2 |
| 字幕检查 | 检查字幕问题 | P2 |
| 循环播放 | 选中区域循环播放 | P2 |

## 3. 数据模型

```rust
/// 字幕数据结构
/// 使用BTreeMap保证按时间排序
pub type SubtitleDict = BTreeMap<u64, (u64, String)>;

/// 字幕存储
/// 5个轨道的字幕数据
pub struct SubtitleStore {
    pub tracks: [SubtitleDict; 5],
    pub style_names: [String; 5],
}

/// 字幕条目
pub struct SubtitleEntry {
    /// 开始时间(毫秒)
    pub start_ms: u64,
    /// 持续时间(毫秒)
    pub duration_ms: u64,
    /// 字幕文本
    pub text: String,
    /// 所属轨道(0-4)
    pub track: usize,
}

/// 表格显示状态
pub struct TableState {
    /// 当前视窗起始行
    pub view_start_row: usize,
    /// 表格间隔(毫秒)
    pub interval_ms: u64,
    /// 当前选中行
    pub selected_row: usize,
    /// 当前选中列
    pub selected_col: usize,
    /// 滚动条位置
    pub scroll_value: i32,
}

/// 编辑历史
pub struct EditHistory {
    /// 历史记录栈
    pub history: Vec<EditSnapshot>,
    /// 当前位置
    pub current_index: usize,
    /// 最大历史数
    pub max_history: usize,
}

/// 编辑快照
pub struct EditSnapshot {
    /// 字幕数据副本
    pub subtitles: SubtitleStore,
    /// 当前位置
    pub position: u64,
    /// 选中行
    pub selected_row: usize,
    /// 滚动条位置
    pub scroll_value: i32,
}
```

## 4. 核心交互流程

### 4.1 表格刷新流程

```
┌─────────────────────────────────────────────────────────────┐
│                    表格刷新流程                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  获取当前时间 │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  计算行号     │
                    │  row = time / interval
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  更新行标题   │
                    │  显示时间码   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  渲染字幕     │
                    │  合并单元格   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  颜色标记     │
                    │  持续时间警告 │
                    └───────────────┘
```

### 4.2 字幕编辑流程

```
双击单元格
    ↓
释放键盘捕获
    ↓
进入编辑模式
    ↓
用户输入文本
    ↓
按下回车/失焦
    ↓
┌─────────────────────────────────┐
│  检查是否已有字幕               │
│  ↓                              │
│  有 → 更新文本                  │
│  无 → 创建新字幕条目            │
│      计算开始时间和持续时间      │
└─────────────────────────────────┘
    ↓
更新字幕字典
    ↓
保存编辑历史
    ↓
刷新表格显示
```

### 4.3 合并字幕流程

```
选中多个行
    ↓
右键菜单 → 合并
    ↓
┌─────────────────────────────────┐
│  获取第一个非空文本             │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  清除选中区域所有字幕           │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  创建新字幕                     │
│  start = 第一行时间             │
│  duration = 最后行时间 - start  │
│  text = 第一个非空文本          │
└─────────────────────────────────┘
    ↓
更新字幕字典
    ↓
合并单元格显示
```

### 4.4 切割字幕流程

```
选中一行
    ↓
右键菜单 → 切割
    ↓
┌─────────────────────────────────┐
│  查找当前位置所在的字幕         │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  将原字幕分为两段               │
│  第一段: start → cut_point      │
│  第二段: cut_point → end        │
└─────────────────────────────────┘
    ↓
更新字幕字典
    ↓
刷新表格显示
```

## 5. 时间格式转换

```rust
/// 毫秒转显示时间 (m:s.ms)
pub fn ms_to_display_time(ms: u64) -> String {
    let m = ms / 60000;
    let s = (ms % 60000) / 1000;
    let ms = ms % 1000;
    format!("{}:{:02}.{:03}", m, s, ms)
}

/// 毫秒转SRT时间 (h:m:s,ms)
pub fn ms_to_srt_time(ms: u64) -> String {
    let h = ms / 3600000;
    let m = (ms % 3600000) / 60000;
    let s = (ms % 60000) / 1000;
    let ms = ms % 1000;
    format!("{}:{:02}:{:02},{:03}", h, m, s, ms)
}

/// 毫秒转ASS时间 (h:m:s.ms)
pub fn ms_to_ass_time(ms: u64) -> String {
    let h = ms / 3600000;
    let m = (ms % 3600000) / 60000;
    let s = (ms % 60000) / 1000;
    let ms = (ms % 1000) / 10; // ASS只用两位毫秒
    format!("{}:{:02}:{:02}.{:02}", h, m, s, ms)
}

/// 毫秒转LRC时间 (m:s.ms)
pub fn ms_to_lrc_time(ms: u64) -> String {
    let m = ms / 60000;
    let s = (ms % 60000) / 1000;
    let ms = (ms % 1000) / 10; // LRC只用两位毫秒
    format!("{:02}:{:02}.{:02}", m, s, ms)
}

/// 显示时间转毫秒
pub fn display_time_to_ms(time: &str) -> u64 {
    let parts: Vec<&str> = time.split(':').collect();
    let m: u64 = parts[0].parse().unwrap_or(0);
    let s_ms: Vec<&str> = parts[1].split('.').collect();
    let s: u64 = s_ms[0].parse().unwrap_or(0);
    let ms: u64 = s_ms.get(1)
        .and_then(|v| v.parse().ok())
        .unwrap_or(0);
    m * 60000 + s * 1000 + ms
}
```

## 6. 消息定义

```rust
pub enum SubtitleMessage {
    /// 刷新表格显示
    RefreshTable,
    /// 双击开始编辑
    StartEdit(usize, usize),
    /// 单元格内容变化
    CellChanged(usize, usize, String),
    /// 点击行号
    RowHeaderClick(usize),
    /// 点击列头(样式名)
    ColumnHeaderClick(usize),
    /// 合并字幕
    Merge,
    /// 切割字幕
    Cut,
    /// 拆分字幕
    Split,
    /// 复制
    Copy,
    /// 粘贴
    Paste,
    /// 剪切
    CutSelection,
    /// 删除
    Delete,
    /// 撤销
    Undo,
    /// 重做
    Redo,
    /// 导入字幕
    Import(usize, PathBuf),
    /// 检查字幕
    Check,
    /// 循环播放选中区域
    LoopSelection,
    /// 取消循环
    CancelLoop,
    /// 滚动条变化
    ScrollChanged(i32),
    /// 表格间隔变化
    IntervalChanged(u64),
}
```

## 7. 颜色标记规则

```rust
/// 根据字幕持续时间返回背景颜色
fn get_duration_color(duration_ms: u64) -> Color {
    if duration_ms < 500 || duration_ms > 8000 {
        // 红色警告 - 持续时间异常
        Color::from_rgb(0.7, 0.13, 0.13) // #B22222
    } else if duration_ms > 4500 {
        // 橙色警告 - 持续时间较长
        Color::from_rgb(0.98, 0.5, 0.44) // #FA8072
    } else {
        // 正常颜色
        Color::from_rgb(0.21, 0.33, 0.36) // #35545d
    }
}
```

## 8. 快捷键映射

| 快捷键 | 功能 |
|--------|------|
| 1/q | 上沿+1行 |
| 2/w | 上沿-1行 |
| 3/e | 下沿+1行 |
| 4/r | 下沿-1行 |
| 5 | 分割字幕 |
| Delete | 删除选中 |
| Ctrl+Z | 撤销 |
| Ctrl+Y | 重做 |
| Ctrl+C | 复制 |
| Ctrl+V | 粘贴 |
| S | 播放选中字幕 |

## 9. 与原版差异

| 功能 | DD_KaoRou2 (QTableWidget) | Rust方案 (Iced List) |
|------|---------------------------|----------------------|
| 表格组件 | QTableWidget | 自定义List Widget |
| 合并单元格 | setSpan | 自定义渲染 |
| 编辑 | 双击触发cellChanged | TextInput内嵌 |
| 滚动 | QScrollBar | Scrollable |
| 虚拟化 | 无(全量渲染) | 虚拟滚动 |
| 性能 | 一般 | 高性能 |
