"""Chestnut Studio 入口 — 视频笔记工具"""

import os
import shutil
import sys
import traceback
import types
import typing
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from chestnut_studio.resources import get_icon_path, get_resource_path
from chestnut_studio.utils.log_manager import LogLevel, LogManager, LogRecord
from chestnut_studio.utils.theme import render_stylesheet
from chestnut_studio.utils.version import get_version

_log_file: typing.TextIO | None = None  # 日志文件句柄，供 crash hook 快照用


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
    global _log_file
    log_dir = _get_log_dir()
    log_path = log_dir / "app.log"

    # 轮转：超过 1MB 则重命名 app.log → app.20260604_143000.log，保留最近 10 个
    max_log_size = 1 * 1024 * 1024
    if log_path.exists() and log_path.stat().st_size > max_log_size:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path.replace(log_path.with_suffix(f".{ts}.log"))
        # 清理旧日志，留最近 10 个
        old_logs = sorted(log_dir.glob("app.*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in old_logs[10:]:
            f.unlink()

    # 文件 handler — 行缓冲 + 即时 flush，崩溃不丢日志
    _log_file = open(log_path, "a", encoding="utf-8", buffering=1)

    # 会话分隔线
    assert _log_file is not None
    sep = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _log_file.write(f"{'=' * 60}\n")
    _log_file.write(f"  Chestnut Studio v{get_version()} — {sep}\n")
    _log_file.write(f"{'=' * 60}\n")
    _log_file.flush()

    def file_handler(record: LogRecord) -> None:
        assert _log_file is not None
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{record.source}] {record.level.name:7s}  {record.message}\n"
        _log_file.write(line)
        _log_file.flush()

    LogManager.instance().add_handler(file_handler)

    # stderr handler（控制台启动时可见）
    def stderr_handler(record: LogRecord) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{record.source}] {record.message}", file=sys.stderr)

    LogManager.instance().add_handler(stderr_handler)

    return log_path


def _setup_crash_hook(log_path: Path) -> None:
    """全局未捕获异常兜底：落日志 + 时间戳快照 + 弹窗提示用户"""
    old_hook = sys.excepthook

    def crash_hook(exc_type: type[BaseException], exc_value: BaseException, exc_tb: types.TracebackType | None):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        LogManager.instance().emit(LogRecord("CRASH", LogLevel.ERROR, msg))

        # 快照：将当前日志复制为 crash_20260604_143000.log 并清空 app.log
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_path = log_path.with_stem(f"crash_{ts}")
        if _log_file is not None:
            try:
                _log_file.flush()
                shutil.copy2(log_path, snap_path)
                _log_file.truncate(0)
            except Exception:
                pass

        # 弹窗告诉用户日志位置
        try:
            QMessageBox.critical(
                None,
                "程序出错",
                f"发生未预期的错误，请将以下日志文件发送给开发者：\n\n{snap_path}\n",
            )
        except Exception:
            pass
        if old_hook is not None:
            old_hook(exc_type, exc_value, exc_tb)
        else:
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = crash_hook


def main():
    """应用入口"""
    import time as _time

    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("Chestnut Studio")
    app.setApplicationVersion(get_version())

    # ── 启动页：用 splash.png 加载 ──
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QColor, QIcon, QPixmap
    from PySide6.QtWidgets import QSplashScreen

    splash_t0 = _time.time()
    splash_path = get_resource_path("splash.png")
    splash = QSplashScreen(QPixmap(str(splash_path)))
    splash.show()
    app.processEvents()

    # ── 分阶段加载（splash 上实时显示进度） ──

    def _msg(text: str) -> None:
        """更新启动页底部提示文字"""
        splash.showMessage(text, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, QColor("#8080b0"))
        app.processEvents()

    # 阶段 0：日志初始化（放在 splash 后，不影响启动页弹出速度）
    _msg("正在初始化日志…")
    log_path = _setup_logging()
    _setup_crash_hook(log_path)

    # 阶段 1：窗口图标 + 字体（极轻量）
    icon_path = get_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 阶段 2：主题（读 QSS 文件 + 正则替换）
    _msg("正在加载主题…")
    app.setStyleSheet(render_stylesheet())

    # 阶段 3：主窗口（含 QMediaPlayer 等重型组件）
    _msg("正在创建主窗口…")
    from chestnut_studio.ui.main_window import MainWindow

    window = MainWindow()
    _msg("正在启动…")
    window.show()

    # 阶段 4：确保至少 1.5s 的展示时间，再过渡到主窗口
    elapsed = (_time.time() - splash_t0) * 1000
    remain = max(0, 1500 - elapsed)
    if remain > 0:
        splash.showMessage("正在启动…", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, QColor("#8080b0"))
        app.processEvents()
        QTimer.singleShot(int(remain), lambda: splash.finish(window))
    else:
        splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
