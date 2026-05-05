# Chestnut Studio — 开发规范

> 代码风格、项目结构、提交规范、协作约定

---

## 一、项目结构

```
D:\ChestnutStudio\
├── prototypes/                    # 设计文档（本目录）
│   ├── prototype.md               # 主文档
│   ├── roadmap.md                 # 路线图
│   ├── development-guide.md       # 开发规范
│   └── modules/                   # 模块设计文档
│       ├── M01-main-window.md
│       ├── M02-player-card.md
│       └── ...
├── src/                           # 源代码
│   ├── main.py                    # 入口文件
│   ├── core/                      # 核心逻辑（无 UI）
│   │   ├── __init__.py
│   │   ├── ffmpeg.py              # FFmpeg 调用封装
│   │   ├── audio.py               # 音频数据处理
│   │   ├── subtitle.py            # 字幕数据结构 + 操作
│   │   └── subtitle_io.py         # 字幕导入/导出（SRT/ASS/VTT/LRC）
│   ├── ui/                        # UI 层
│   │   ├── __init__.py
│   │   ├── main_window.py         # QMainWindow
│   │   ├── menubar.py             # 菜单栏
│   │   ├── toolbar.py             # 工具栏
│   │   ├── statusbar.py           # 状态栏
│   │   ├── cards/                 # 卡片组件
│   │   │   ├── __init__.py
│   │   │   ├── player_card.py     # 视频播放卡片
│   │   │   ├── waveform_card.py   # 音频波形卡片
│   │   │   ├── timeline_card.py   # 打轴编辑卡片
│   │   │   └── translate_card.py  # 翻译面板卡片
│   │   └── dialogs/               # 弹窗
│   │       ├── __init__.py
│   │       └── hotkey_dialog.py   # 快捷键说明
│   ├── resources/                 # 资源文件
│   │   ├── style.qss              # 暗色主题样式表
│   │   ├── icons/                 # 图标
│   │   └── fonts/                 # 字体
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── time_utils.py          # 时间格式转换
│       └── config.py              # 配置管理
├── tests/                         # 测试
│   ├── test_subtitle.py
│   ├── test_ffmpeg.py
│   └── test_io.py
├── assets/                        # 静态资源
│   └── sample/                    # 示例文件
├── pyproject.toml                 # 项目配置
├── requirements.txt               # 依赖
├── README.md                      # 说明文档
├── .gitignore
└── LICENSE
```

---

## 二、命名规范

### 2.1 文件命名

| 类型 | 规则 | 示例 |
|------|------|------|
| Python 文件 | 小写 + 下划线 | `player_card.py`, `time_utils.py` |
| QSS 文件 | 小写 + 下划线 | `style.qss` |
| 图标文件 | 小写 + 下划线 | `play_icon.svg`, `pause_icon.svg` |
| 文档文件 | 小写 + 连字符 | `M01-main-window.md` |

### 2.2 类命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 普通类 | PascalCase | `MainWindow`, `PlayerCard` |
| 卡片类 | PascalCase + Card 后缀 | `PlayerCard`, `TimelineCard` |
| 弹窗类 | PascalCase + Dialog 后缀 | `HotkeyDialog` |
| 线程类 | PascalCase + Thread 后缀 | `FFmpegThread` |
| 信号类 | PascalCase + Signal 后缀 | （直接在类中定义 Signal） |

### 2.3 函数/方法命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 公有方法 | snake_case | `open_video()`, `play_pause()` |
| 私有方法 | 下划线开头 | `_refresh_table()`, `_parse_srt()` |
| 槽函数 | snake_case | `on_play_clicked()`, `on_position_changed()` |
| 属性 | snake_case | `video_path`, `duration` |

### 2.4 常量命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 全局常量 | 全大写 + 下划线 | `DEFAULT_INTERVAL`, `MAX_UNDO_STEPS` |
| 配置键 | 小写 | `layout_type`, `red_line_pos` |

