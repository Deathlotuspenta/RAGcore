#!/usr/bin/env python3
"""RAGcore desktop launcher — start bundled uvicorn, open browser, show status window."""

from __future__ import annotations

import os
import platform
import signal
import subprocess
import sys
import time
import tkinter as tk
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk

PORT = int(os.getenv("PORT", "8765"))
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}"
HEALTH_URL = f"{URL}/health"
PID_FILE_NAME = "ragcore.pid"


def bundle_resources_dir() -> Path:
    explicit = os.getenv("RAGCORE_BUNDLE_DIR")
    if explicit:
        return Path(explicit).resolve()
    exe = Path(sys.argv[0]).resolve()
    contents = exe.parent.parent
    if contents.name == "Contents" and (contents / "Resources").is_dir():
        return contents / "Resources"
    return exe.parent.resolve()


def default_data_dir() -> Path:
    explicit = os.getenv("RAGCORE_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser()
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home()
        return base / "RAGcore"
    return Path.home() / "Library" / "Application Support" / "RAGcore"


def python_executable(resources: Path) -> Path:
    if platform.system() == "Windows":
        return resources / "python" / "python.exe"
    return resources / "python" / "bin" / "python3"


def pid_file(data_dir: Path) -> Path:
    return data_dir / PID_FILE_NAME


def is_server_up() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=1) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def read_pid(data_dir: Path) -> int | None:
    path = pid_file(data_dir)
    if not path.is_file():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if platform.system() == "Windows":
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}"],
                text=True,
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
            return str(pid) in out
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def open_browser() -> None:
    if platform.system() == "Darwin":
        subprocess.run(["open", URL], check=False)
    elif platform.system() == "Windows":
        os.startfile(URL)  # type: ignore[attr-defined]
    else:
        webbrowser.open(URL)


def wait_for_server(seconds: float = 60.0) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if is_server_up():
            return True
        time.sleep(0.25)
    return False


def start_server(resources: Path, data_dir: Path) -> subprocess.Popen:
    py = python_executable(resources)
    backend = resources / "backend"
    if not py.is_file():
        raise FileNotFoundError(f"未找到内置 Python: {py}")
    if not backend.is_dir():
        raise FileNotFoundError(f"未找到后端目录: {backend}")

    data_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "RAGCORE_BUNDLE": "1",
            "RAGCORE_BUNDLE_DIR": str(resources),
            "RAGCORE_DATA_DIR": str(data_dir),
            "SERVE_STATIC": "true",
            "PORT": str(PORT),
            "PYTHONPATH": str(backend),
        }
    )

    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout = open(log_dir / "ragcore.out.log", "a", encoding="utf-8")
    stderr = open(log_dir / "ragcore.err.log", "a", encoding="utf-8")

    creationflags = 0
    if platform.system() == "Windows" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        [str(py), "-m", "uvicorn", "server.main:app", "--host", HOST, "--port", str(PORT)],
        cwd=str(backend),
        env=env,
        stdout=stdout,
        stderr=stderr,
        creationflags=creationflags,
    )
    pid_file(data_dir).write_text(str(proc.pid), encoding="utf-8")
    return proc


def stop_server(pid: int, data_dir: Path) -> None:
    if not process_alive(pid):
        pid_file(data_dir).unlink(missing_ok=True)
        return
    if platform.system() == "Windows":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
    else:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            if process_alive(pid):
                os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    pid_file(data_dir).unlink(missing_ok=True)


class StatusWindow:
    def __init__(self, data_dir: Path, server_pid: int | None, owns_server: bool) -> None:
        self.data_dir = data_dir
        self.server_pid = server_pid
        self.owns_server = owns_server
        self._closing = False

        self.root = tk.Tk()
        self.root.title("RAGcore")
        self.root.geometry("420x260")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit)

        pad = {"padx": 16, "pady": 6}
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="RAGcore 笔记知识库", font=("", 16, "bold")).pack(anchor=tk.W, **pad)

        self.status_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.status_var, font=("", 12)).pack(anchor=tk.W, **pad)

        ttk.Label(frame, text=f"访问地址：{URL}", foreground="#2563eb").pack(anchor=tk.W, **pad)
        ttk.Label(
            frame,
            text="关闭此窗口将停止后台服务（笔记数据已保存在用户目录）",
            wraplength=380,
            foreground="#666",
        ).pack(anchor=tk.W, **pad)

        log_dir = data_dir / "logs"
        ttk.Label(frame, text=f"日志：{log_dir}", foreground="#888", wraplength=380).pack(
            anchor=tk.W, **pad
        )

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_row, text="打开浏览器", command=open_browser).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="退出并停止服务", command=self.on_quit).pack(side=tk.LEFT)

        self._poll_status()

    def _poll_status(self) -> None:
        if self._closing:
            return
        if is_server_up():
            self.status_var.set("● 服务运行中")
        elif self.server_pid and process_alive(self.server_pid):
            self.status_var.set("● 正在启动，请稍候…")
        else:
            self.status_var.set("● 服务未响应，请查看日志")
        self.root.after(1000, self._poll_status)

    def on_quit(self) -> None:
        if self._closing:
            return
        if self.owns_server and self.server_pid:
            if messagebox.askyesno("退出 RAGcore", "确定退出并停止后台服务吗？"):
                self._closing = True
                stop_server(self.server_pid, self.data_dir)
                self.root.destroy()
        else:
            self._closing = True
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    resources = bundle_resources_dir()
    data_dir = default_data_dir()

    server_pid: int | None = None
    owns_server = False

    existing = read_pid(data_dir)
    if is_server_up():
        server_pid = existing if existing and process_alive(existing) else None
    elif existing and process_alive(existing):
        if wait_for_server(15.0):
            server_pid = existing
        else:
            stop_server(existing, data_dir)
            existing = None

    if server_pid is None:
        try:
            proc = start_server(resources, data_dir)
            server_pid = proc.pid
            owns_server = True
        except FileNotFoundError as exc:
            messagebox.showerror("RAGcore 启动失败", str(exc))
            return 1

        if not wait_for_server(60.0):
            messagebox.showerror(
                "RAGcore 启动失败",
                f"服务未在 60 秒内就绪。\n请查看日志：\n{data_dir / 'logs'}",
            )
            if owns_server and server_pid:
                stop_server(server_pid, data_dir)
            return 1

    open_browser()
    StatusWindow(data_dir, server_pid, owns_server).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
