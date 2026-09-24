# -*- coding: utf-8 -*-
"""
Codex Auto-Resume Watchdog — Automated Build and GitHub Release Publisher.
Supports:
1. Compilation of CodexAutoResume.exe via PyInstaller.
2. Packaging of CodexAutoResume-v2.0-Windows.zip release archive.
3. Automatic GitHub Release creation and asset uploading via GitHub REST API.
4. Git tagging (e.g. v2.0.0) and syncing with origin.
"""

import os
import sys
import time
import argparse
import subprocess
import urllib.request
import urllib.parse
import json
import zipfile
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_git_credential_token() -> str:
    """Retrieves the GitHub OAuth/PAT token from Git Credential Manager."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    try:
        proc = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, _ = proc.communicate(input="protocol=https\nhost=github.com\n", timeout=5)
        for line in out.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def get_git_remote_repo() -> str:
    """Extracts 'owner/repo' from 'git remote get-url origin'."""
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=str(PROJECT_ROOT),
            text=True
        ).strip()
        if url.endswith(".git"):
            url = url[:-4]
        if "github.com/" in url:
            return url.split("github.com/", 1)[1]
        elif "github.com:" in url:
            return url.split("github.com:", 1)[1]
    except Exception:
        pass
    return "MrPanica/codex-auto-resume"


def build_binary_and_archive(tag: str = "v2.1.0") -> tuple[Path, Path]:
    """Compiles CodexAutoResume.exe via PyInstaller and packages release ZIP."""
    print("=" * 60)
    print(">>> [1/3] Compiling CodexAutoResume.exe via PyInstaller...")
    print("=" * 60)

    dist_dir = PROJECT_ROOT / "dist"
    release_dir = PROJECT_ROOT / "release"
    icon_file = PROJECT_ROOT / "icon.ico"
    base_png = PROJECT_ROOT / "codex_base.png"

    dist_dir.mkdir(exist_ok=True)
    release_dir.mkdir(exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        "--name", "CodexAutoResume",
        "--icon", str(icon_file),
        "--add-data", f"{icon_file};.",
        "--add-data", f"{base_png};.",
        "--add-data", f"{PROJECT_ROOT / 'settings_gui.py'};.",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32con",
        "--hidden-import", "qfluentwidgets",
        "--hidden-import", "comtypes",
        "--hidden-import", "comtypes.client",
        "--hidden-import", "sqlite3",
        str(PROJECT_ROOT / "codex_tray_app.py")
    ]

    print("Command:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller build failed with exit code {res.returncode}")

    exe_path = dist_dir / "CodexAutoResume.exe"
    if not exe_path.exists():
        raise FileNotFoundError(f"Binary not found: {exe_path}")

    exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Built: {exe_path.name} ({exe_size_mb:.2f} MB)")

    # Packaging ZIP
    print("\n>>> Packaging release archive...")
    zip_path = release_dir / f"CodexAutoResume-{tag}-Windows.zip"
    files_to_pack = [
        ("CodexAutoResume.exe", exe_path),
        ("icon.ico", icon_file),
        ("codex_base.png", base_png),
        ("README.md", PROJECT_ROOT / "README.md"),
        ("toggle_guardian.vbs", PROJECT_ROOT / "toggle_guardian.vbs"),
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, fpath in files_to_pack:
            if fpath.exists():
                zf.write(fpath, arcname)
                print(f" [+] Added to ZIP: {arcname}")

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Packaged: {zip_path.name} ({zip_size_mb:.2f} MB)")

    return exe_path, zip_path


def create_github_release(token: str, repo: str, tag: str, title: str, notes: str, draft: bool = False, prerelease: bool = False) -> dict:
    """Creates a new release on GitHub using REST API."""
    print(f"\n>>> [2/3] Creating GitHub Release {tag} on {repo}...")
    url = f"https://api.github.com/repos/{repo}/releases"
    payload = json.dumps({
        "tag_name": tag,
        "name": title,
        "body": notes,
        "draft": draft,
        "prerelease": prerelease,
        "generate_release_notes": not bool(notes)
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "CodexAutoResume-Publisher",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[SUCCESS] Release created: {data.get('html_url')}")
            return data
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        if e.code == 422:
            print(f"[INFO] Release {tag} might already exist. Fetching existing release...")
            get_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "CodexAutoResume-Publisher",
                    "Accept": "application/vnd.github+json"
                }
            )
            with urllib.request.urlopen(get_req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        raise RuntimeError(f"GitHub API error {e.code}: {err}")


def upload_release_asset(token: str, upload_url: str, file_path: Path):
    """Uploads binary asset to the release."""
    print(f"\n>>> [3/3] Uploading {file_path.name} to release...")
    clean_upload_url = upload_url.split("{")[0]
    full_url = f"{clean_upload_url}?name={urllib.parse.quote(file_path.name)}"

    file_size = file_path.stat().st_size
    print(f"Uploading {file_path.name} ({file_size / 1024 / 1024:.2f} MB)...")

    # If asset already exists on this release, delete it first to allow clean overwrite
    # (extracted from upload_url)
    try:
        release_id = upload_url.split("/releases/")[1].split("/assets")[0]
        repo_part = upload_url.split("https://uploads.github.com/repos/")[1].split("/releases/")[0]
        list_assets_url = f"https://api.github.com/repos/{repo_part}/releases/{release_id}/assets"
        list_req = urllib.request.Request(
            list_assets_url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "CodexAutoResume-Publisher",
                "Accept": "application/vnd.github+json"
            }
        )
        with urllib.request.urlopen(list_req) as r:
            assets = json.loads(r.read().decode("utf-8"))
            for asset in assets:
                if asset.get("name") == file_path.name:
                    del_req = urllib.request.Request(
                        asset["url"],
                        headers={
                            "Authorization": f"Bearer {token}",
                            "User-Agent": "CodexAutoResume-Publisher"
                        },
                        method="DELETE"
                    )
                    urllib.request.urlopen(del_req)
                    print(f" [i] Deleted existing asset: {asset['name']}")
                    time.sleep(1)
    except Exception:
        pass

    with open(file_path, "rb") as f:
        file_data = f.read()

    req = urllib.request.Request(
        full_url,
        data=file_data,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "CodexAutoResume-Publisher",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/octet-stream",
            "Content-Length": str(file_size)
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            download_url = data.get("browser_download_url")
            print(f"[SUCCESS] Asset {file_path.name} uploaded successfully!")
            print(f"Download URL: {download_url}")
            return data
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        raise RuntimeError(f"Failed to upload asset (HTTP {e.code}): {err}")


def main():
    parser = argparse.ArgumentParser(description="Codex Auto-Resume Automated Build & GitHub Release Publisher")
    parser.add_argument("--tag", default="v2.1.0", help="Git release tag (default: v2.1.0)")
    parser.add_argument("--title", default="", help="Release title (default: Codex Auto-Resume v2.1.0)")
    parser.add_argument("--notes", default="", help="Release notes markdown content")
    parser.add_argument("--build-only", action="store_true", help="Only build binary without publishing to GitHub")
    parser.add_argument("--no-build", action="store_true", help="Skip build step and use existing dist/CodexAutoResume.exe")
    parser.add_argument("--push-tag", action="store_true", default=True, help="Create and push git tag to origin")
    args = parser.parse_args()

    tag = args.tag
    title = args.title or f"Codex Auto-Resume {tag}"

    if not args.no_build:
        exe_path, zip_path = build_binary_and_archive(tag)
    else:
        exe_path = PROJECT_ROOT / "dist" / "CodexAutoResume.exe"
        zip_path = PROJECT_ROOT / "release" / f"CodexAutoResume-{tag}-Windows.zip"
        if not exe_path.exists() or not zip_path.exists():
            raise FileNotFoundError(f"Binaries not found. Run without --no-build.")

    if args.build_only:
        print(f"\n[DONE] Build completed successfully at:\n - {exe_path}\n - {zip_path}")
        return

    # GitHub Publishing
    token = get_git_credential_token()
    if not token:
        print("[ERROR] GitHub token not found! Set GITHUB_TOKEN environment variable or configure git credential manager.")
        sys.exit(1)

    repo = get_git_remote_repo()
    print(f"Target Repository: {repo}")

    if args.push_tag:
        try:
            print(f"Tagging commit with {tag}...")
            subprocess.run(["git", "tag", "-a", tag, "-m", title], cwd=str(PROJECT_ROOT), check=False)
            print(f"Pushing tag {tag} to origin...")
            subprocess.run(["git", "push", "origin", tag], cwd=str(PROJECT_ROOT), check=False)
        except Exception as e:
            print(f"Tag push warning: {e}")

    notes = args.notes or (
        f"## 🚀 Codex Auto-Resume Watchdog {tag}\n\n"
        f"An intelligent, non-intrusive background guardian for **OpenAI Codex & ChatGPT Desktop** on Windows 10/11.\n\n"
        f"### ⚡ What's New in {tag}:\n"
        f"- **🛑 Strict Error-Driven Resumption (Manual Interrupt Respect):** Auto-resume now activates **only** when an enabled server error is detected (`selected model is at capacity`, `remote compact task`, `stream disconnected`, etc.). When a task is manually stopped by the user (`status: interrupted`) or completes normally (`status: completed`), the watchdog strictly respects the stop and never auto-resumes.\n"
        f"- **🛡️ Focus Stability & Zero Window Popping:** Removed background chat switching routines to eliminate unwanted Electron/Chromium window activations and focus stealing while running other applications or games.\n"
        f"- **📋 Enhanced Event Journal:** Displays the exact chat title, goal objective or task query, button name, and counters with rich tooltips in both Russian and English.\n"
        f"- **🔒 Resilient Windows Enumeration:** Handled edge cases with desktop switches and Win32 `EnumWindows` error codes (error 112).\n"
        f"- **🚀 Updated Autostart Integration:** Clean VBScript startup launcher referencing the permanent repository path.\n\n"
        f"### 📥 Downloads:\n"
        f"- **`CodexAutoResume.exe`**: Standalone portable single-file executable.\n"
        f"- **`CodexAutoResume-{tag}-Windows.zip`**: Complete release package with assets, VBScript helper, and bilingual documentation.\n"
    )

    release_info = create_github_release(token, repo, tag, title, notes)
    upload_url = release_info.get("upload_url", "")
    if not upload_url:
        raise ValueError(f"No upload_url found in release response: {release_info}")

    upload_release_asset(token, upload_url, exe_path)
    upload_release_asset(token, upload_url, zip_path)

    print("\n" + "=" * 60)
    print(f">>> RELEASE PUBLISHED SUCCESSFULLY!")
    print(f"Release Page: {release_info.get('html_url')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
