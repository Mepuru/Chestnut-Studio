# 日志管理器设计

> `chestnut_studio/utils/log_manager.py`
> 日志管理器（单例）、Logger 实例、LogLevel 枚举、LogRecord 数据类

---

## 一、职责

- 集中管理所有日志输出
- 提供统一的日志接口
- 支持多个日志处理器（可插拔）
- 支持日志级别过滤

---

## 二、类设计

### 2.1 LogLevel 枚举

```python
from enum import Enum

class LogLevel(Enum):
    """日志级别"""
    DEBUG = 0      # 调试信息
    INFO = 1       # 一般信息
    WARNING = 2    # 警告信息
    ERROR = 3      # 错误信息
```

### 2.2 LogRecord 数据类

```python
from dataclasses import dataclass

@dataclass
class LogRecord:
    """日志记录"""
    source: str      # 日志源（如 "FFmpeg"、"波形"）
    level: LogLevel  # 日志级别
    message: str     # 日志消息
```

### 2.3 Logger 实例

```python
class Logger:
    """日志器实例
    
    每个模块（如 FFmpeg、导入模块）获取自己的 Logger 实例，
    通过 source 标识来源。
    """
    
    def __init__(self, source: str):
        self.source = source
    
    def debug(self, message: str):
        """输出 DEBUG 级别日志"""
        LogManager.instance().emit(
            LogRecord(self.source, LogLevel.DEBUG, message)
        )
    
    def info(self, message: str):
        """输出 INFO 级别日志"""
        LogManager.instance().emit(
            LogRecord(self.source, LogLevel.INFO, message)
        )
    
    def warning(self, message: str):
        """输出 WARNING 级别日志"""
        LogManager.instance().emit(
            LogRecord(self.source, LogLevel.WARNING, message)
        )
    
    def error(self, message: str):
        """输出 ERROR 级别日志"""
        LogManager.instance().emit(
            LogRecord(self.source, LogLevel.ERROR, message)
        )
```

### 2.4 LogManager 单例

```python
from PySide6.QtCore import QObject, Signal
from typing import Callable

class LogManager(QObject):
    """日志管理器（单例）
    
    职责：
    - 管理所有日志源
    - 分发日志记录到处理器
    - 支持动态添加/移除处理器
    """
    
    # 信号：新日志记录（可用于 UI 组件订阅）
    log_recorded = Signal(LogRecord)
    
    _instance: 'LogManager | None' = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        self._loggers: dict[str, Logger] = {}
        self._handlers: list[Callable[[LogRecord], None]] = []
        self._min_level = LogLevel.DEBUG
    
    @classmethod
    def instance(cls) -> 'LogManager':
        """获取单例实例"""
        if cls._instance is None:
            cls()
        return cls._instance
    
    def get_logger(self, source: str) -> Logger:
        """获取或创建日志器
        
        Args:
            source: 日志源标识（如 "FFmpeg"、"波形"）
            
        Returns:
            Logger 实例
        """
        if source not in self._loggers:
            self._loggers[source] = Logger(source)
        return self._loggers[source]
    
    def set_min_level(self, level: LogLevel):
        """设置最低日志级别
        
        Args:
            level: 最低日志级别
        """
        self._min_level = level
    
    def add_handler(self, handler: Callable[[LogRecord], None]):
        """添加日志处理器
        
        Args:
            handler: 处理函数，接收 LogRecord 参数
        """
        self._handlers.append(handler)
    
    def remove_handler(self, handler: Callable[[LogRecord], None]):
        """移除日志处理器
        
        Args:
            handler: 之前添加的处理函数
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    def emit(self, record: LogRecord):
        """发射日志记录
        
        Args:
            record: 日志记录
        """
        if record.level.value >= self._min_level.value:
            # 发射信号（供 UI 组件订阅）
            self.log_recorded.emit(record)
            
            # 调用所有处理器
            for handler in self._handlers:
                try:
                    handler(record)
                except Exception:
                    # 处理器异常不应影响主程序
                    pass
```

---

## 三、使用示例

### 3.1 基本使用

```python
from chestnut_studio.utils.log_manager import LogManager

class FFmpeg:
    def get_video_info(self, path: str):
        logger = LogManager.instance().get_logger("FFmpeg")
        logger.info(f"获取视频信息: {path}")
        
        try:
            # ... 原有逻辑 ...
            logger.info(f"视频信息: {info.width}x{info.height}")
            return info
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            raise
```

### 3.2 添加处理器

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

### 3.3 日志级别过滤

```python
from chestnut_studio.utils.log_manager import LogManager, LogLevel

# 只显示 INFO 及以上级别的日志
LogManager.instance().set_min_level(LogLevel.INFO)

# DEBUG 日志不会输出
logger = LogManager.instance().get_logger("Test")
logger.debug("这条不会显示")
logger.info("这条会显示")
```

---

## 四、与现有代码的对比

### 4.1 改造前

```python
# main_window.py
class MainWindow(QMainWindow):
    def _on_video_opened(self, path: str):
        # ...
        if self._debug_console and self._debug_console.isVisible():
            print(f"[FFmpeg] 视频信息: {info.width}x{info.height}")
```

### 4.2 改造后

```python
# main_window.py
class MainWindow(QMainWindow):
    def _on_video_opened(self, path: str):
        logger = LogManager.instance().get_logger("FFmpeg")
        logger.info(f"视频信息: {info.width}x{info.height}")
```

---

## 五、注意事项

### 5.1 单例模式

- `LogManager` 使用单例模式，确保全局只有一个实例
- 使用 `LogManager.instance()` 获取实例

### 5.2 线程安全

- Qt 信号机制是线程安全的
- 处理器调用在主线程中执行

### 5.3 异常处理

- 处理器内部捕获异常，不影响主程序
- 如果处理器抛出异常，会被静默忽略
