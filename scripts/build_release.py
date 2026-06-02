"""Chestnut Studio 构建脚本

打包为 PyInstaller 单目录发行包。
用法:
    uv run python scripts/build_release.py

输出:
    dist/ChestnutStudio-{version}/   (目录)
    dist/ChestnutStudio-{version}.exe (快捷入口)
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def get_version() -> str:
    """从 pyproject.toml 读取版本号"""
    text = (PROJECT_ROOT / "pyproject.toml").read_text("utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        print("错误: 无法从 pyproject.toml 读取版本号")
        sys.exit(1)
    return m.group(1)


def build():
    version = get_version()
    # 例如 "2.1.0" → "2_1_0"（避免文件名歧义）
    name = f"ChestnutStudio-{version}"

    print(f"=== 构建 Chestnut Studio v{version} ===")

    # ── 准备资源路径 ──
    resources_src = PROJECT_ROOT / "chestnut_studio" / "resources"
    if not resources_src.exists():
        print(f"错误: 未找到资源目录 {resources_src}")
        sys.exit(1)

    # PyInstaller add-data 分隔符: Windows=; 其他=:
    sep = ";" if sys.platform == "win32" else ":"
    resources_arg = f"{resources_src}{sep}chestnut_studio/resources"

    # ── 清理旧构建 ──
    for d in ["build", "dist"]:
        shutil.rmtree(PROJECT_ROOT / d, ignore_errors=True)

    # ── PyInstaller ──
    cmd = [
        sys.executable or "python",
        "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--name", name,
        "--add-data", resources_arg,
        str(PROJECT_ROOT / "main.py"),
    ]

    print(f"运行: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"错误: PyInstaller 退出码 {result.returncode}")
        sys.exit(result.returncode)

    # ── 确认输出 ──
    dist_dir = PROJECT_ROOT / "dist" / name
    if dist_dir.exists():
        exe = dist_dir / f"{name}.exe"
        exe2 = dist_dir / "main.exe"
        # 重命名 main.exe → ChestnutStudio-{version}.exe
        if exe2.exists() and not exe.exists():
            exe2.rename(exe)
        print(f"\n✓ 构建完成: {dist_dir}")
        print(f"  入口: {exe}")
        print(f"  大小: {sum(f.stat().st_size for f in dist_dir.rglob('*')) / 1024 / 1024:.1f} MB")
    else:
        print(f"\n✗ 构建失败: {dist_dir} 未生成")
        sys.exit(1)


if __name__ == "__main__":
    build()
