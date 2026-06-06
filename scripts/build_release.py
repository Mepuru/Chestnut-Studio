"""Chestnut Studio 构建脚本 — Nuitka --mode=standalone + NSIS installer

用法:
    uv run python scripts/build_release.py

输出:
    dist/ChestnutStudio-{version}-Setup-x86_64_v1.exe
"""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CHECK = "v"
MAKENSIS = Path(r"C:\Program Files (x86)\NSIS\makensis.exe")
INSTALLER_NSI = PROJECT_ROOT / "scripts" / "installer.nsi"


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


def _find_zig() -> Path:
    """在 Nuitka 缓存中找到 zig.exe"""
    candidates = [
        Path.home() / "AppData" / "Local" / "Nuitka" / "Nuitka" / "Cache",
        Path.home() / ".cache" / "Nuitka",
        Path(sys.prefix) / "Lib" / "site-packages" / "ziglang",
    ]
    for base in candidates:
        if base.exists():
            for f in base.rglob("zig.exe"):
                return f
    print("错误: 找不到 zig.exe")
    sys.exit(1)


# ── Nuitka --mode=onedir ──


def build_nuitka(version: str, python: Path) -> Path:
    """用 Nuitka --mode=standalone --zig 构建"""
    dist_name = "main"
    resources_src = PROJECT_ROOT / "chestnut_studio" / "resources"
    main_py = PROJECT_ROOT / "main.py"
    wrapper = PROJECT_ROOT / "scripts" / "zig_wrapper.exe"

    cpu_count = os.cpu_count() or 4
    print(f"\n── Nuitka --mode=standalone (--jobs={cpu_count}, -mcpu=baseline) ──")

    # Zig 默认 -mcpu=native，旧 CPU 会崩溃 (0xc000001d)
    # 临时替换 zig.exe 为 C 包装器，强制 -mcpu=baseline
    zig_path = _find_zig()
    zig_dir = zig_path.parent
    zig_real = zig_dir / "zig_real.exe"
    try:
        if not zig_real.exists():
            shutil.copy2(zig_path, zig_real)
            shutil.copy2(wrapper, zig_path)
            print(f"  {CHECK} zig.exe -> zig_real.exe + wrapper (-mcpu=baseline)")
        else:
            print(f"  {CHECK} zig.exe 已经是 wrapper 模式")

        cmd = [
            str(python),
            "-m",
            "nuitka",
            "--mode=standalone",
            "--zig",
            "--assume-yes-for-downloads",
            "--enable-plugin=pyside6",
            "--include-qt-plugins=multimedia",
            "--windows-console-mode=disable",
            f"--jobs={cpu_count}",
            f"--windows-icon-from-ico={resources_src / 'icon.png'}",
            f"--output-filename={dist_name}",
            f"--output-dir={PROJECT_ROOT / 'dist'}",
            f"--include-data-dir={resources_src}=chestnut_studio/resources",
            "--include-data-file=pyproject.toml=pyproject.toml",
            str(main_py),
        ]

        t0 = time.time()
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        elapsed = time.time() - t0

        if result.returncode != 0:
            print(f"  x Nuitka 退出码 {result.returncode}")
            sys.exit(result.returncode)

        dist_dir = PROJECT_ROOT / "dist" / "main.dist"
        if not dist_dir.exists():
            print(f"  x 输出目录未生成: {dist_dir}")
            sys.exit(1)

        # 计算总大小（递归）
        total_bytes = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
        print(f"  {CHECK} {dist_dir.name}/  ({human_size(total_bytes / 1024)}, {elapsed:.0f}s)")

        return dist_dir
    finally:
        if zig_real.exists():
            shutil.copy2(zig_real, zig_path)
            zig_real.unlink()
            print(f"  {CHECK} zig.exe 已恢复")


# ── NSIS 安装器 ──


def build_installer(version: str, source_dir: Path) -> Path:
    """将 onedir 目录打包成 NSIS setup.exe"""
    print("\n-- NSIS 打包 (makensis) --")

    if not MAKENSIS.exists():
        print(f"  x 找不到 makensis: {MAKENSIS}")
        sys.exit(1)

    setup_name = f"ChestnutStudio-{version}-Setup-x86_64_v1.exe"
    setup_path = PROJECT_ROOT / "dist" / setup_name
    # 删除旧文件，避免干扰
    if setup_path.exists():
        setup_path.unlink()

    cmd = [
        str(MAKENSIS),
        f'/DVERSION={version}',
        f'/DSOURCE_DIR={source_dir}',
        str(INSTALLER_NSI),
    ]

    t0 = time.time()
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"  x makensis 退出码 {result.returncode}")
        sys.exit(result.returncode)

    if not setup_path.exists():
        print(f"  x setup.exe 未生成: {setup_path}")
        sys.exit(1)

    size_kb = setup_path.stat().st_size / 1024
    print(f"  {CHECK} {setup_path.name}  ({human_size(size_kb)}, {elapsed:.0f}s)")
    return setup_path


# ── 主流程 ──


def main():
    version = get_version()
    python = find_python()

    print(f"╔══ Chestnut Studio v{version} Build (+ NSIS) ═══╗")
    print(f"  Python: {python}")
    print()

    dist_dir = build_nuitka(version, python)
    setup_path = build_installer(version, dist_dir)

    # 清理 Nuitka 中间产物
    print()
    print("── 清理中间产物 ──")
    for item in PROJECT_ROOT.glob("dist/*.dist"):
        shutil.rmtree(item, ignore_errors=True)
        print(f"  {CHECK} 删除 {item.name}")
    for item in PROJECT_ROOT.glob("dist/*.build"):
        shutil.rmtree(item, ignore_errors=True)
        print(f"  {CHECK} 删除 {item.name}")
    for item in PROJECT_ROOT.glob("dist/*.onefile-build"):
        shutil.rmtree(item, ignore_errors=True)

    print()
    print("╔══ 构建完成 ═══════════════════════════════════╗")
    kb = setup_path.stat().st_size / 1024
    print(f"  {CHECK} {setup_path.name}  ({human_size(kb)})")
    print(f"  {CHECK} CPU: x86-64 baseline（兼容所有 x86-64 CPU）")
    print(f"  {CHECK} 双击安装，旧版自动覆盖升级")
    print(f"  📁 {PROJECT_ROOT / 'dist'}")


if __name__ == "__main__":
    main()
