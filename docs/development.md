# Chestnut Studio — 开发指南

> 代码风格、项目结构、提交规范、协作约定

---

## 一、项目结构

```
D:\ChestnutStudio\
├── chestnut_studio/               # 主模块
│   ├── __init__.py
│   ├── core/                      # 核心逻辑（无 UI 依赖）
│   │   ├── __init__.py
│   │   ├── ffmpeg.py              # FFmpeg 封装
│   │   ├── audio.py               # 音频数据处理
│   │   ├── subtitle.py            # 字幕数据结构 + 操作
│   │   └── subtitle_io.py         # 字幕导入/导出（SRT/ASS/VTT/LRC）
│   ├── ui/                        # UI 层
│   │   ├── __init__.py
│   │   ├── main_window.py         # QMainWindow
│   │   ├── menubar.py             # 菜单栏
│   │   ├── statusbar.py           # 状态栏
│   │   ├── cards/                 # 卡片组件
│   │   │   ├── __init__.py
│   │   │   ├── player_card.py     # 视频播放卡片
│   │   │   ├── waveform_card.py   # 音频波形卡片
│   │   │   ├── timeline_card.py   # 打轴编辑卡片
│   │   │   └── translate_card.py  # 翻译面板卡片
│   │   └── dialogs/               # 弹窗
│   │       └── __init__.py
│   ├── resources/                 # 资源文件
│   │   ├── style.qss              # 暗色主题样式表
│   │   └── fonts/                 # 字体（HarmonyOS Sans）
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       └── time_utils.py          # 时间格式转换
├── docs/                          # 文档
│   ├── architecture.md            # 架构文档
│   └── development.md             # 开发指南（本文件）
├── prototypes/                    # 设计文档
│   ├── prototype.md               # 主文档
│   ├── roadmap.md                 # 路线图
│   ├── development-guide.md       # 原始开发规范（已迁移）
│   └── modules/                   # 模块设计文档
├── tests/                         # 测试
│   ├── conftest.py                # 测试配置
│   ├── test_phase0.py             # Phase 0 测试
│   └── test_subtitle.py           # 字幕测试
├── main.py                        # 入口文件
├── pyproject.toml                 # 项目配置
├── uv.lock                        # 依赖锁定
├── README.md                      # 说明文档
├── .gitignore
└── LICENSE                        # MIT 协议
```

---

## 二、命名规范

### 2.1 文件命名

| 类型 | 规则 | 示例 |
|------|------|------|
| Python 文件 | 小写 + 下划线 | `player_card.py`, `time_utils.py` |
| QSS 文件 | 小写 + 下划线 | `style.qss` |
| 文档文件 | 小写 + 连字符 | `architecture.md`, `development.md` |

### 2.2 类命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 普通类 | PascalCase | `MainWindow`, `PlayerCard` |
| 卡片类 | PascalCase + Card 后缀 | `PlayerCard`, `TimelineCard` |
| 弹窗类 | PascalCase + Dialog 后缀 | `HotkeyDialog` |
| 线程类 | PascalCase + Thread 后缀 | `FFmpegThread` |

### 2.3 函数/方法命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 公有方法 | snake_case | `open_video()`, `play_pause()` |
| 私有方法 | 下划线开头 | `_refresh_table()`, `_parse_srt()` |
| 槽函数 | snake_case | `on_play_clicked()`, `on_position_changed()` |

### 2.4 信号命名

| 规则 | 示例 |
|------|------|
| 小写 + 下划线，描述事件 | `position_changed`, `subtitle_selected` |
| 动词开头 | `clicked`, `updated`, `finished` |

---

## 三、代码风格

### 3.1 Python 代码

- 遵循 **PEP 8**
- 使用 **4 空格** 缩进，不用 Tab
- 行宽 **120 字符**（非 79）
- 字符串统一使用 **双引号**
- 导入顺序：标准库 → 第三方库 → 本地模块

```python
import os
import subprocess
from typing import Optional

import numpy as np
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestnut_studio.core.subtitle import SubtitleDict
from chestnut_studio.utils.time_utils import ms_to_time_str
```

### 3.2 类型注解

公共 API 必须添加类型注解：

```python
def open_video(self, path: str) -> bool:
    """打开视频文件，返回是否成功"""
    ...

def set_position(self, ms: int) -> None:
    """设置播放位置（毫秒）"""
    ...
```

### 3.3 文档字符串

公共类和公共方法必须写 docstring：

