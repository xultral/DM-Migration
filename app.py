from __future__ import annotations

import argparse
import atexit
import ctypes
import json
import os
from pathlib import Path
import sys
import threading
import webbrowser

from dm_migration.server import Application, create_server


def choose_path(kind: str, initial: str, result_file: Path | None = None) -> None:
    import tkinter as tk
    from tkinter import filedialog

    window = tk.Tk()
    window.withdraw()
    window.attributes("-topmost", True)
    options = {"parent": window}
    initial_path = Path(initial) if initial else Path.cwd()
    if initial_path.is_dir():
        options["initialdir"] = str(initial_path)
    elif initial_path.parent.is_dir():
        options["initialdir"] = str(initial_path.parent)
    if kind == "directory":
        result = filedialog.askdirectory(title="选择文件夹", **options)
    else:
        result = filedialog.askopenfilename(title="选择达梦导出文件", filetypes=[("达梦转储文件", "*.dmp"), ("所有文件", "*.*")], **options)
    window.destroy()
    data = json.dumps({"path": result}, ensure_ascii=False)
    if result_file:
        result_file.write_text(data, encoding="utf-8")
    elif sys.stdout:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(data)


def message_box(message: str) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, message, "达梦迁移工具", 0x10)
    elif sys.stderr:
        print(message, file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="达梦数据库可视化迁移工具")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--port", type=int, default=0, help="本地界面端口，默认自动分配")
    parser.add_argument("--dialog", choices=["directory", "file"])
    parser.add_argument("--initial", default="")
    parser.add_argument("--dialog-result", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--data-dir", type=Path, help="自定义任务记录目录")
    parser.add_argument("--launch-info", type=Path, help="将本次本地启动地址写入 JSON 文件，供自动化检查使用")
    arguments = parser.parse_args()
    if arguments.dialog:
        choose_path(arguments.dialog, arguments.initial, arguments.dialog_result)
        return 0
    frozen = getattr(sys, "frozen", False)
    root = Path(sys.executable).resolve().parent if frozen else Path(__file__).resolve().parent
    resource_root = Path(getattr(sys, "_MEIPASS", root))
    application = Application(root, resource_root / "web", data_dir=arguments.data_dir, bundled_bin_dir=resource_root / "bin" if frozen else None)
    server = create_server(application, arguments.port)
    atexit.register(application.jobs.shutdown)
    address = f"http://127.0.0.1:{server.server_port}/#token={application.token}"
    if arguments.launch_info:
        arguments.launch_info.parent.mkdir(parents=True, exist_ok=True)
        arguments.launch_info.write_text(json.dumps({"url": address, "pid": os.getpid()}), encoding="utf-8")
    if sys.stdout:
        print(f"达梦迁移工具已启动：{address}", flush=True)
        print("可在界面左下角退出；关闭浏览器不会中断任务。", flush=True)
    if not arguments.no_browser:
        threading.Timer(0.35, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        application.jobs.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        message_box(f"启动失败：{error}\n\n请将程序放在可写目录，保留旁边的 bin 文件夹。")
        raise SystemExit(1)
