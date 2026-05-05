"""测试配置"""

import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def app():
    """创建 QApplication 实例（整个测试会话共享）"""
    existing = QApplication.instance()
    if existing:
        return existing
    return QApplication(sys.argv)


@pytest.fixture
def main_window(app):
    """创建主窗口实例"""
    from chestnut_studio.ui.main_window import MainWindow

    return MainWindow()
