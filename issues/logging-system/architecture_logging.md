# 统一日志系统方案

> 针对调试控制台存在的重复代码、职责不清、缺乏日志级别等问题，提出统一的日志系统方案。
> 核心思路：参考现有的卡片注册和信号声明模式，建立声明式、可扩展的日志系统。

---

## 一、问题描述

### 1.1 现状

当前调试控制台实现存在以下问题：

```python
# main_window.py 当前状态 — 重复的可见性检查
class MainWindow(QMainWindow):
    def _on_video_opened(self, path: str):
        # ...
        if self._debug_console and self._debug_console.isVisible():
            print(f"[FFmpeg] 视频信息: {info.width}x{info.height}")
        
    def _load_waveform(self, video_path: str):
        if self._debug_console and self._debug_console.isVisible():
            print(f"[波形] 开始加载: {video_path}")
        
        success = self.waveform_card.load_waveform(video_path)
        if success:
            if self._debug_console and self._debug_console.isVisible():
                print("[波形] 加载完成")
        else:
            if self._debug_console and self._debug_console.isVisible():
                print("[波形] 加载失败")
```

### 1.2 问题清单

| 问题 | 位置 | 影响 |
|------|------|------|
| 重复代码 | `main_window.py` 7 处 | 维护困难，容易遗漏 |
| 全局污染 | `sys.stderr/stdout` 重定向 | 影响其他输出 |
| 缺少日志级别 | 所有 `print()` 调用 | 无法区分信息/警告/错误 |
| 散落的调试逻辑 | 多个文件 | 难以统一管理 |
| 性能隐患 | 热路径中的可见性检查 | 可能影响性能 |

### 1.3 重复代码统计

```python
# 以下模式在 main_window.py 中出现 7 次
if self._debug_console and self._debug_console.isVisible():
    print(f"[{source}] {message}")
```

| 位置 | 行号 | 日志源 |
|------|------|--------|
| `_on_video_opened()` | 370-371 | FFmpeg |
| `_on_video_opened()` | 374-375 | FFmpeg |
| `_on_import_subtitle()` | 664-665 | 导入 |
| `_on_import_subtitle()` | 673-674 | 导入 |
| `_load_waveform()` | 780-781 | 波形 |
| `_load_waveform()` | 786-787 | 波形 |
| `_load_waveform()` | 790-791 | 波形 |

---

## 二、目标架构

### 2.1 核心原则

> **日志输出应该是声明式的，日志处理器应该是可插拔的。**

参考现有的设计模式：
- **卡片注册**：`@register_card` 装饰器 → `@log_source` 装饰器
- **信号声明**：`@subscribe` / `@relay` → `@log_call` 装饰器
- **信号管理**：`SignalManager` → `LogManager`

### 2.2 目标结构

```
chestnut_studio/
├── utils/
│   ├── log_manager.py      # 日志管理器（单例）
│   ├── log_decorator.py    # 日志装饰器
│   └── ...
├── ui/
│   ├── dialogs/
│   │   └── debug_console.py  # 调试控制台（改造后）
│   └── main_window.py        # 简化后的主窗口
└── ...
```

### 2.3 改造后的代码

```python
# main_window.py 改造后 — 无重复代码
class MainWindow(QMainWindow):
    def __init__(self):
        # ...
        self._debug_console = None
        
        # 注册日志处理器（可选：输出到标准输出）
        LogManager.instance().add_handler(self._log_to_stdout)
    
    def _on_video_opened(self, path: str):
        logger = LogManager.instance().get_logger("FFmpeg")
        logger.info(f"视频信息: {info.width}x{info.height}")
        # 无需检查 debug_console 是否可见
    
    def _load_waveform(self, video_path: str):
        logger = LogManager.instance().get_logger("波形")
        logger.info(f"开始加载: {video_path}")
        
        success = self.waveform_card.load_waveform(video_path)
        if success:
            logger.info("加载完成")
        else:
            logger.error("加载失败")
```

---

## 三、方案组件

### 3.1 组件总览

