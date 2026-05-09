#!/usr/bin/env python3
"""Run nanobot weixin login and render the QR code in the terminal."""
import json
import os
import subprocess
import sys
from pathlib import Path


def render_qr(url: str) -> None:
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        pass


def get_state_dir(config_path: str) -> Path:
    """Read stateDir from config.json, fall back to ~/.nanobot/weixin."""
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        state_dir = cfg.get("channels", {}).get("weixin", {}).get("stateDir", "")
        if state_dir:
            return Path(state_dir).expanduser()
    except Exception:
        pass
    return Path.home() / ".nanobot" / "weixin"


def main() -> None:
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = os.path.join(project_dir, "config.json")

    state_dir = get_state_dir(config)
    account_file = state_dir / "account.json"
    force = False
    if account_file.exists():
        print(f"已找到微信登录状态：{account_file}")
        answer = input("重新登录？[y/N] ").strip().lower()
        if answer != "y":
            print("跳过登录。")
            sys.exit(0)
        force = True

    cmd = ["nanobot", "channels", "login", "weixin", "--config", config]
    if force:
        cmd.append("--force")

    # Use a PTY so nanobot thinks it's connected to a real terminal,
    # preventing buffering and ensuring the login URL is printed.
    import pty
    import select

    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
    )
    os.close(slave_fd)

    qr_shown = False
    buf = ""
    while True:
        try:
            rlist, _, _ = select.select([master_fd], [], [], 0.1)
        except (ValueError, OSError):
            break
        if rlist:
            try:
                chunk = os.read(master_fd, 4096).decode("utf-8", errors="replace")
            except OSError:
                break
            sys.stdout.write(chunk)
            sys.stdout.flush()
            buf += chunk
            if not qr_shown and "Login URL:" in buf:
                for line in buf.splitlines():
                    if "Login URL:" in line:
                        url = line.split("Login URL:", 1)[-1].strip()
                        if url:
                            render_qr(url)
                        qr_shown = True
                        break
        if proc.poll() is not None:
            # Drain remaining output
            try:
                while True:
                    rlist, _, _ = select.select([master_fd], [], [], 0.05)
                    if not rlist:
                        break
                    chunk = os.read(master_fd, 4096).decode("utf-8", errors="replace")
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
            except OSError:
                pass
            break

    os.close(master_fd)
    sys.exit(proc.wait())


if __name__ == "__main__":
    main()
