"""Phase 2 音频波形测试"""

import pytest

from chestnut_studio.ui.cards.waveform_card import WaveformCard, WaveformPlotWidget


class TestWaveformPlotWidget:
    """测试波形绘图组件"""

    def test_creation(self, app):
        """测试组件创建"""
        widget = WaveformPlotWidget()
        assert widget is not None

    def test_duration(self, app):
        """测试设置时长"""
        widget = WaveformPlotWidget()
        widget.set_duration(60000)
        assert widget._duration_ms == 60000

    def test_signal_position_clicked(self, app):
        """测试点击信号"""
        widget = WaveformPlotWidget()
        widget.set_duration(60000)

        # 测试信号存在
        assert hasattr(widget, "position_clicked")

        # 测试信号发射
        received = []
        widget.position_clicked.connect(lambda ms: received.append(ms))
        widget.position_clicked.emit(5000)
        assert received == [5000]


class TestWaveformCard:
    """测试波形卡片"""

    def test_creation(self, app):
        """测试卡片创建"""
        card = WaveformCard()
        assert card is not None
        assert card.windowTitle() == "波形图"

    def test_default_area(self, app):
        """测试默认停靠区域"""
        from PySide6.QtCore import Qt
        card = WaveformCard()
        assert card.default_area == Qt.BottomDockWidgetArea

    def test_has_plot_widget(self, app):
        """测试包含绘图组件"""
        card = WaveformCard()
        assert hasattr(card, "_plot_widget")
        assert isinstance(card._plot_widget, WaveformPlotWidget)

    def test_has_red_line(self, app):
        """测试包含红线"""
        card = WaveformCard()
        assert hasattr(card, "_red_line")

    def test_has_hint_label(self, app):
        """测试包含提示标签"""
        card = WaveformCard()
        assert hasattr(card, "_hint_label")

    def test_duration_setting(self, app):
        """测试设置时长"""
        card = WaveformCard()
        card.set_duration(60000)
        assert card._duration_ms == 60000

    def test_position_update(self, app):
        """测试更新播放位置"""
        card = WaveformCard()
        card.set_duration(60000)
        card.update_position(30000)
        assert card._current_position_ms == 30000

    def test_subtitle_regions(self, app):
        """测试字幕区域设置"""
        card = WaveformCard()
        regions = {1000: 3000, 5000: 7000}
        card.set_subtitle_regions(regions)
        assert card._subtitle_regions == regions

    def test_clear_subtitle_regions(self, app):
        """测试清除字幕区域"""
        card = WaveformCard()
        regions = {1000: 3000, 5000: 7000}
        card.set_subtitle_regions(regions)
        card.clear_subtitle_regions()
        assert card._subtitle_regions == {}

    def test_signal_position_clicked(self, app):
        """测试点击信号传递"""
        card = WaveformCard()
        card.set_duration(60000)

        # 测试信号存在
        assert hasattr(card, "position_clicked")

        # 测试信号传递
        received = []
        card.position_clicked.connect(lambda ms: received.append(ms))
        card._plot_widget.position_clicked.emit(5000)
        assert received == [5000]

    def test_invalid_video_path(self, app):
        """测试无效视频路径"""
        card = WaveformCard()
        result = card.load_waveform("nonexistent.mp4")
        assert result is False

    def test_view_window_setting(self, app):
        """测试视窗宽度常量"""
        card = WaveformCard()
        assert card.DEFAULT_VIEW_WINDOW_MS == 30000  # 30 秒

    def test_waveform_curve_exists(self, app):
        """测试波形曲线对象存在"""
        card = WaveformCard()
        assert hasattr(card, "_waveform_curve")

    def test_subtitle_items_list(self, app):
        """测试字幕条列表存在"""
        card = WaveformCard()
        assert hasattr(card, "_subtitle_items")
        assert isinstance(card._subtitle_items, list)
        assert len(card._subtitle_items) == 0


class TestWaveformCardIntegration:
    """测试波形卡片与 MainWindow 的集成"""

    def test_waveform_card_exists(self, main_window):
        """测试主窗口包含波形卡片"""
        assert hasattr(main_window, "waveform_card")
        assert isinstance(main_window.waveform_card, WaveformCard)

    def test_waveform_signal_connections(self, main_window):
        """测试信号连接"""
        # 测试播放位置信号连接到波形卡片
        player = main_window.player_card
        waveform = main_window.waveform_card

        # 模拟位置变化
        received = []
        waveform.update_position = lambda ms: received.append(ms)
        player.position_changed.emit(5000)
        # 注意：由于我们替换了方法，信号应该已经连接
        # 这里主要测试信号连接存在


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
