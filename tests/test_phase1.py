"""Phase 1 视频播放测试"""

import pytest

from chestnut_studio.core.ffmpeg import FFmpeg, VideoInfo

# ========== FFmpeg 测试 ==========


class TestFFmpeg:
    """FFmpeg 视频信息解析测试"""

    def test_parse_duration(self):
        """测试时长解析"""
        ffmpeg = FFmpeg()
        line = "  Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s"
        assert ffmpeg._parse_duration(line) == 330120

    def test_parse_duration_no_ms(self):
        """测试无毫秒的时长解析"""
        ffmpeg = FFmpeg()
        line = "  Duration: 01:02:03, start: 0.000000, bitrate: 1000 kb/s"
        assert ffmpeg._parse_duration(line) == 3723000

    def test_parse_duration_invalid(self):
        """测试无效时长"""
        ffmpeg = FFmpeg()
        assert ffmpeg._parse_duration("invalid") == 0

    def test_parse_bitrate(self):
        """测试码率解析"""
        ffmpeg = FFmpeg()
        line = "  Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s"
        assert ffmpeg._parse_bitrate(line) == 2000

    def test_parse_bitrate_large(self):
        """测试大码率解析"""
        ffmpeg = FFmpeg()
        line = "  Duration: 00:02:00.00, start: 0.000000, bitrate: 15000 kb/s"
        assert ffmpeg._parse_bitrate(line) == 15000

    def test_parse_bitrate_missing(self):
        """测试缺少码率"""
        ffmpeg = FFmpeg()
        assert ffmpeg._parse_bitrate("no bitrate here") == 0

    def test_parse_video_stream(self):
        """测试视频流信息解析"""
        ffmpeg = FFmpeg()
        line = "  Stream #0:0: Video: h264, yuv420p, 1920x1080, 60 fps, 60 tbr"
        w, h, fps = ffmpeg._parse_video_stream(line)
        assert w == 1920
        assert h == 1080
        assert fps == 60.0

    def test_parse_video_stream_30fps(self):
        """测试 30fps 视频流解析"""
        ffmpeg = FFmpeg()
        line = "  Stream #0:0: Video: h264, yuv420p, 1280x720, 30 fps"
        w, h, fps = ffmpeg._parse_video_stream(line)
        assert w == 1280
        assert h == 720
        assert fps == 30.0

    def test_parse_video_stream_invalid(self):
        """测试无效视频流"""
        ffmpeg = FFmpeg()
        w, h, fps = ffmpeg._parse_video_stream("invalid line")
        assert w == 0
        assert h == 0
        assert fps == 0.0

    def test_video_info_dataclass(self):
        """测试 VideoInfo 数据类"""
        info = VideoInfo()
        assert info.duration == 0
        assert info.width == 0
        assert info.height == 0
        assert info.fps == 0.0
        assert info.bitrate == 0

        info2 = VideoInfo(duration=330000, width=1920, height=1080, fps=60.0, bitrate=2000)
        assert info2.duration == 330000
        assert info2.width == 1920
        assert info2.height == 1080
        assert info2.fps == 60.0
        assert info2.bitrate == 2000


# ========== PlayerCard 测试 ==========


