# 轴卡片模块

## 1. 模块概述

轴卡片模块负责在右侧面板显示所有轴的卡片列表，每个卡片内显示该轴的片段条目，支持点击跳转和右键管理。

## 2. 功能清单

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 轴卡片容器 | 水平滚动显示所有轴 | P0 |
| 片段列表 | 每个轴卡片内垂直滚动 | P0 |
| 点击跳转 | 点击片段跳转到起始帧 | P0 |
| 当前高亮 | 当前帧所在片段高亮 | P0 |
| 轴头部 | 显示轴名称和颜色条 | P1 |
| 右键菜单 | 删除/重命名/锁定轴 | P1 |

## 3. 数据模型

```rust
/// 轴卡片状态
pub struct AxisCardsState {
    /// 水平滚动位置
    pub scroll_x: f32,
    /// 选中的轴ID
    pub selected_axis: Option<u64>,
    /// 选中的片段ID
    pub selected_segment: Option<u64>,
}
```

## 4. 布局结构

```
┌──────────────────────────────────────────────┐
│  轴卡片区 (水平Scrollable)                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────┐ │
│  │ 轴1          │ │ 轴2          │ │ 轴3  │ │
│  │ ┌──────────┐ │ │ ┌──────────┐ │ │      │ │
│  │ │ 轴1-1    │ │ │ │ 轴2-1    │ │ │ ...  │ │
│  │ │ 0:01-0:03│ │ │ │ 0:05-0:08│ │ │      │ │
│  │ ├──────────┤ │ │ ├──────────┤ │ │      │ │
│  │ │ 轴1-2    │ │ │ │ 轴2-2    │ │ │      │ │
│  │ │ 0:04-0:06│ │ │ │ 0:10-0:12│ │ │      │ │
│  │ └──────────┘ │ │ └──────────┘ │ │      │ │
│  └──────────────┘ └──────────────┘ └──────┘ │
└──────────────────────────────────────────────┘
```

## 5. 轴卡片渲染

```rust
/// 渲染单个轴卡片
fn render_axis_card(axis: &Axis, current_frame: u64) -> Element<Message> {
    let header = row![
        // 颜色条
        container(empty())
            .width(4)
            .height(Length::Fill)
            .style(axis.color),
        // 轴名称
        text(&axis.name).size(16),
        // 锁定图标
        if axis.locked { text("🔒") } else { text("") },
    ]
    .spacing(8)
    .padding(8);
    
    let segments: Element<Message> = column(
        axis.segments
            .iter()
            .map(|seg| render_segment(seg, current_frame))
            .collect()
    )
    .spacing(2)
    .into();
    
    container(column![header, segments])
        .width(200)
        .height(Length::Fill)
        .style(card_style)
        .into()
}

/// 渲染单个片段条目
fn render_segment(segment: &Segment, current_frame: u64) -> Element<Message> {
    let is_current = current_frame >= segment.start_frame 
                  && current_frame < segment.end_frame;
    
    let content = column![
        // 序号和时间
        text(format!("轴{}-{}", axis.index, segment.id))
            .size(12),
        text(format!("{} - {}", 
            ms_to_time(segment.start_frame),
            ms_to_time(segment.end_frame)
        )).size(10),
        // 文本预览
        text(&segment.text)
            .size(14)
            .width(Length::Fill),
    ]
    .spacing(2)
    .padding(4);
    
    container(content)
        .width(Length::Fill)
        .style(if is_current { 
            highlighted_style 
        } else { 
            normal_style 
        })
        .on_click(Message::SegmentClick { 
            axis_id: axis.id, 
            segment_id: segment.id 
        })
        .into()
}
```

## 6. 消息定义

```rust
pub enum AxisCardMessage {
    /// 点击片段
    SegmentClick { axis_id: u64, segment_id: u64 },
    /// 双击片段(进入编辑)
    SegmentDoubleClick { axis_id: u64, segment_id: u64 },
    /// 右键轴卡片
    AxisRightClick { axis_id: u64, action: AxisAction },
    /// 滚动变化
    ScrollChanged(f32),
}

pub enum AxisAction {
    Delete,
    Rename,
    ToggleLock,
    ChangeColor,
}
```

## 7. 与原版差异

| 功能 | DD_KaoRou2 | Rust方案 |
|------|------------|----------|
| 组件 | QTableWidget | Iced Column/Row |
| 滚动 | QScrollBar | Scrollable |
| 合并 | setSpan | 自定义渲染 |
| 性能 | 一般 | 虚拟滚动优化 |
