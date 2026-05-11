# 日志装饰器

> `chestnut_studio/utils/log_decorator.py`
> 声明式方式定义日志源和记录方法调用。

---

## 职责

- 提供声明式方式定义日志源
- 提供声明式方式记录方法调用
- 简化日志代码编写

---

## 装饰器概览

| 装饰器 | 类型 | 说明 |
|--------|------|------|
| `@log_source` | 类装饰器 | 声明类的日志源 |
| `@log_call` | 方法装饰器 | 自动记录方法调用 |

---

## 用法示例

### 基本使用

```python
from chestnut_studio.utils.log_decorator import log_source, log_call
from chestnut_studio.utils.log_manager import LogLevel

@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO)
    def get_video_info(self, path: str):
        # 自动记录：[FFmpeg] get_video_info 开始
        # 自动记录：[FFmpeg] get_video_info 成功
        pass
```

### 自定义消息

```python
@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO, message="获取视频信息")
    def get_video_info(self, path: str):
        # 自动记录：[FFmpeg] 获取视频信息 开始
        # 自动记录：[FFmpeg] 获取视频信息 成功
        pass
```

### 异常处理

```python
@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO)
    def get_video_info(self, path: str):
        # 如果抛出异常：
        # 自动记录：[FFmpeg] get_video_info 开始
        # 自动记录：[FFmpeg] get_video_info 失败: <异常信息>
        raise ValueError("Invalid path")
```

### 混合使用

```python
from chestnut_studio.utils.log_decorator import log_source, log_call
from chestnut_studio.utils.log_manager import LogManager, LogLevel

@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO)
    def auto_logged(self):
        # 自动记录
        pass

    def manual_logged(self):
        # 手动记录
        logger = LogManager.instance().get_logger("FFmpeg")
        logger.debug("自定义日志")
```

---

## 装饰器详细说明

### @log_source

类装饰器，声明类的日志源。

```python
def log_source(source: str) -> Callable[[type], type]:
    """类装饰器：声明类的日志源

    Args:
        source: 日志源标识（如 "FFmpeg"、"波形"）

    Returns:
        装饰后的类
    """
```

**效果：**
- 被装饰的类会添加 `_log_source` 属性
- `@log_call` 会读取此属性作为日志源

**示例：**
```python
@log_source("FFmpeg")
class FFmpeg:
    pass

print(FFmpeg._log_source)  # "FFmpeg"
```

---

### @log_call

方法装饰器，自动记录方法调用。

```python
def log_call(
    level: LogLevel = LogLevel.INFO,
    message: str | None = None,
) -> Callable[[F], F]:
    """方法装饰器：自动记录方法调用

    Args:
        level: 日志级别
        message: 自定义日志消息（默认使用方法名）

    Returns:
        装饰后的函数
    """
```

**效果：**
- 方法开始时记录：`{msg} 开始`
- 方法成功时记录：`{msg} 成功`
- 方法失败时记录：`{msg} 失败: {异常信息}`（级别为 ERROR）

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `level` | `LogLevel` | `LogLevel.INFO` | 日志级别 |
| `message` | `str \| None` | `None` | 自定义消息（默认使用方法名） |

---

## 设计说明

### 与 @wraps 的关系

`@log_call` 使用 `@wraps(func)` 保留原函数的元信息：
- `__name__`：函数名
- `__doc__`：文档字符串
- `__module__`：模块名
- `__qualified_name__`：限定名

### 日志源获取顺序

1. 如果 `self` 有 `_log_source` 属性（使用了 `@log_source`），使用该值
2. 否则使用 `"Unknown"` 作为默认值

### 性能影响

- 装饰器会引入少量性能开销（约 1-2 微秒）
- 对于热路径，可以考虑不使用装饰器
- 手动记录日志与装饰器记录日志可以混合使用

---

## 注意事项

### 装饰器顺序

- `@log_source` 应该在类定义上
- `@log_call` 应该在方法定义上
- 多个装饰器可以叠加使用

```python
@log_source("FFmpeg")  # 类装饰器
class FFmpeg:
    @log_call(LogLevel.INFO)  # 方法装饰器
    @staticmethod  # 其他装饰器
    def static_method():
        pass
```

### 类型提示

- 装饰器会保留原函数的类型提示
- 使用 `@wraps` 确保元信息保留

### 与 @staticmethod / @classmethod 的兼容性

`@log_call` 可以与 `@staticmethod` 和 `@classmethod` 一起使用，但需要注意：
- `@staticmethod` 没有 `self` 参数，日志源将是 `"Unknown"`
- `@classmethod` 的第一个参数是 `cls`，可以设置类属性

---

## 扩展指南

### 自定义装饰器

可以基于 LogManager 创建自定义装饰器：

```python
from functools import wraps
from chestnut_studio.utils.log_manager import LogManager, LogLevel

def log_enter_exit(level: LogLevel = LogLevel.DEBUG):
    """装饰器：记录方法进入和退出"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            source = getattr(args[0], '_log_source', 'Unknown') if args else 'Unknown'
            logger = LogManager.instance().get_logger(source)

            logger.log(level, f"进入 {func.__name__}")
            result = func(*args, **kwargs)
            logger.log(level, f"退出 {func.__name__}")

            return result
        return wrapper
    return decorator
```

---

## 依赖

- `chestnut_studio.utils.log_manager`
- Python 标准库：`functools`, `collections.abc`
