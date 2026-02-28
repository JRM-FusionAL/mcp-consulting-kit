#!/usr/bin/env python3
"""
launch.py - Cross-platform server launcher for mcp-consulting-kit
Works on Windows, Linux, and macOS

Usage:
  python3 launch.py           # start all servers
  python3 launch.py --stop    # stop all servers
  python3 launch.py --status  # check health of all servers
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ── Platform detection ────────────────────────────────────────────────────────

PLATFORM = platform.system()  # Windows / Linux / Darwin
IS_WINDOWS = PLATFORM == "Windows"
IS_MAC = PLATFORM == "Darwin"
IS_LINUX = PLATFORM == "Linux"

# ── Find Python executable ────────────────────────────────────────────────────

def find_python() -> str:
    for candidate in ["python3", "python"]:
        path = shutil.which(candidate)
        if path:
            # Verify it's Python 3
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True, text=True
                )
                if "Python 3" in result.stdout + result.stderr:
                    return path
            except Exception:
                pass
    # Windows fallback
    if IS_WINDOWS:
        for candidate in [
            r"c:\python314\python.exe",
            r"c:\python313\python.exe",
            r"c:\python312\python.exe",
            r"c:\python311\python.exe",
        ]:
            if Path(candidate).exists():
                return candidate
    raise RuntimeError("Python 3 not found. Install from https://python.org")


PYTHON = find_python()

# ── Find repo root ────────────────────────────────────────────────────────────

def find_repo_root() -> Path:
    """Find mcp-consulting-kit repo root regardless of where script is run from."""
    # Check if we're already in it
    candidates = [
        Path(__file__).resolve().parent,
        Path.cwd(),
        Path.home() / "Projects" / "mcp-consulting-kit",
        Path.home() / "mcp-consulting-kit",
        Path("/mnt/c/Users") / os.environ.get("USERNAME", "") / "Projects" / "mcp-consulting-kit",
    ]
    for c in candidates:
        if (c / "showcase-servers").exists():
            return c
    raise RuntimeError(
        "Cannot find mcp-consulting-kit repo root. "
        "Run this script from inside the repo directory."
    )


REPO_ROOT = find_repo_root()
SHOWCASE = REPO_ROOT / "showcase-servers"

# ── Server definitions ────────────────────────────────────────────────────────

SERVERS = [
    {"name": "Business Intelligence MCP", "dir": SHOWCASE / "business-intelligence-mcp", "port": 8101},
    {"name": "API Integration Hub",        "dir": SHOWCASE / "api-integration-hub",        "port": 8102},
    {"name": "Content Automation MCP",     "dir": SHOWCASE / "content-automation-mcp",     "port": 8103},
]


def load_env(env_path: Path) -> dict:
    """Load .env file into a dict."""
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip()
    return env


def start_server(server: dict) -> subprocess.Popen | None:
    """Start a single server in a new terminal window or background process."""
    directory = server["dir"]
    port = server["port"]
    name = server["name"]

    if not directory.exists():
        print(f"  ⚠️  Directory not found: {directory}")
        return None

    env = {**os.environ, **load_env(directory / ".env")}
    cmd = [PYTHON, "-m", "uvicorn", "main:app",
           "--host", "0.0.0.0", "--port", str(port), "--reload"]

    if IS_WINDOWS:
        proc = subprocess.Popen(
            ["cmd", "/k", " ".join([f'cd /d "{directory}"'] + ["&&"] + cmd)],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            env=env,
        )
    elif IS_MAC:
        script = f'cd "{directory}" && {" ".join(cmd)}'
        proc = subprocess.Popen(
            ["osascript", "-e",
             f'tell application "Terminal" to do script "{script}"'],
            env=env,
        )
    else:
        # Linux — run in background, log to file
        log_file = directory / f"server-{port}.log"
        proc = subprocess.Popen(
            cmd,
            cwd=str(directory),
            env=env,
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
        )

    print(f"  ✅ {name} → http://localhost:{port} (pid {proc.pid})")
    return proc


def check_health(port: int) -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(
            f"http://localhost:{port}/health", timeout=3
        ) as r:
            return r.status == 200
    except Exception:
        return False


def status():
    print("\nServer health:")
    for s in SERVERS:
        ok = check_health(s["port"])
        icon = "✅" if ok else "❌"
        print(f"  {icon} {s['name']} → http://localhost:{s['port']}/health")
    print()


def start_all():
    print(f"\n🚀 Starting mcp-consulting-kit servers")
    print(f"   Platform: {PLATFORM} | Python: {PYTHON}")
    print(f"   Repo: {REPO_ROOT}\n")

    procs = []
    for server in SERVERS:
        proc = start_server(server)
        if proc:
            procs.append(proc)
        time.sleep(0.5)

    print(f"\n⏳ Waiting for servers to come up...")
    time.sleep(5)
    status()

    if not IS_WINDOWS:
        # On Linux/Mac keep process alive so Ctrl+C stops all servers
        print("Press Ctrl+C to stop all servers\n")
        try:
            for proc in procs:
                proc.wait()
        except KeyboardInterrupt:
            print("\n\nStopping all servers...")
            for proc in procs:
                proc.terminate()
            print("Done.")


def main():
    parser = argparse.ArgumentParser(description="mcp-consulting-kit server launcher")
    parser.add_argument("--stop", action="store_true", help="Stop all running servers")
    parser.add_argument("--status", action="store_true", help="Check server health")
    args = parser.parse_args()

    if args.status:
        status()
    elif args.stop:
        if IS_WINDOWS:
            subprocess.run(
                ["powershell", "-Command",
                 "Get-Process python,python3,uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force"],
                capture_output=True
            )
        else:
            subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
        print("✅ Servers stopped")
    else:
        start_all()


if __name__ == "__main__":
    main()
