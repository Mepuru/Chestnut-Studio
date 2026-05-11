# 调试控制台

> `chestnut_studio/ui/dialogs/debug_console.py`
> `DebugConsole(QDialog)` — 调试控制台窗口，显示日志输出。

---

## 职责

- 显示日志输出（通过 LogManager）
- 支持日志级别颜色区分
- 支持清空和复制
- 支持日志级别过滤

---

## 日志级别颜色

| 级别 | 颜色 | 说明 |
|------|------|------|
| DEBUG | `#6a9955` (绿色) | 调试信息 |
| INFO | `#d4d4d4` (白色) | 一般信息 |
| WARNING | `#dcdcaa` (黄色) | 警告信息 |
| ERROR | `#f44747` (红色) | 错误信息 |

---

## API 参考

### __init__(parent)

初始化调试控制台。

**参数：**
- `parent`: 父窗口（可选）

---

## 使用方式

### MainWindow 中使用

```python
class MainWindow(QMainWindow):
    def _toggle_debug_console(self):
        from chestnut_studio.ui.dialogs.debug_console import DebugConsole

        if self._debug_console is None:
            self._debug_console = DebugConsole(self)
            self._debug_console.show()
        elif self._debug_console.isVisible():
            self._debug_console.hide()
        else:
            self._debug_console.show()
```

### 输出日志

```python
from chestnut_studio.utils.log_manager import LogManager

# 获取日志器
logger = LogManager.instance().get_logger("FFmpeg")

# 输出日志（会自动显示在调试控制台）
logger.info("视频信息: 1920x1080")
logger.error("处理失败: 文件不存在")
```

---

## 设计说明

### 与 LogManager 的关系

- DebugConsole 是 LogManager 的一个处理器（handler）
- 打开时注册处理器：`LogManager.instance().add_handler(self._on_log_record)`
- 关闭时移除处理器：`LogManager.instance().remove_handler(self._on_log_record)`
- 不再重定向 sys.stderr/stdout

### 日志级别过滤

- 下拉框选择最低日志级别
- 调用 `LogManager.instance().set_min_level(level)` 设置
- 低于该级别的日志不会显示

---

## 注意事项

### 处理器注册/注销

- 打开调试控制台时自动注册处理器
- 关闭调试控制台时自动注销处理器
- 避免内存泄漏

### 线程安全

- LogManager 的处理器调用在主线程中执行
- Qt 信号机制是线程安全的

### 性能影响

- 日志处理器会引入少量性能开销
- 对于热路径，可以使用日志级别过滤跳过低级别日志

---

## 依赖

- PySide6: `QDialog`, `QTextEdit`, `QComboBox`, `QPushButton`
- chestnut_studio.utils.log_manager: `LogManager`, `LogRecord`, `LogLevel`
