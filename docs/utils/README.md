# 工具层模块

> `chestnut_studio/utils/` 下各模块的接口和用法。
> 工具层无外部依赖，提供通用工具函数。

---

## 模块概览

| 模块 | 文件 | 职责 |
|------|------|------|
| [统一日志管理器](log_manager.md) | `log_manager.py` | 声明式、可扩展的日志系统 |
| [日志装饰器](log_decorator.md) | `log_decorator.py` | 声明式方式定义日志源和记录方法调用 |
| [时间格式转换](time_utils.md) | `time_utils.py` | 毫秒与各格式互转 |
| 版本号工具 | `version.py` | 从 pyproject.toml 单源读取版本号 |

---

## 依赖关系

```
UI 层 (ui/)
  ↓ 调用
核心层 (core/)
  ↓ 调用
工具层 (utils/)  ← 本模块
```

- **工具层**无外部依赖
- **核心层**依赖工具层
- **UI 层**依赖工具层

---

## 设计原则

### 1. 纯函数

工具函数采用纯函数设计：
- 无状态，无副作用
- 输入输出明确
- 易于测试和复用

### 2. 通用性

工具函数应具有通用性：
- 不依赖特定业务逻辑
- 可用于多个模块
- 接口简洁明了

### 3. 无外部依赖

工具层不依赖任何第三方库：
- 只使用 Python 标准库
- 确保轻量级和可移植性
- 避免依赖冲突

---

## 使用示例

### 日志装饰器

```python
from chestnut_studio.utils.log_decorator import log_source, log_call
from chestnut_studio.utils.log_manager import LogLevel

@log_source("FFmpeg")
class FFmpeg:
    @log_call(LogLevel.INFO)
    def get_video_info(self, path: str):
        pass
```

### 日志管理器

```python
from chestnut_studio.utils.log_manager import LogManager

# 获取日志器并输出
logger = LogManager.instance().get_logger("FFmpeg")
logger.info("视频信息: 1920x1080")

# 添加处理器（输出到标准输出）
def stdout_handler(record):
    print(f"[{record.source}] {record.message}")

LogManager.instance().add_handler(stdout_handler)
```

### 时间格式转换

```python
from chestnut_studio.utils.time_utils import ms_to_srt_time, split_time

# 状态栏显示
print(split_time(330000))       # "05:30"

# SRT 导出
print(ms_to_srt_time(330012))   # "0:05:30,012"
```

---

## 测试要求

| 模块 | 测试要求 |
|------|---------|
| `log_manager.py` | 必须有完整测试 |
| `log_decorator.py` | 必须有完整测试 |
| `time_utils.py` | 必须有完整测试 |

运行测试：

```bash
uv run pytest tests/test_log_manager.py
uv run pytest tests/test_log_decorator.py
uv run pytest tests/test_time_utils.py
```

---

## 扩展指南

### 添加新工具函数

1. 在 `utils/` 目录下创建新文件
2. 实现纯函数，无状态无副作用
3. 添加类型注解和文档字符串
4. 编写单元测试
5. 更新本文档

### 添加日志处理器

日志系统支持可插拔处理器，扩展时无需修改现有代码：

```python
from chestnut_studio.utils.log_manager import LogManager, LogRecord

def my_handler(record: LogRecord):
    # 自定义处理逻辑
    pass

LogManager.instance().add_handler(my_handler)
```

### 命名规范

- 文件名：小写 + 下划线
- 函数名：小写 + 下划线
- 常量名：大写 + 下划线

---

## 依赖

- Python 标准库