| 组件 | 文件 | 职责 | 详细文档 |
|------|------|------|----------|
| **LogManager** | `utils/log_manager.py` | 日志管理器（单例） | [log_manager.md](log_manager.md) |
| **Logger** | `utils/log_manager.py` | 日志器实例 | [log_manager.md](log_manager.md) |
| **LogLevel** | `utils/log_manager.py` | 日志级别枚举 | [log_manager.md](log_manager.md) |
| **@log_source** | `utils/log_decorator.py` | 类装饰器：声明日志源 | [log_decorator.md](log_decorator.md) |
| **@log_call** | `utils/log_decorator.py` | 方法装饰器：自动记录调用 | [log_decorator.md](log_decorator.md) |
| **DebugConsole** | `ui/dialogs/debug_console.py` | 调试控制台（改造后） | [debug_console.md](debug_console.md) |

### 3.2 组件依赖关系

```
LogManager (单例)
  │
  ├─► Logger (实例)
  │     │
  │     └─► LogRecord (数据类)
  │
  ├─► LogLevel (枚举)
  │
  └─► Handler (可插拔处理器)
        │
        ├─► DebugConsole (UI 处理器)
        │
        └─► StdoutHandler (标准输出处理器)
```

### 3.3 与现有架构的关系

本方案**不改变**现有架构的分层原则：

```
UI 层 (ui/)          → 依赖核心层和工具层，依赖 PySide6
核心层 (core/)        → 只依赖工具层，不依赖 PySide6
工具层 (utils/)       → 无外部依赖
```

改动范围**仅限工具层新增模块 + UI 层调试控制台改造**：

| 改动 | 不改动 |
|------|--------|
| `utils/log_manager.py` (新增) | `core/` 目录 |
| `utils/log_decorator.py` (新增) | 各卡片的 `_setup_ui()` 内部逻辑 |
| `ui/dialogs/debug_console.py` (改造) | 核心层数据结构 |
| `ui/main_window.py` (简化) | 工具栏、状态栏、拖放覆盖层 |

---

## 四、使用示例

### 4.1 基本使用

```python
from chestnut_studio.utils.log_manager import LogManager

class FFmpeg:
    def get_video_info(self, path: str):
        logger = LogManager.instance().get_logger("FFmpeg")
        logger.info(f"获取视频信息: {path}")
        
        try:
            # ... 原有逻辑 ...
            logger.info(f"视频信息: {info.width}x{info.height}, {info.fps}fps")
            return info
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            raise
```

### 4.2 使用装饰器

```python
from chestnut_studio.utils.log_decorator import log_source, log_call
from chestnut_studio.utils.log_manager import LogLevel

@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO)
    def get_video_info(self, path: str):
        # 方法执行后会自动输出日志
        pass
```

### 4.3 添加日志处理器

```python
from chestnut_studio.utils.log_manager import LogManager, LogRecord, LogLevel

# 输出到标准输出
def stdout_handler(record: LogRecord):
    print(f"[{record.source}] {record.message}")

LogManager.instance().add_handler(stdout_handler)

# 输出到文件
def file_handler(record: LogRecord):
    with open("app.log", "a") as f:
        f.write(f"[{record.source}] {record.message}\n")

LogManager.instance().add_handler(file_handler)
```

### 4.4 日志级别过滤

```python
from chestnut_studio.utils.log_manager import LogManager, LogLevel

# 只显示 INFO 及以上级别的日志
LogManager.instance().set_min_level(LogLevel.INFO)
```

---

## 五、实施计划

### Phase 1: 核心日志管理器（0.5 天）

| 任务 | 说明 |
|------|------|
| 创建 `utils/log_manager.py` | LogManager 单例、Logger 实例、LogLevel 枚举、LogRecord 数据类 |
| 编写单元测试 | 验证核心功能 |

### Phase 2: 日志装饰器（0.5 天）

| 任务 | 说明 |
|------|------|
| 创建 `utils/log_decorator.py` | @log_source、@log_call 装饰器 |
| 编写单元测试 | 验证装饰器功能 |

### Phase 3: 调试控制台改造（0.5 天）

| 任务 | 说明 |
|------|------|
| 重构 `ui/dialogs/debug_console.py` | 移除 StreamRedirector，使用 LogManager |
| 支持日志级别颜色区分 | DEBUG（绿色）、INFO（白色）、WARNING（黄色）、ERROR（红色） |

### Phase 4: 现有代码迁移（1 天）

