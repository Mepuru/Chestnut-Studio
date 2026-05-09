"""全局拖放覆盖层模块

当用户从外部拖拽文件到窗口上时，显示全屏半透明覆盖层，
根据文件后缀自动识别类型并显示对应的提示区域。
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

VIDEO_EXTENSIONS = {".mp4", ".avi", ".flv", ".mkv", ".mov", ".wmv", ".mp3", ".wav", ".aac", ".flac", ".ogg"}
SUBTITLE_EXTENSIONS = {".srt", ".ass", ".vtt", ".lrc"}

OVERLAY_STYLE = "background: rgba(0, 0, 0, 160);"

ZONE_BASE_STYLE = """
    QLabel {{
        border: 3px dashed {border};
        border-radius: 16px;
        background: {bg};
        color: {color};
        font-size: 14pt;
        font-weight: bold;
        padding: 24px;
    }}
"""

ZONE_ACTIVE_STYLE = """
    QLabel {{
        border: 3px dashed {border};
        border-radius: 16px;
        background: {bg};
        color: {color};
        font-size: 14pt;
        font-weight: bold;
        padding: 24px;
    }}
"""


def _detect_file_type(paths: list[str]) -> str:
    """根据文件后缀判断拖入文件类型

    Returns:
        "video" | "subtitle" | "unknown"
    """
    for path in paths:
        ext = os.path.splitext(path)[1].lower()
        if ext in VIDEO_EXTENSIONS:
            return "video"
        if ext in SUBTITLE_EXTENSIONS:
            return "subtitle"
    return "unknown"


class DragOverlay(QWidget):
    """全屏拖放覆盖层

    信号：
        video_dropped(str): 视频文件被放下
        subtitle_dropped(str): 字幕文件被放下
    """

    video_dropped = Signal(str)
    subtitle_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(OVERLAY_STYLE)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(24)

        # 提示文字
        title = QLabel("拖放文件到此处")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e4e4e7; font-size: 18pt; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(title)

        # 两个拖放区域
        self._video_zone = self._create_zone("#3b82f6", "rgba(59, 130, 246, 30)", "#93c5fd")
        self._video_zone.setText("🎬  视频 / 音频文件")
        self._video_zone.setFixedHeight(120)

        self._subtitle_zone = self._create_zone("#10b981", "rgba(16, 185, 129, 30)", "#6ee7b7")
        self._subtitle_zone.setText("📝  字幕文件（.srt / .ass）")
        self._subtitle_zone.setFixedHeight(120)

        layout.addWidget(self._video_zone)
        layout.addWidget(self._subtitle_zone)
        layout.addStretch()

    @staticmethod
    def _create_zone(border: str, bg: str, color: str) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(ZONE_BASE_STYLE.format(border=border, bg=bg, color=color))
        return label

    def _set_zone_active(self, zone: QLabel, active: bool, border: str, bg_active: str, color: str):
        if active:
            zone.setStyleSheet(ZONE_ACTIVE_STYLE.format(border=border, bg=bg_active, color=color))
        else:
            dim_border = border + "66"
            dim_bg = bg_active.replace(", 80)", ", 15)")
            zone.setStyleSheet(ZONE_ACTIVE_STYLE.format(border=dim_border, bg=dim_bg, color=color + "66"))

    def update_for_files(self, paths: list[str]):
        """根据拖入的文件类型高亮对应区域"""
        file_type = _detect_file_type(paths)
        is_video = file_type == "video"
        is_subtitle = file_type == "subtitle"

        self._set_zone_active(self._video_zone, is_video, "#3b82f6", "rgba(59, 130, 246, 80)", "#93c5fd")
        self._set_zone_active(self._subtitle_zone, is_subtitle, "#10b981", "rgba(16, 185, 129, 80)", "#6ee7b7")

    def handle_drop(self, paths: list[str]):
        """处理文件放下事件，根据类型分发信号"""
        for path in paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                self.video_dropped.emit(path)
            elif ext in SUBTITLE_EXTENSIONS:
                self.subtitle_dropped.emit(path)
        self.hide()
