"""状态栏模块"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStatusBar


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

        self.time_label = QLabel("当前: 00:00:00.000")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 添加到状态栏
        self.addWidget(self.status_label, 1)  # 拉伸因子 1
        self.addWidget(self.video_info_label, 2)  # 拉伸因子 2
        self.addWidget(self.time_label, 1)  # 拉伸因子 1

    def _set_default_state(self):
        """设置默认状态"""
        self.status_label.setText("就绪")
        self.video_info_label.setText("")
        self.time_label.setText("当前: 00:00:00.000")

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

    def set_time(self, time_str: str) -> None:
        """设置当前播放时间

        Args:
            time_str: 时间字符串（如 "00:01:32.450"）
        """
        self.time_label.setText(f"当前: {time_str}")

    def clear_video_info(self) -> None:
        """清除视频参数信息"""
        self.video_info_label.setText("")
