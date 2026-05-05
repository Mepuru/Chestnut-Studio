"""Chestnut Studio 入口"""

import sys

from PySide6.QtWidgets import QApplication, QMainWindow


def main():
    """应用入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("Chestnut Studio")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("ChestnutStudio")

    # TODO: 加载样式表
    # TODO: 创建主窗口
    # TODO: 显示主窗口

    print("Chestnut Studio 启动中...")
    print("版本: 0.1.0")
    print("Phase 0: 基础设施搭建中...")

    # 临时：显示一个空窗口
    window = QMainWindow()
    window.setWindowTitle("Chestnut Studio - 打轴工具")
    window.resize(1280, 720)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