| 任务 | 说明 |
|------|------|
| 迁移 `ui/main_window.py` | 移除 7 处重复检查，使用 LogManager |
| 迁移 `core/ffmpeg.py` | 使用 LogManager 输出日志 |
| 迁移 `ui/signal_manager.py` | 使用 LogManager 输出日志 |
| 迁移 `ui/layout_config.py` | 使用 LogManager 输出日志 |
| 迁移 `ui/cards/timeline_card.py` | 使用 LogManager 输出日志 |

### Phase 5: 测试与文档（0.5 天）

| 任务 | 说明 |
|------|------|
| 编写 `tests/test_log_manager.py` | LogManager 单元测试 |
| 更新 `docs/utils/` | 添加日志系统文档 |
| 更新 `docs/development.md` | 添加日志使用指南 |

---

## 六、总工作量

| 阶段 | 工作量 | 风险 |
|------|--------|------|
| Phase 1: 核心日志管理器 | 0.5 天 | 低 |
| Phase 2: 日志装饰器 | 0.5 天 | 低 |
| Phase 3: 调试控制台改造 | 0.5 天 | 低 |
| Phase 4: 现有代码迁移 | 1 天 | 低 |
| Phase 5: 测试与文档 | 0.5 天 | 低 |
| **合计** | **3 天** | |

---

## 七、收益

### 7.1 代码质量

| 指标 | 改造前 | 改造后 |
|------|--------|--------|
| 重复检查代码 | 7 处 | 0 处 |
| 日志级别支持 | 无 | DEBUG/INFO/WARNING/ERROR |
| 全局输出影响 | 有（重定向 sys） | 无 |
| 新增日志点成本 | 3-5 行 + 可见性检查 | 1 行 |

### 7.2 可扩展性

| 方面 | 改造前 | 改造后 |
|------|--------|--------|
| 添加文件日志 | 需修改代码 | 动态添加 handler |
| 添加网络日志 | 需修改代码 | 动态添加 handler |
| 日志级别过滤 | 不支持 | 配置即可 |
| 日志格式定制 | 不支持 | 自定义 handler |

### 7.3 可维护性

- **单一职责**：日志逻辑集中管理
- **关注点分离**：业务代码只关心日志内容，不关心输出目标
- **开闭原则**：新增日志处理器不需要修改现有代码
- **可测试性**：LogManager 可以独立测试

---

## 八、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 迁移期间新旧代码混合 | 混乱 | 渐进式迁移，每阶段独立可运行 |
| 日志处理器异常 | 影响主程序 | handler 内部捕获异常 |
| 性能影响 | 微小 | 单例模式，避免重复创建 |
| 装饰器误用 | 代码可读性 | 提供清晰的文档和示例 |

---

## 九、未来扩展

### 9.1 可能的扩展方向

| 扩展 | 说明 | 实现方式 |
|------|------|----------|
| 文件日志 | 将日志写入文件 | 添加 FileHandler |
| 网络日志 | 将日志发送到远程服务器 | 添加 NetworkHandler |
| 日志轮转 | 自动清理旧日志 | FileHandler 支持 |
| 日志搜索 | 在 UI 中搜索日志 | DebugConsole 扩展 |
| 日志导出 | 导出日志为文件 | DebugConsole 扩展 |

### 9.2 与 Python logging 的关系

本方案是轻量级的日志系统，适用于 PySide6 应用。如果未来需要更复杂的日志功能（如日志轮转、多进程安全等），可以考虑集成 Python 标准库的 `logging` 模块。

---

## 十、与现有架构的关系

本方案**不改变**现有架构的分层原则：

```
UI 层 (ui/)          → 依赖核心层和工具层，依赖 PySide6
核心层 (core/)        → 只依赖工具层，不依赖 PySide6
工具层 (utils/)       → 无外部依赖
```

改动范围**仅限工具层新增模块 + UI 层调试控制台改造**：

| 改动 | 不改动 |
|------|--------|
| `utils/log_manager.py` (新增) | `core/` 目录 |
| `utils/log_decorator.py` (新增) | 各卡片的 `_setup_ui()` 内部逻辑 |
| `ui/dialogs/debug_console.py` (改造) | 核心层数据结构 |
| `ui/main_window.py` (简化) | 工具栏、状态栏、拖放覆盖层 |
