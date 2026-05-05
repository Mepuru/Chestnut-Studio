"""Phase 1 视频播放测试"""

import pytest

from chestnut_studio.core.ffmpeg import FFmpeg, VideoInfo

# ========== FFmpeg 测试 ==========


class TestFFmpeg:
    """FFmpeg 视频信息解析测试"""

    def test_parse_duration(self):
        ffmpeg = FFmpeg()
        line = "  Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s"
        assert ffmpeg._parse_duration(line) == 330120

    def test_parse_duration_no_ms(self):
        ffmpeg = FFmpeg()
        line = "  Duration: 01:02:03, start: 0.000000, bitrate: 1000 kb/s"
        assert ffmpeg._parse_duration(line) == 3723000

    def test_parse_duration_invalid(self):
        ffmpeg = FFmpeg()
        assert ffmpeg._parse_duration("invalid") == 0

    def test_parse_bitrate(self):
        ffmpeg = FFmpeg()
        line = "  Duration: 00:05:30.12, start: 0.000000, bitrate: 2000 kb/s"
        assert ffmpeg._parse_bitrate(line) == 2000

    def test_parse_bitrate_large(self):
        ffmpeg = FFmpeg()
        line = "  Duration: 00:02:00.00, start: 0.000000, bitrate: 15000 kb/s"
        assert ffmpeg._parse_bitrate(line) == 15000

    def test_parse_bitrate_missing(self):
        ffmpeg = FFmpeg()
        assert ffmpeg._parse_bitrate("no bitrate here") == 0

    def test_parse_video_stream(self):
        ffmpeg = FFmpeg()
        line = "  Stream #0:0: Video: h264, yuv420p, 1920x1080, 60 fps, 60 tbr"
        w, h, fps = ffmpeg._parse_video_stream(line)
        assert w == 1920
        assert h == 1080
        assert fps == 60.0

    def test_parse_video_stream_30fps(self):
        ffmpeg = FFmpeg()
        line = "  Stream #0:0: Video: h264, yuv420p, 1280x720, 30 fps"
        w, h, fps = ffmpeg._parse_video_stream(line)
        assert w == 1280
        assert h == 720
        assert fps == 30.0

    def test_parse_video_stream_invalid(self):
        ffmpeg = FFmpeg()
        w, h, fps = ffmpeg._parse_video_stream("invalid line")
        assert w == 0
        assert h == 0
        assert fps == 0.0

    def test_video_info_dataclass(self):
        info = VideoInfo()
        assert info.duration == 0
        assert info.width == 0
        assert info.height == 0
        assert info.fps == 0.0
        assert info.bitrate == 0

        info2 = VideoInfo(duration=330000, width=1920, height=1080, fps=60.0, bitrate=2000)
        assert info2.duration == 330000


# ========== PlayerCard 测试 ==========


class TestPlayerCard:
    """PlayerCard 卡片测试"""

    def test_player_card_creation(self, main_window):
        player = main_window.player_card
        assert player is not None
        assert "视频预览" in player.windowTitle()

    def test_player_card_has_ui_components(self, main_window):
        player = main_window.player_card
        assert hasattr(player, "_view")
        assert hasattr(player, "_scene")
        assert hasattr(player, "_video_item")
        assert hasattr(player, "_subtitle_item")
        assert hasattr(player, "_time_label")

    def test_player_card_signals(self, main_window):
        player = main_window.player_card
        assert hasattr(player, "position_changed")
        assert hasattr(player, "duration_changed")
        assert hasattr(player, "video_opened")
        assert hasattr(player, "playback_state_changed")
        assert hasattr(player, "subtitle_dropped")

    def test_player_card_initial_state(self, main_window):
        player = main_window.player_card
        assert not player.is_playing()
        assert player.get_position() == 0
        assert player.get_duration() == 0

    def test_player_card_volume(self, main_window):
        player = main_window.player_card
        player.set_volume(50)
        assert player._volume == 50

    def test_player_card_volume_clamp(self, main_window):
        player = main_window.player_card
        player.set_volume(-10)
        assert player._volume == 0
        player.set_volume(200)
        assert player._volume == 100

    def test_player_card_playback_rate(self, main_window):
        player = main_window.player_card
        player.set_playback_rate(1.5)
        assert player._playback_rate == 1.5

    def test_player_card_playback_rate_clamp(self, main_window):
        player = main_window.player_card
        player.set_playback_rate(0.05)
        assert player._playback_rate == 0.1
        player.set_playback_rate(3.0)
        assert player._playback_rate == 2.0

    def test_player_card_subtitle_overlay(self, main_window):
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
        toolbar = main_window.toolbar
        assert toolbar is not None

    def test_toolbar_has_components(self, main_window):
        toolbar = main_window.toolbar
        assert hasattr(toolbar, "_frame_label")
        assert hasattr(toolbar, "_play_btn")
        assert hasattr(toolbar, "_frame_back_btn")
        assert hasattr(toolbar, "_frame_fwd_btn")
        assert hasattr(toolbar, "_skip_back_btn")
        assert hasattr(toolbar, "_skip_fwd_btn")
        assert hasattr(toolbar, "_rate_combo")

    def test_toolbar_signals(self, main_window):
        toolbar = main_window.toolbar
        assert hasattr(toolbar, "play_clicked")
        assert hasattr(toolbar, "skip_forward")
        assert hasattr(toolbar, "skip_backward")
        assert hasattr(toolbar, "frame_forward")
        assert hasattr(toolbar, "frame_backward")
        assert hasattr(toolbar, "rate_changed")

    def test_toolbar_set_duration(self, main_window):
        toolbar = main_window.toolbar
        toolbar.set_duration(330000)
        assert toolbar._duration == 330000

    def test_toolbar_set_playing(self, main_window):
        toolbar = main_window.toolbar
        toolbar.set_playing(True)
        assert toolbar._play_btn.text() == "暂停"
        toolbar.set_playing(False)
        assert toolbar._play_btn.text() == "播放"

    def test_toolbar_set_fps(self, main_window):
        toolbar = main_window.toolbar
        toolbar.set_fps(60.0)
        assert toolbar._fps == 60.0
        toolbar.set_fps(0)
        assert toolbar._fps == 30.0  # fallback

    def test_toolbar_update_position(self, main_window):
        toolbar = main_window.toolbar
        toolbar.set_fps(60.0)
        toolbar.update_position(1000)  # 1s at 60fps = frame 60
        assert "60" in toolbar._frame_label.text()


# ========== MainWindow 集成测试 ==========


class TestMainWindowPhase1:
    """MainWindow Phase 1 集成测试"""

    def test_toolbar_exists(self, main_window):
        assert hasattr(main_window, "toolbar")

    def test_ffmpeg_instance(self, main_window):
        assert hasattr(main_window, "_ffmpeg")
        assert isinstance(main_window._ffmpeg, FFmpeg)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
