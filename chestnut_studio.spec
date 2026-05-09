# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置文件"""

import sys
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(SPECPATH)

# 资源文件路径
RESOURCES_DIR = ROOT_DIR / "chestnut_studio" / "resources"

# 收集资源文件
datas = [
    (str(RESOURCES_DIR / "icon.png"), "chestnut_studio/resources"),
    (str(RESOURCES_DIR / "style.qss"), "chestnut_studio/resources"),
]

# 收集字体文件
fonts_dir = RESOURCES_DIR / "fonts"
if fonts_dir.exists():
    for font_file in fonts_dir.glob("*.ttf"):
        datas.append((str(font_file), "chestnut_studio/resources/fonts"))

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="Chestnut Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(RESOURCES_DIR / "icon.png"),  # 应用图标
)