"""Chestnut Studio 构建脚本

支持 PyInstaller 和 Nuitka 两种后端，均输出 single-file exe。

用法:
    uv run python scripts/build_release.py                  # 构建全部
    uv run python scripts/build_release.py pyinstaller      # 仅 PyInstaller
    uv run python scripts/build_release.py nuitka           # 仅 Nuitka

输出:
    dist/ChestnutStudio-{version}-PyInstaller.exe   (≈45 MB)
    dist/ChestnutStudio-{version}-Nuitka.exe        (≈18 MB)
"""

import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SEP = ";" if sys.platform == "win32" else ":"


def get_version() -> str:
    text = (PROJECT_ROOT / "pyproject.toml").read_text("utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        print("错误: 无法从 pyproject.toml 读取版本号")
        sys.exit(1)
    return m.group(1)


def find_python() -> Path:
    candidates = [
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
        PROJECT_ROOT / ".venv" / "bin" / "python",
    ]
    for p in candidates:
        if p.exists():
            return p
    print("错误: 未找到 .venv 中的 Python，请先运行 `uv sync`")
    sys.exit(1)


def human_size(kb: float) -> str:
    if kb > 1024:
        return f"{kb / 1024:.1f} MB"
    return f"{kb:.0f} KB"


# ── PyInstaller 后端 ──


def build_pyinstaller(version: str, python: Path) -> Path:
    """用 PyInstaller --onefile 构建"""
    name = f"ChestnutStudio-{version}-PyInstaller"
    resources_src = PROJECT_ROOT / "chestnut_studio" / "resources"

    print(f"\n── PyInstaller --onefile ──")

    cmd = [
        str(python),
        "-m",
        "PyInstaller",
        "--onefile",
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

    t0 = time.time()
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"  ✗ PyInstaller 退出码 {result.returncode}")
        sys.exit(result.returncode)

    exe_path = PROJECT_ROOT / "dist" / f"{name}.exe"
    if not exe_path.exists():
        print(f"  ✗ 输出未生成: {exe_path}")
        sys.exit(1)

    size_kb = exe_path.stat().st_size / 1024
    print(f"  ✓ {exe_path.name}  ({human_size(size_kb)}, {elapsed:.0f}s)")
    return exe_path


# ── Nuitka 后端 ──





def build_nuitka(version: str, python: Path) -> Path:
    """用 Nuitka --onefile --zig 构建"""
    name = f"ChestnutStudio-{version}-Nuitka"
    resources_src = PROJECT_ROOT / "chestnut_studio" / "resources"
    main_py = PROJECT_ROOT / "main.py"

    # 自动检测 CPU 核心数，用于并行编译
    import os
    cpu_count = os.cpu_count() or 4

    print(f"\n── Nuitka --onefile --zig (--jobs={cpu_count}) ──")

    cmd = [
        str(python),
        "-m",
        "nuitka",
        "--onefile",
        "--standalone",
        "--zig",
        "--assume-yes-for-downloads",
        "--enable-plugin=pyside6",
        "--include-qt-plugins=multimedia",
        "--onefile-as-archive",
        "--windows-console-mode=disable",
        f"--jobs={cpu_count}",
        f"--windows-icon-from-ico={resources_src / 'icon.png'}",
        f"--output-filename={name}",
        f"--output-dir={PROJECT_ROOT / 'dist'}",
        f"--include-data-dir={resources_src}=chestnut_studio/resources",
        str(main_py),
    ]

    t0 = time.time()
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"  ✗ Nuitka 退出码 {result.returncode}")
        sys.exit(result.returncode)

    # Nuitka 把 exe 放在 dist/ 根目录
    exe_path = PROJECT_ROOT / "dist" / f"{name}.exe"
    if not exe_path.exists():
        print(f"  ✗ 输出未生成: {exe_path}")
        sys.exit(1)

    size_kb = exe_path.stat().st_size / 1024
    print(f"  ✓ {exe_path.name}  ({human_size(size_kb)}, {elapsed:.0f}s)")

    # 清理 Nuitka 遗留的临时构建目录
    for d in ("main.build", "main.dist", "main.onefile-build"):
        shutil.rmtree(PROJECT_ROOT / "dist" / d, ignore_errors=True)

    return exe_path


# ── 主流程 ──


def main():
    version = get_version()
    python = find_python()

    # 解析目标
    targets = [a.lower() for a in sys.argv[1:]] if len(sys.argv) > 1 else ["pyinstaller", "nuitka"]

    print(f"╔══ Chestnut Studio v{version} 构建 ═══╗")
    print(f"  Python: {python}")
    print(f"  目标:   {', '.join(targets)}")
    print()

    results = []

    if "pyinstaller" in targets:
        results.append(build_pyinstaller(version, python))

    if "nuitka" in targets:
        results.append(build_nuitka(version, python))

    # ── 汇总 ──
    print()
    print("╔══ 构建汇总 ═══════════════════════════╗")
    for p in results:
        kb = p.stat().st_size / 1024
        print(f"  ✓ {p.name}  ({human_size(kb)})")
    print(f"  📁 {PROJECT_ROOT / 'dist'}")


if __name__ == "__main__":
    main()
