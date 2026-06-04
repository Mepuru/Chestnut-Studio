"""Chestnut Studio 入口 — B站风格视频笔记工具"""

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from chestnut_studio.resources import get_icon_path, get_stylesheet_path
from chestnut_studio.ui.main_window import MainWindow
from chestnut_studio.utils.log_manager import LogManager, LogLevel, LogRecord
from chestnut_studio.utils.version import get_version


def _get_log_dir() -> Path:
    """获取日志目录 — %LOCALAPPDATA%/ChestnutStudio/logs"""
    base = Path(os.environ["LOCALAPPDATA"]) / "ChestnutStudio"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _setup_logging() -> Path:
    """初始化日志系统：文件 handler + stderr handler

    Returns:
        日志文件路径
    """
    log_dir = _get_log_dir()
    log_path = log_dir / "app.log"

    # 文件 handler — 行缓冲 + 即时 flush，崩溃不丢日志
    log_file = open(log_path, "a", encoding="utf-8", buffering=1)

    def file_handler(record: LogRecord) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{record.source}] {record.level.name:7s}  {record.message}\n"
        log_file.write(line)
        log_file.flush()

    LogManager.instance().add_handler(file_handler)

    # stderr handler（控制台启动时可见）
    def stderr_handler(record: LogRecord) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{record.source}] {record.message}", file=sys.stderr)

    LogManager.instance().add_handler(stderr_handler)

    return log_path


def _setup_crash_hook(log_path: Path) -> None:
    """全局未捕获异常兜底：落日志 + 弹窗提示用户"""
    old_hook = sys.excepthook

    def crash_hook(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        LogManager.instance().emit(LogRecord("CRASH", LogLevel.ERROR, msg))
        # 弹窗告诉用户日志位置
        try:
            QMessageBox.critical(
                None,
                "程序出错",
                f"发生未预期的错误，请将以下日志文件发送给开发者：\n\n{log_path}\n",
            )
        except Exception:
            pass
        if old_hook:
            old_hook(exc_type, exc_value, exc_tb)
        else:
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = crash_hook


def main():
    """应用入口"""
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 日志初始化（放在最前面，确保后续所有日志都能捕获）
    log_path = _setup_logging()
    _setup_crash_hook(log_path)

    app = QApplication(sys.argv)
    app.setApplicationName("Chestnut Studio")
    app.setApplicationVersion(get_version())

    # 设置窗口图标
    from PySide6.QtGui import QIcon

    icon_path = get_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # 全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 加载样式表
    style_path = get_stylesheet_path()
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # 主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