```python
class PlayerCard(QDockWidget):
    """视频播放卡片
    
    功能：
    - 视频渲染 + 字幕叠加预览
    - 播放控制（播放/暂停/停止/音量/倍速）
    - 进度条拖拽 + 时间显示
    - 滚轮缩放 + 拖放打开
    """
    
    def open_video(self, path: str) -> bool:
        """打开视频文件
        
        Args:
            path: 视频文件路径
            
        Returns:
            是否成功打开
        """
        ...
```

---

## 四、架构规范

### 4.1 分层原则

```
UI 层 (ui/)
  ↓ 调用
核心层 (core/)
  ↓ 调用
工具层 (utils/)
```

- **UI 层**：只负责显示和用户交互，不包含业务逻辑
- **核心层**：纯逻辑，不依赖 PySide6（可独立测试）
- **工具层**：通用工具函数

### 4.2 卡片组件规范

每个卡片继承 `QDockWidget`：

```python
class PlayerCard(QDockWidget):
    """视频播放卡片"""
    
    # 信号定义
    position_changed = Signal(int)  # 播放位置变化
    video_opened = Signal(str)      # 视频已打开
    
    # 默认停靠区域
    default_area = Qt.LeftDockWidgetArea
    
    def __init__(self, parent=None):
        super().__init__("视频预览", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """初始化 UI"""
        ...
```

### 4.3 信号通信规范

卡片间通信通过信号，不直接引用：

```python
# ✅ 正确：通过信号通信
self.player_card.position_changed.connect(self.waveform_card.update_position)

# ❌ 错误：直接调用其他卡片的方法
self.player_card._player.setPosition(1000)
```

---

## 五、测试规范

### 5.1 测试目录

```
tests/
├── conftest.py           # 测试配置，共享 fixtures
├── test_phase0.py        # Phase 0 基础设施测试
└── test_subtitle.py      # 字幕数据结构测试
```

### 5.2 测试命名

```python
class TestSubtitleManager:
    def test_set_and_get(self):
        """测试设置和获取字幕"""
        ...
    
    def test_delete(self):
        """测试删除字幕"""
        ...
    
    def test_merge(self):
        """测试合并字幕"""
        ...
```

### 5.3 测试覆盖要求

| 模块 | 测试要求 |
|------|---------|
| `core/subtitle.py` | 必须有完整测试（数据结构核心） |
| `core/subtitle_io.py` | 必须有完整测试（各格式导入导出） |
| `core/ffmpeg.py` | 至少有集成测试 |
| `ui/cards/` | 可选，优先测试核心逻辑 |

---

## 六、Git 规范

### 6.1 提交信息格式

```
<类型>(<范围>): <描述>

<详细说明（可选）>

<关联 Issue（可选）>
```

**类型：**

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 |
| `refactor` | 重构 |
| `style` | 样式/格式 |
| `docs` | 文档 |
| `test` | 测试 |
| `chore` | 构建/工具 |

**示例：**

```
feat(player): 实现视频播放卡片基础功能

- 集成 QMediaPlayer
- 实现播放/暂停/停止
- 实现进度条拖拽
- 实现音量控制

Closes #1
```

---

## 七、依赖管理（uv）

本项目使用 [uv](https://github.com/astral-sh/uv) 进行包管理。

### 7.1 核心依赖

```toml
# pyproject.toml
[project]
name = "chestnut-studio"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "PySide6>=6.11.0",
    "pyqtgraph>=0.14.0",
    "numpy>=2.4.4",
]
```

### 7.2 开发依赖

```toml
[dependency-groups]
dev = [
    "pytest>=9.0.3",
    "ruff>=0.15.12",
]
```

### 7.3 常用命令

```bash
# 安装依赖（自动创建 .venv）
uv sync

# 激活虚拟环境
.venv\Scripts\activate

# 运行应用
uv run python main.py

# 运行测试
uv run pytest tests/

# 代码检查
uv run ruff check chestnut_studio/

# 代码格式化
uv run ruff format chestnut_studio/

# 添加新依赖
uv add <package>

# 添加开发依赖
uv add --dev <package>
```

---

## 八、工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| **uv** | 包管理 | `uv sync` / `uv add <pkg>` / `uv run <cmd>` |
| **ruff** | 代码检查 + 格式化 | `uv run ruff check chestnut_studio/` / `uv run ruff format chestnut_studio/` |
| **pytest** | 测试框架 | `uv run pytest tests/` |
| **PyInstaller** | 打包 | `uv run pyinstaller chestnut.spec` |
