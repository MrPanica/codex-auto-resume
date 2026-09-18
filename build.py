# -*- coding: utf-8 -*-
"""
Codex Auto-Resume Build & Packaging Script
Автоматическая сборка автономного EXE через PyInstaller и создание релизного ZIP-архива.
"""

import os
import sys
import shutil
import subprocess
import zipfile
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
RELEASE_DIR = os.path.join(BASE_DIR, "release")
ICON_FILE = os.path.join(BASE_DIR, "icon.ico")
BASE_PNG = os.path.join(BASE_DIR, "codex_base.png")

def clean():
    print("[*] Очистка временных папок сборки...")
    for d in [DIST_DIR, BUILD_DIR, RELEASE_DIR]:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except Exception as e:
                print(f"[-] Не удалось удалить {d}: {e}")

def run_pyinstaller():
    print("[*] Запуск PyInstaller для сборки CodexAutoResume.exe...")
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(RELEASE_DIR, exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        "--name", "CodexAutoResume",
        "--icon", ICON_FILE,
        "--add-data", f"{ICON_FILE};.",
        "--add-data", f"{BASE_PNG};.",
        "--add-data", f"{os.path.join(BASE_DIR, 'settings_gui.py')};.",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32con",
        "--hidden-import", "qfluentwidgets",
        "--hidden-import", "comtypes",
        "--hidden-import", "comtypes.client",
        "--hidden-import", "sqlite3",
        os.path.join(BASE_DIR, "codex_tray_app.py")
    ]

    print("Команда сборки:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode != 0:
        print("[-] Ошибка сборки PyInstaller!")
        sys.exit(res.returncode)
    print("[+] Сборка EXE успешно завершена!")

def package_release():
    print("[*] Упаковка релиза в ZIP-архив...")
    exe_path = os.path.join(DIST_DIR, "CodexAutoResume.exe")
    if not os.path.exists(exe_path):
        print(f"[-] Исполняемый файл не найден: {exe_path}")
        sys.exit(1)

    zip_name = "CodexAutoResume-v2.0-Windows.zip"
    zip_path = os.path.join(RELEASE_DIR, zip_name)

    files_to_pack = [
        ("CodexAutoResume.exe", exe_path),
        ("icon.ico", ICON_FILE),
        ("codex_base.png", BASE_PNG),
        ("README.md", os.path.join(BASE_DIR, "README.md")),
        ("toggle_guardian.vbs", os.path.join(BASE_DIR, "toggle_guardian.vbs")),
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, fpath in files_to_pack:
            if os.path.exists(fpath):
                zf.write(fpath, arcname)
                print(f" [+] Добавлен в архив: {arcname}")

    exe_size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)

    sha256 = hashlib.sha256()
    with open(zip_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    hash_str = sha256.hexdigest()

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ СБОРКИ:")
    print(f"  EXE:      {exe_path} ({exe_size_mb:.2f} MB)")
    print(f"  ZIP:      {zip_path} ({zip_size_mb:.2f} MB)")
    print(f"  SHA256:   {hash_str}")
    print("=" * 60)

if __name__ == "__main__":
    clean()
    run_pyinstaller()
    package_release()