class TestPlayerCard:
    """PlayerCard 卡片测试"""

    def test_player_card_creation(self, main_window):
        """测试播放器卡片创建"""
        player = main_window.player_card
        assert player is not None
        assert "视频预览" in player.windowTitle()

    def test_player_card_has_ui_components(self, main_window):
        """测试播放器卡片 UI 组件"""
        player = main_window.player_card
        assert hasattr(player, "_view")
        assert hasattr(player, "_scene")
        assert hasattr(player, "_video_item")
        assert hasattr(player, "_subtitle_item")

    def test_player_card_signals(self, main_window):
        """测试播放器卡片信号定义"""
        player = main_window.player_card
        assert hasattr(player, "position_changed")
        assert hasattr(player, "duration_changed")
        assert hasattr(player, "video_opened")
        assert hasattr(player, "playback_state_changed")
        assert hasattr(player, "subtitle_dropped")

    def test_player_card_initial_state(self, main_window):
        """测试播放器卡片初始状态"""
        player = main_window.player_card
        assert not player.is_playing()
        assert player.get_position() == 0
        assert player.get_duration() == 0

    def test_player_card_volume(self, main_window):
        """测试音量设置"""
        player = main_window.player_card
        player.set_volume(50)
        assert player._volume == 50

        player.set_volume(0)
        assert player._volume == 0

        player.set_volume(100)
        assert player._volume == 100

    def test_player_card_volume_clamp(self, main_window):
        """测试音量值边界"""
        player = main_window.player_card
        player.set_volume(-10)
        assert player._volume == 0

        player.set_volume(200)
        assert player._volume == 100

    def test_player_card_playback_rate(self, main_window):
        """测试倍速设置"""
        player = main_window.player_card
        player.set_playback_rate(1.5)
        assert player._playback_rate == 1.5

    def test_player_card_playback_rate_clamp(self, main_window):
        """测试倍速边界"""
        player = main_window.player_card
        player.set_playback_rate(0.05)
        assert player._playback_rate == 0.1

        player.set_playback_rate(3.0)
        assert player._playback_rate == 2.0

    def test_player_card_subtitle_overlay(self, main_window):
        """测试字幕叠加"""
        player = main_window.player_card
        assert not player._subtitle_item.isVisible()

        player.update_subtitle_overlay("测试字幕")
        assert player._subtitle_item.isVisible()
        assert player._subtitle_item.toPlainText() == "测试字幕"

        player.update_subtitle_overlay("")
        assert not player._subtitle_item.isVisible()



# ========== ToolBar 测试 ==========


class TestToolBar:
    """ToolBar 工具栏测试"""

    def test_toolbar_creation(self, main_window):
        """测试工具栏创建"""
        toolbar = main_window.toolbar
        assert toolbar is not None

    def test_toolbar_has_components(self, main_window):
        """测试工具栏组件"""
        toolbar = main_window.toolbar
        assert hasattr(toolbar, "_play_btn")
        assert hasattr(toolbar, "_mute_btn")
        assert hasattr(toolbar, "_volume_slider")
        assert hasattr(toolbar, "_progress_slider")
        assert hasattr(toolbar, "_time_label")
        assert hasattr(toolbar, "_rate_combo")

    def test_toolbar_signals(self, main_window):
        """测试工具栏信号定义"""
        toolbar = main_window.toolbar
        assert hasattr(toolbar, "play_clicked")
        assert hasattr(toolbar, "mute_clicked")
        assert hasattr(toolbar, "volume_changed")
        assert hasattr(toolbar, "position_changed")
        assert hasattr(toolbar, "rate_changed")

    def test_toolbar_set_duration(self, main_window):
        """测试设置时长"""
        toolbar = main_window.toolbar
        toolbar.set_duration(330000)
        assert toolbar._duration == 330000
        assert toolbar._progress_slider.maximum() == 330000

    def test_toolbar_set_playing(self, main_window):
        """测试播放状态切换"""
        toolbar = main_window.toolbar
        toolbar.set_playing(True)
        assert toolbar._play_btn.text() == "暂停"

        toolbar.set_playing(False)
        assert toolbar._play_btn.text() == "播放"

    def test_toolbar_ms_to_str(self):
        """测试时间格式化"""
        from chestnut_studio.ui.toolbar import ToolBar

        assert ToolBar._ms_to_str(0) == "00:00"
        assert ToolBar._ms_to_str(1000) == "00:01"
        assert ToolBar._ms_to_str(60000) == "01:00"
        assert ToolBar._ms_to_str(330000) == "05:30"


# ========== MainWindow 集成测试 ==========


class TestMainWindowPhase1:
    """MainWindow Phase 1 集成测试"""

    def test_toolbar_exists(self, main_window):
        """测试工具栏存在"""
        assert hasattr(main_window, "toolbar")

    def test_ffmpeg_instance(self, main_window):
        """测试 FFmpeg 实例"""
        assert hasattr(main_window, "_ffmpeg")
        assert isinstance(main_window._ffmpeg, FFmpeg)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
