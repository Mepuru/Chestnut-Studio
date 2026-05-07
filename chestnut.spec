# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 优化大小版本"""

import os
import sys

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(SPEC))

# 收集数据文件
datas = []

# 添加资源文件（样式表、字体等）
resources_dir = os.path.join(ROOT_DIR, 'chestnut_studio', 'resources')
if os.path.exists(resources_dir):
    datas.append((resources_dir, os.path.join('chestnut_studio', 'resources')))

# 分析配置
a = Analysis(
    ['main.py'],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'pyqtgraph',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 不需要的大型模块
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
        # 不需要的 Qt 模块
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'PySide6.Qt3D',
        'PySide6.QtBluetooth',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtHelp',
        'PySide6.QtLocation',
        'PySide6.QtNetwork',
        'PySide6.QtNfc',
        'PySide6.QtPositioning',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtSql',
        'PySide6.QtSvg',
        'PySide6.QtTest',
        'PySide6.QtTextToSpeech',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
        'PySide6.QtXml',
        'PySide6.QtXmlPatterns',
        # 不需要的 OpenGL
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'OpenGL',
        'pyqtgraph.opengl',
    ],
    noarchive=False,
    optimize=0,
)

# 创建 PYZ 压缩包
pyz = PYZ(a.pure)

# 创建 EXE
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChestnutStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT_DIR, 'chestnut_studio', 'resources', 'icon.png'),  # 应用图标
)

# 收集文件
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChestnutStudio',
)
