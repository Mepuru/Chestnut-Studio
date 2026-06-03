"""Chestnut Studio 入口 — B站风格视频笔记工具"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from chestnut_studio.resources import get_icon_path, get_stylesheet_path
from chestnut_studio.ui.main_window import MainWindow
from chestnut_studio.utils.log_manager import LogManager
from chestnut_studio.utils.version import get_version


def main():
    """应用入口"""
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

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

    # 日志输出（stderr，控制台启动时可见）
    LogManager.instance().add_handler(
        lambda r: print(f"[{r.source}] {r.message}", file=sys.stderr)
    )

    # 主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
