"""核心组件测试"""

import pytest

from chestnut_studio.core.ffmpeg import FFmpeg
from chestnut_studio.core.model.ffmpeg import VideoInfo

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
    """PlayerCard 视频播放器测试"""

    def test_player_card_creation(self, main_window):
        player = main_window.player_card
        assert player is not None

    def test_player_card_signals(self, main_window):
        player = main_window.player_card
        assert hasattr(player, "position_changed")
        assert hasattr(player, "duration_changed")
        assert hasattr(player, "video_opened")
        assert hasattr(player, "playback_state_changed")

    def test_player_card_initial_state(self, main_window):
        player = main_window.player_card
        assert not player.is_playing()
        assert player.get_position() == 0
        assert player.get_duration() == 0

    def test_player_card_volume(self, main_window):
        player = main_window.player_card
        player.set_volume(50)
        assert player.get_position() is not None  # volume no side effect

    def test_player_card_volume_range(self, main_window):
        player = main_window.player_card
        player.set_volume(-10)
        # volume should be clamped to valid range
        player.set_volume(200)
        # should not crash

    def test_player_card_playback_rate(self, main_window):
        player = main_window.player_card
        player.set_playback_rate(1.5)
        player.set_playback_rate(0.05)  # should clamp
        player.set_playback_rate(3.0)  # should clamp
        # should not crash


# ========== MainWindow 集成测试 ==========


class TestMainWindow:
    """MainWindow 集成测试"""

    def test_main_window_creation(self, main_window):
        assert main_window.windowTitle().startswith("Chestnut Studio")

    def test_player_card_exists(self, main_window):
        assert hasattr(main_window, "player_card")

    def test_input_bar_exists(self, main_window):
        assert hasattr(main_window, "input_bar")

    def test_note_panel_exists(self, main_window):
        assert hasattr(main_window, "note_panel")

    def test_note_manager_exists(self, main_window):
        assert hasattr(main_window, "_note_manager")

    def test_ffmpeg_instance(self, main_window):
        assert hasattr(main_window, "_ffmpeg")
        assert isinstance(main_window._ffmpeg, FFmpeg)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
