"""主窗口模块"""

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QMainWindow

from chestnut_studio.ui.menubar import MenuBar
from chestnut_studio.ui.statusbar import StatusBar
from chestnut_studio.ui.cards.player_card import PlayerCard
from chestnut_studio.ui.cards.timeline_card import TimelineCard
from chestnut_studio.ui.cards.waveform_card import WaveformCard
from chestnut_studio.ui.cards.translate_card import TranslateCard


class MainWindow(QMainWindow):
    """主窗口，管理所有 DockWidget 卡片
    
    功能：
    - 管理四个可拖拽的 DockWidget 卡片
    - 集成菜单栏、状态栏
    - 支持布局保存与恢复
    
    默认布局：
    ┌───────────────────────┬───────────────────────┐
    │                       │                       │
    │    视频播放卡片         │    打轴编辑卡片        │
    │    (左 55%)           │    (右 45%)           │
    │                       │                       │
    ├───────────────────────┼───────────────────────┤
    │                       │                       │
    │    音频波形卡片         │    翻译面板卡片        │
    │    高度 200px          │    高度 200px          │
    │                       │                       │
    └───────────────────────┴───────────────────────┘
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chestnut Studio - 打轴工具")
        self.resize(1280, 720)
        
        # 禁用 Tab 合并，只允许嵌套停靠
        self.setDockNestingEnabled(True)
        self.setDockOptions(
            QMainWindow.AnimatedDocks |
            QMainWindow.AllowNestedDocks
        )
        
        # 初始化设置
        self.settings = QSettings("ChestnutStudio", "KaoRouTool")
        
        # 创建四个卡片
        self._create_cards()
        
        # 设置默认布局
        self._setup_default_layout()
        
        # 创建菜单栏
        self._create_menubar()
        
        # 创建状态栏
        self._create_statusbar()
        
        # 开发阶段：不恢复布局，每次都使用默认布局
        # TODO: 发布时取消注释以下代码
        # self._restore_layout()
    
    def _create_cards(self):
        """创建四个 DockWidget 卡片"""
        from PySide6.QtWidgets import QDockWidget
        
        # 视频播放卡片
        self.player_card = PlayerCard(self)
        self.player_card.setObjectName("player_card")
        self.player_card.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )
        
        # 打轴编辑卡片
        self.timeline_card = TimelineCard(self)
        self.timeline_card.setObjectName("timeline_card")
        self.timeline_card.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )
        
        # 音频波形卡片
        self.waveform_card = WaveformCard(self)
        self.waveform_card.setObjectName("waveform_card")
        self.waveform_card.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )
        
        # 翻译面板卡片
        self.translate_card = TranslateCard(self)
        self.translate_card.setObjectName("translate_card")
        self.translate_card.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )
        
        # 设置卡片属性
        for card in [self.player_card, self.timeline_card, 
                     self.waveform_card, self.translate_card]:
            card.setMinimumSize(200, 150)
    
    def _setup_default_layout(self):
        """设置默认布局"""
        # 添加卡片到主窗口
        self.addDockWidget(Qt.LeftDockWidgetArea, self.player_card)
        self.addDockWidget(Qt.RightDockWidgetArea, self.timeline_card)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.waveform_card)
        self.addDockWidget(Qt.RightDockWidgetArea, self.translate_card)
        
        # 设置左右分割布局
        # 上层：视频播放(左) + 打轴编辑(右)
        self.splitDockWidget(self.player_card, self.timeline_card, Qt.Horizontal)
        
        # 下层：音频波形(左) + 翻译面板(右)
        self.splitDockWidget(self.waveform_card, self.translate_card, Qt.Horizontal)
        
        # 上下分割：上层和下层
        self.splitDockWidget(self.player_card, self.waveform_card, Qt.Vertical)
        
        # 设置初始大小比例
        # 上层高度约 500px，下层高度约 200px
        self.resizeDocks([self.player_card, self.waveform_card], [500, 200], Qt.Vertical)
        
        # 左右比例：左 55%，右 45%
        self.resizeDocks([self.player_card, self.timeline_card], [704, 576], Qt.Horizontal)
        self.resizeDocks([self.waveform_card, self.translate_card], [704, 576], Qt.Horizontal)
    
    def _create_menubar(self):
        """创建菜单栏"""
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # 连接菜单信号
        self.menu_bar.open_video.connect(self._on_open_video)
        self.menu_bar.open_subtitle.connect(self._on_open_subtitle)
        self.menu_bar.save_subtitle.connect(self._on_save_subtitle)
        self.menu_bar.quit_app.connect(self.close)
        self.menu_bar.toggle_fullscreen.connect(self._toggle_fullscreen)
    
    def _create_statusbar(self):
        """创建状态栏"""
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)
    
    def _restore_layout(self):
        """恢复上次保存的布局"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def _save_layout(self):
        """保存当前布局"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event):
        """关闭事件，保存布局"""
        self._save_layout()
        super().closeEvent(event)
    
    def _on_open_video(self):
        """打开视频文件"""
        # TODO: 实现打开视频对话框
        pass
    
    def _on_open_subtitle(self):
        """导入字幕文件"""
        # TODO: 实现导入字幕对话框
        pass
    
    def _on_save_subtitle(self):
        """导出字幕文件"""
        # TODO: 实现导出字幕对话框
        pass
    
    def _toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
