"""Phase 0 基础设施测试"""

import pytest


def test_main_window_creation(main_window):
    """测试主窗口创建"""
    assert main_window.windowTitle().startswith("Chestnut Studio")
    # 允许一定的误差（边框、标题栏等会影响实际大小）
    assert abs(main_window.size().width() - 1280) < 50
    assert abs(main_window.size().height() - 720) < 50


def test_cards_creation(main_window):
    """测试四个卡片创建"""
    # 检查卡片是否存在
    assert hasattr(main_window, "player_card")
    assert hasattr(main_window, "timeline_card")
    assert hasattr(main_window, "waveform_card")
    assert hasattr(main_window, "translate_card")

    # 检查卡片标题
    assert "视频预览" in main_window.player_card.windowTitle()
    assert "时间轴" in main_window.timeline_card.windowTitle()
    assert "波形图" in main_window.waveform_card.windowTitle()
    assert "翻译" in main_window.translate_card.windowTitle()


def test_menubar_creation(main_window):
    """测试菜单栏创建"""
    menubar = main_window.menuBar()
    assert menubar is not None

    # 检查菜单项
    menu_actions = [action.text() for action in menubar.actions()]
    assert "文件(&F)" in menu_actions
    assert "视图(&V)" in menu_actions
    assert "帮助(&H)" in menu_actions


def test_statusbar_creation(main_window):
    """测试状态栏创建"""
    statusbar = main_window.statusBar()
    assert statusbar is not None

    # 检查状态栏标签
    assert hasattr(statusbar, "status_label")
    assert hasattr(statusbar, "video_info_label")
    assert hasattr(statusbar, "time_label")


def test_stylesheet_loading():
    """测试样式表加载"""
    from main import load_stylesheet

    stylesheet = load_stylesheet()
    assert len(stylesheet) > 0
    assert "QMainWindow" in stylesheet
    assert "QDockWidget" in stylesheet


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
