# 统一日志管理器

> `chestnut_studio/utils/log_manager.py`
> 声明式、可扩展的日志系统，替代散落的 print() 调用。

---

## 职责

- 集中管理所有日志输出
- 提供统一的日志接口
- 支持多个日志处理器（可插拔）
- 支持日志级别过滤

---

## 组件概览

| 组件 | 类型 | 说明 |
|------|------|------|
| `LogLevel` | 枚举 | 日志级别：DEBUG, INFO, WARNING, ERROR |
| `LogRecord` | 数据类 | 日志记录（不可变） |
| `Logger` | 类 | 日志器实例，按模块划分 |
| `LogManager` | 类 | 日志管理器（单例） |

---

## 用法示例

### 基本使用

```python
from chestnut_studio.utils.log_manager import LogManager

# 获取日志器
logger = LogManager.instance().get_logger("FFmpeg")

# 输出日志
logger.info("视频信息: 1920x1080")
logger.error("处理失败: 文件不存在")
```

### 添加处理器

```python
from chestnut_studio.utils.log_manager import LogManager, LogRecord

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

### 日志级别过滤

```python
from chestnut_studio.utils.log_manager import LogManager, LogLevel

# 只显示 INFO 及以上级别的日志
LogManager.instance().set_min_level(LogLevel.INFO)

logger = LogManager.instance().get_logger("Test")
logger.debug("这条不会显示")
logger.info("这条会显示")
```

---

## 组件详细说明

### LogLevel

日志级别枚举，值越小级别越低。

```python
class LogLevel(Enum):
    DEBUG = 0      # 调试信息
    INFO = 1       # 一般信息
    WARNING = 2    # 警告信息
    ERROR = 3      # 错误信息
```

---

### LogRecord

日志记录数据类，使用 `frozen=True` 确保不可变。

```python
@dataclass(frozen=True, slots=True)
class LogRecord:
    source: str      # 日志源（如 "FFmpeg"、"波形"）
    level: LogLevel  # 日志级别
    message: str     # 日志消息
```

---

### Logger

日志器实例，每个模块获取自己的 Logger。

```python
class Logger:
    def __init__(self, source: str) -> None: ...
    def debug(self, message: str) -> None: ...
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
```

**方法说明：**

| 方法 | 级别 | 用途 |
|------|------|------|
| `debug(message)` | DEBUG | 调试信息，开发阶段使用 |
| `info(message)` | INFO | 一般信息，正常运行状态 |
| `warning(message)` | WARNING | 警告信息，不影响运行但需注意 |
| `error(message)` | ERROR | 错误信息，操作失败 |

---

### LogManager

日志管理器（单例），管理所有日志源和处理器。

```python
class LogManager:
    @classmethod
    def instance(cls) -> LogManager: ...
    def get_logger(self, source: str) -> Logger: ...
    def set_min_level(self, level: LogLevel) -> None: ...
    def get_min_level(self) -> LogLevel: ...
    def add_handler(self, handler: Callable[[LogRecord], None]) -> None: ...
    def remove_handler(self, handler: Callable[[LogRecord], None]) -> None: ...
    def clear_handlers(self) -> None: ...
    def emit(self, record: LogRecord) -> None: ...
```

**方法说明：**

| 方法 | 说明 |
|------|------|
| `instance()` | 获取单例实例 |
| `get_logger(source)` | 获取或创建指定源的日志器 |
| `set_min_level(level)` | 设置最低日志级别（低于此级别的日志被忽略） |
| `get_min_level()` | 获取当前最低日志级别 |
| `add_handler(handler)` | 添加日志处理器 |
| `remove_handler(handler)` | 移除日志处理器 |
| `clear_handlers()` | 清空所有处理器 |
| `emit(record)` | 发射日志记录（内部使用） |

---

## 设计说明

### 为什么不用 Python 标准库 logging？

| 考虑因素 | Python logging | 自定义 LogManager |
|----------|---------------|-------------------|
| 复杂度 | 高（Logger/Handler/Formatter/Filter） | 低（仅需核心功能） |
| Qt 集成 | 需要桥接 | 可直接使用 handler 模式 |
| 学习成本 | 需要理解层级命名 | 简单直观 |
| 适用场景 | 大型项目、多模块 | PySide6 桌面应用 |

对于 PySide6 桌面应用，自定义 LogManager 更轻量、更易用。

### 线程安全

- `add_handler()` 和 `remove_handler()` 使用 `threading.Lock` 保护
- `emit()` 复制 handler 列表后再遍历，避免并发修改
- 处理器异常会被捕获，不影响主程序

### 单例模式

- 使用双重检查锁（DCLP）确保线程安全
- 提供 `reset()` 方法用于测试时重置

---

## 注意事项

### 处理器注册/注销

- 添加处理器后，所有日志会分发到该处理器
- 不再需要时应调用 `remove_handler()` 移除，避免内存泄漏
- UI 组件（如调试控制台）应在 `closeEvent` 中移除处理器

### 性能影响

- 日志处理器会引入少量性能开销
- 对于热路径，可以使用日志级别过滤跳过低级别日志
- 处理器异常会被静默忽略，不影响主程序

### 与调试控制台的关系

调试控制台（DebugConsole）是 LogManager 的一个处理器：
- 打开时注册处理器
- 关闭时移除处理器
- 通过 LogManager 接收日志，不再重定向 sys.stderr/stdout

---

## 扩展指南

### 自定义处理器

```python
from chestnut_studio.utils.log_manager import LogRecord, LogLevel

# 按级别过滤的处理器
def error_only_handler(record: LogRecord):
    if record.level == LogLevel.ERROR:
        print(f"ERROR: [{record.source}] {record.message}")

LogManager.instance().add_handler(error_only_handler)

# 格式化输出的处理器
def formatted_handler(record: LogRecord):
    import datetime
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"{now} [{record.level.name}] [{record.source}] {record.message}")

LogManager.instance().add_handler(formatted_handler)
```

---

## 依赖

- Python 标准库：`threading`, `dataclasses`, `enum`, `collections.abc`