### 2.5 信号命名

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
- 字符串统一使用 **双引号**（与 QSS/JSON 一致）
- 导入顺序：标准库 → 第三方库 → 本地模块，各组之间空一行

```python
import os
import subprocess
from typing import Optional

import numpy as np
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout

from src.core.subtitle import SubtitleDict
from src.utils.time_utils import ms_to_time_str
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

### 3.4 QSS 样式

- 使用 **4 空格** 缩进
- 每个属性独占一行
- 选择器之间空一行
- 颜色值使用小写 hex

```css
QDockWidget {
    background: #2b2d30;
    border: 1px solid #3f4147;
    border-radius: 8px;
}

QDockWidget::title {
    background: #313338;
    padding: 6px 12px;
    color: #e0e0e0;
}
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
    
    def __init__(self, parent=None):
        super().__init__("视频预览", parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """初始化 UI"""
        ...
    
    def _connect_signals(self):
        """连接信号槽"""
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

### 4.4 数据流规范

```
用户操作 → UI 事件 → 核心逻辑处理 → 更新数据 → 刷新 UI
```

字幕数据流示例：
```
用户双击 → cellChanged 信号 → subtitle.set_text() → 更新 subtitleDict → refresh_table()
```

---

## 五、测试规范

### 5.1 测试目录

```
tests/
├── test_subtitle.py      # 字幕数据结构测试
├── test_ffmpeg.py        # FFmpeg 调用测试
├── test_io.py            # 字幕导入导出测试
└── conftest.py           # 测试配置
```

### 5.2 测试命名

```python
class TestSubtitleDict:
    def test_add_subtitle(self):
        """测试添加字幕"""
        ...
    
    def test_delete_subtitle(self):
        """测试删除字幕"""
        ...
    
    def test_merge_subtitles(self):
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

### 6.1 分支策略

```
main          ← 稳定版本
  └── dev     ← 开发主线
       ├── feature/player-card    ← 功能分支
       ├── feature/timeline-card
       └── fix/table-refresh
```

### 6.2 提交信息格式

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

### 6.3 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# Virtual Environment
.venv/
venv/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project
temp_audio/
*.tmp
config
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

### 7.3 外部工具

| 工具 | 用途 | 安装方式 |
|------|------|---------|
| FFmpeg | 视频/音频处理 | 用户自行安装或打包时附带 |
| uv | 包管理 | `pip install uv` 或 `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

---

## 八、文档规范

### 8.1 模块设计文档

每个模块对应 `prototypes/modules/` 下的一个 md 文件，包含：
- 模块职责
- 组件清单
- 信号定义
- 接口设计
- 实现要点

### 8.2 代码注释

- 复杂逻辑必须写注释
- 注释说明"为什么"，而非"是什么"
- 使用中文注释（项目面向中文开发者）

```python
# 刷新可视范围内的字幕条，避免全量刷新导致卡顿
for start in sorted(sub_data):
    if start >= view_end:
        break  # 超出视窗，跳出
```

---

## 九、工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| **uv** | 包管理 | `uv sync` / `uv add <pkg>` / `uv run <cmd>` |
| **ruff** | 代码检查 + 格式化 | `uv run ruff check src/` / `uv run ruff format src/` |
| **pytest** | 测试框架 | `uv run pytest tests/` |
| **PyInstaller** | 打包 | `uv run pyinstaller chestnut.spec` |

### 9.1 开发环境搭建

```bash
# 克隆仓库
git clone https://gitee.com/kurikana/chestnut-studio.git
cd chestnut-studio

# 安装依赖（自动创建 .venv）
uv sync

# 激活虚拟环境
.venv\Scripts\activate

# 运行
uv run python src/chestnut_studio/main.py

# 测试
uv run pytest tests/

# 代码检查
uv run ruff check src/

# 添加新依赖
uv add <package>

# 添加开发依赖
uv add --dev <package>
```
