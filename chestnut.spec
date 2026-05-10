# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 单文件版本"""

import os
import tomllib

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(SPEC))

# 从 pyproject.toml 读取版本号（打包命名用）
with open(os.path.join(ROOT_DIR, 'pyproject.toml'), 'rb') as f:
    _pyproject = tomllib.load(f)
VERSION = _pyproject['project']['version']

# 收集数据文件
datas = []

# 添加资源文件（样式表、字体、图标）
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
        'PySide6.QtNetwork',
        'PySide6.QtOpenGL',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'pyqtgraph',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'cv2',
        'torch',
        'tensorflow',
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'PySide6.Qt3D',
        'PySide6.QtBluetooth',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtHelp',
        'PySide6.QtLocation',
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
        'pyqtgraph.opengl',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'Chestnut Studio {VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT_DIR, 'chestnut_studio', 'resources', 'icon.png'),
)
