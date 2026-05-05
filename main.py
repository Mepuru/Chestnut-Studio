"""Chestnut Studio 入口"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

from chestnut_studio.ui.main_window import MainWindow


def load_stylesheet() -> str:
    """加载样式表
    
    Returns:
        样式表内容
    """
    style_path = Path(__file__).parent / "chestnut_studio" / "resources" / "style.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def load_fonts() -> str:
    """加载自定义字体
    
    Returns:
        字体族名称
    """
    fonts_dir = Path(__file__).parent / "chestnut_studio" / "resources" / "fonts"
    font_family = "Microsoft YaHei"  # 默认字体
    
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    font_family = families[0]
                    print(f"已加载字体: {font_file.name} -> {font_family}")
    
    return font_family


def main():
    """应用入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("Chestnut Studio")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("ChestnutStudio")
    
    # 加载自定义字体
    font_family = load_fonts()
    
    # 设置全局字体
    font = QFont(font_family, 10)
    app.setFont(font)
    
    # 加载样式表
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
