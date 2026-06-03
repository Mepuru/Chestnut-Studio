"""Chestnut Studio 构建脚本

打包为 PyInstaller 单目录发行包。
每次构建是确定性的——同一源码 + 同依赖版本 → 字节相同的输出。

用法:
    uv run python scripts/build_release.py

输出:
    dist/ChestnutStudio-{version}/   (可运行目录)
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SEP = ";" if sys.platform == "win32" else ":"


def get_version() -> str:
    """从 pyproject.toml 读取版本号"""
    text = (PROJECT_ROOT / "pyproject.toml").read_text("utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        print("错误: 无法从 pyproject.toml 读取版本号")
        sys.exit(1)
    return m.group(1)


def find_python() -> Path:
    """找到项目虚拟环境中的 Python"""
    candidates = [
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
        PROJECT_ROOT / ".venv" / "bin" / "python",
    ]
    for p in candidates:
        if p.exists():
            return p
    print("错误: 未找到 .venv 中的 Python，请先运行 `uv sync`")
    sys.exit(1)


def clean_build_artifacts():
    """清理上次构建产物"""
    for d in ["build", "dist"]:
        shutil.rmtree(PROJECT_ROOT / d, ignore_errors=True)


def build():
    version = get_version()
    name = f"ChestnutStudio-{version}"
    python = find_python()

    print(f"=== 构建 Chestnut Studio v{version} ===")
    print(f"  Python: {python}")
    print(f"  输出:   {PROJECT_ROOT / 'dist' / name}")

    # ── 清理 ──
    clean_build_artifacts()

    # ── 资源路径 ──
    resources_src = PROJECT_ROOT / "chestnut_studio" / "resources"
    if not resources_src.exists():
        print(f"错误: 未找到资源目录 {resources_src}")
        sys.exit(1)

    # ── PyInstaller ──
    # 使用 --onedir 而非 --onefile：
    #   - 构建确定性的（没有 UPX/zip 时间戳差异）
    #   - 方便调试（可以直接看目录内容）
    #   - 后续可用 NSIS / Inno Setup 打包为安装包
    cmd = [
        str(python),
        "-m",
        "PyInstaller",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--name",
        name,
        "--icon",
        str(resources_src / "icon.png"),
        "--add-data",
        f"{resources_src}{SEP}chestnut_studio/resources",
        str(PROJECT_ROOT / "main.py"),
    ]

    print(f"\n运行: pyinstaller {' '.join(cmd[2:])}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"\n✗ PyInstaller 退出码 {result.returncode}")
        sys.exit(result.returncode)

    # ── 确认输出 ──
    out_dir = PROJECT_ROOT / "dist" / name
    exe_path = out_dir / f"{name}.exe"

    if not exe_path.exists():
        print(f"\n✗ 构建失败: {exe_path} 未生成")
        sys.exit(1)

    total_kb = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file()) / 1024
    file_count = sum(1 for _ in out_dir.rglob("*") if _.is_file())
    exe_kb = exe_path.stat().st_size / 1024

    print(f"\n✓ 构建完成: {exe_path}")
    print(f"  exe 大小: {exe_kb:.0f} KB")
    print(f"  目录大小: {total_kb:.0f} KB（{file_count} 个文件）")
    print(f"  dist 路径: {out_dir}")


if __name__ == "__main__":
    build()
