"""状态栏模块"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStatusBar

from chestnut_studio.utils.version import get_version


class StatusBar(QStatusBar):
    """状态栏

    功能：
    - 三段式显示：状态信息 · 视频参数 · 当前时间
    - 支持动态更新
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._set_default_state()

    def _setup_ui(self):
        """初始化 UI"""
        # 创建三段式布局
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.video_info_label = QLabel("")
        self.video_info_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 版本号标签（右侧永久显示）
        self.version_label = QLabel(f"v{get_version()}")
        self.version_label.setStyleSheet("color: #52525b; font-size: 8pt; padding-right: 4px;")
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 添加到状态栏
        self.addWidget(self.status_label, 1)  # 拉伸因子 1
        self.addWidget(self.video_info_label, 2)  # 拉伸因子 2
        self.addWidget(self.time_label, 1)  # 拉伸因子 1
        self.addPermanentWidget(self.version_label)  # 右侧永久部件

    def _set_default_state(self):
        """设置默认状态"""
        self.status_label.setText("就绪")
        self.video_info_label.setText("")
        self.time_label.setText("00:00 / 00:00")

    def set_status(self, text: str) -> None:
        """设置状态信息

        Args:
            text: 状态文本
        """
        self.status_label.setText(text)

    def set_video_info(self, resolution: str = "", fps: str = "", bitrate: str = "") -> None:
        """设置视频参数信息

        Args:
            resolution: 分辨率（如 "1920×1080"）
            fps: 帧率（如 "60fps"）
            bitrate: 码率（如 "2000kbps"）
        """
        parts = []
        if resolution:
            parts.append(resolution)
        if fps:
            parts.append(fps)
        if bitrate:
            parts.append(bitrate)

        self.video_info_label.setText(" · ".join(parts))

    def set_time(self, current: str, total: str = "") -> None:
        """设置当前播放时间

        Args:
            current: 当前时间（如 "01:32"）
            total: 总时长（如 "05:30"），为空则只显示当前时间
        """
        if total:
            self.time_label.setText(f"{current} / {total}")
        else:
            self.time_label.setText(current)

    def clear_video_info(self) -> None:
        """清除视频参数信息"""
        self.video_info_label.setText("")
