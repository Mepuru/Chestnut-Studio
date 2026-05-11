# 日志装饰器设计

> `chestnut_studio/utils/log_decorator.py`
> @log_source、@log_call 装饰器

---

## 一、职责

- 提供声明式方式定义日志源
- 提供声明式方式记录方法调用
- 简化日志代码编写

---

## 二、装饰器设计

### 2.1 @log_source 装饰器

```python
from collections.abc import Callable

def log_source(source: str) -> Callable:
    """装饰器：声明类的日志源
    
    用法：
        @log_source("FFmpeg")
        class FFmpeg:
            def get_video_info(self):
                logger = LogManager.instance().get_logger("FFmpeg")
                # ...
    
    Args:
        source: 日志源标识（如 "FFmpeg"、"波形"）
        
    Returns:
        装饰后的类
    """
    def decorator(cls: type) -> type:
        cls._log_source = source
        return cls
    return decorator
```

### 2.2 @log_call 装饰器

```python
from functools import wraps
from chestnut_studio.utils.log_manager import LogManager, LogLevel

def log_call(level: LogLevel = LogLevel.INFO, message: str | None = None) -> Callable:
    """装饰器：声明方法的日志输出
    
    自动记录方法的开始和结束，以及异常情况。
    
    用法：
        class FFmpeg:
            @log_call(LogLevel.INFO)
            def get_video_info(self, path: str):
                # 方法执行后会自动输出日志
                pass
            
            @log_call(LogLevel.INFO, message="获取视频信息")
            def get_video_info(self, path: str):
                # 自定义日志消息
                pass
    
    Args:
        level: 日志级别
        message: 自定义日志消息（默认使用方法名）
        
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取日志源
            source = getattr(args[0], '_log_source', 'Unknown') if args else 'Unknown'
            logger = LogManager.instance().get_logger(source)
            
            # 输出方法开始日志
            msg = message or func.__name__
            logger.info(f"{msg} 开始")
            
            try:
                result = func(*args, **kwargs)
                # 输出方法成功日志
                logger.info(f"{msg} 成功")
                return result
            except Exception as e:
                # 输出方法失败日志
                logger.error(f"{msg} 失败: {e}")
                raise
        return wrapper
    return decorator
```

---

## 三、使用示例

### 3.1 基本使用

```python
from chestnut_studio.utils.log_decorator import log_source, log_call
from chestnut_studio.utils.log_manager import LogLevel

@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO)
    def get_video_info(self, path: str):
        # 方法执行后会自动输出日志
        # 输出: [FFmpeg] get_video_info 开始
        # 输出: [FFmpeg] get_video_info 成功
        pass
```

### 3.2 自定义消息

```python
@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO, message="获取视频信息")
    def get_video_info(self, path: str):
        # 输出: [FFmpeg] 获取视频信息 开始
        # 输出: [FFmpeg] 获取视频信息 成功
        pass
```

### 3.3 异常处理

```python
@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO)
    def get_video_info(self, path: str):
        # 如果方法抛出异常
        # 输出: [FFmpeg] get_video_info 开始
        # 输出: [FFmpeg] get_video_info 失败: <异常信息>
        raise ValueError("Invalid path")
```

### 3.4 混合使用

```python
from chestnut_studio.utils.log_decorator import log_source, log_call
from chestnut_studio.utils.log_manager import LogManager, LogLevel

@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO)
    def get_video_info(self, path: str):
        # 自动记录方法调用
        pass
    
    def custom_method(self):
        # 手动记录日志
        logger = LogManager.instance().get_logger("FFmpeg")
        logger.debug("自定义日志")
```

---

## 四、与现有代码的对比

### 4.1 改造前

```python
# main_window.py
class MainWindow(QMainWindow):
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

### 4.2 改造后

```python
# waveform_card.py
from chestnut_studio.utils.log_decorator import log_source, log_call
from chestnut_studio.utils.log_manager import LogLevel

@log_source("波形")
class WaveformCard(BaseCard):
    @log_call(LogLevel.INFO)
    def load_waveform(self, video_path: str):
        # 自动记录开始和结束
        pass
```

---

## 五、注意事项

### 5.1 装饰器顺序

- `@log_source` 应该在类定义上
- `@log_call` 应该在方法定义上
- 多个装饰器可以叠加使用

### 5.2 性能影响

- 装饰器会引入少量性能开销
- 对于热路径，可以考虑不使用装饰器

### 5.3 类型提示

- 装饰器会保留原函数的类型提示
- 使用 `@wraps` 确保元信息保留

---

## 六、扩展性

### 6.1 自定义装饰器

```python
def log_enter_exit(level: LogLevel = LogLevel.DEBUG) -> Callable:
    """装饰器：记录方法进入和退出"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            source = getattr(args[0], '_log_source', 'Unknown') if args else 'Unknown'
            logger = LogManager.instance().get_logger(source)
            
            logger.debug(f"进入 {func.__name__}")
            result = func(*args, **kwargs)
            logger.debug(f"退出 {func.__name__}")
            
            return result
        return wrapper
    return decorator
```

### 6.2 条件日志

```python
def log_if(condition: Callable[..., bool], level: LogLevel = LogLevel.INFO) -> Callable:
    """装饰器：条件日志"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if condition(result):
                source = getattr(args[0], '_log_source', 'Unknown') if args else 'Unknown'
                logger = LogManager.instance().get_logger(source)
                logger.info(f"{func.__name__} 返回: {result}")
            
            return result
        return wrapper
    return decorator
```
