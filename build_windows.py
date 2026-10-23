"""Build and packaging script for OpenRouter Tracker on Windows."""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_tests() -> bool:
    print("🧪 [1/4] Running Windows unit test suite...")
    res = subprocess.run([sys.executable, "-m", "unittest", "windows.tests.test_windows_core", "-v"])
    return res.returncode == 0


def ensure_icon() -> Path:
    ico_path = Path("OpenRouterTrackerApp/AppIcon.ico")
    if not ico_path.exists():
        print("🎨 Generating AppIcon.ico from AppIcon.png...")
        from PIL import Image
        img = Image.open("OpenRouterTrackerApp/AppIcon.png")
        img.save(
            str(ico_path),
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
        )
    return ico_path


def build_executable(onefile: bool = True) -> bool:
    print(f"📦 [2/4] Compiling Windows executable with PyInstaller ({'onefile' if onefile else 'onedir'})...")
    ico_path = ensure_icon()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        "OpenRouterTracker",
        "--icon",
        str(ico_path),
        "--add-data",
        "OpenRouterTrackerApp/AppIcon.png;OpenRouterTrackerApp",
        "windows/main.py",
    ]

    if onefile:
        cmd.insert(4, "--onefile")
    else:
        cmd.insert(4, "--onedir")

    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("❌ PyInstaller compilation failed.")
        print("💡 Hint: If a PyInstaller dependency is missing, run: pip install pyinstaller altgraph")
        print("💡 You can also run the application directly at any time via: run_windows.bat (or python windows/main.py)")
        return False

    out_exe = Path("dist/OpenRouterTracker.exe") if onefile else Path("dist/OpenRouterTracker/OpenRouterTracker.exe")
    print(f"✨ [3/4] Build Succeeded! Executable at: {out_exe.resolve()}")
    return True


def create_release_zip(onefile: bool = True) -> bool:
    print("🗜️ [4/4] Creating distribution ZIP archive for release...")
    dist_dir = Path("dist")
    zip_path = dist_dir / "OpenRouterTracker-windows-x64.zip"

    if zip_path.exists():
        zip_path.unlink()

    if onefile:
        exe_file = dist_dir / "OpenRouterTracker.exe"
        if not exe_file.exists():
            print(f"❌ Missing {exe_file}")
            return False
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(exe_file, arcname="OpenRouterTracker.exe")
    else:
        app_dir = dist_dir / "OpenRouterTracker"
        if not app_dir.exists():
            print(f"❌ Missing {app_dir}")
            return False
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(app_dir):
                for file in files:
                    full_p = Path(root) / file
                    arcname = full_p.relative_to(dist_dir)
                    zf.write(full_p, arcname=str(arcname))

    print(f"✅ Release package created: {zip_path.resolve()} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build OpenRouter Tracker for Windows")
    parser.add_argument("--onedir", action="store_true", help="Build as a directory instead of a single executable")
    parser.add_argument("--no-test", action="store_true", help="Skip running unit tests before build")
    args = parser.parse_args()

    onefile_mode = not args.onedir

    if not args.no_test:
        if not run_tests():
            print("❌ Tests failed. Build aborted.")
            sys.exit(1)

    if not build_executable(onefile=onefile_mode):
        sys.exit(1)

    if not create_release_zip(onefile=onefile_mode):
        sys.exit(1)
