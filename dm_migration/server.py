from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import tempfile
from typing import Any
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .database import DatabaseError, DatabaseService
from .jobs import JobManager, write_json
from .models import Connection, MigrationRequest, ValidationError
from .native import build_commands, tool_status


class Application:
    def __init__(self, root: Path, static_dir: Path, *, data_dir: Path | None = None, bundled_bin_dir: Path | None = None):
        self.root = root
        self.static_dir = static_dir
        self.data_dir = data_dir or root / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.data_dir / "settings.json"
        self.bundled_bin_dir = bundled_bin_dir.resolve() if bundled_bin_dir and bundled_bin_dir.is_dir() else None
        default_bin_dir = root / "bin"
        if not default_bin_dir.is_dir() and self.bundled_bin_dir:
            default_bin_dir = self.bundled_bin_dir
        self.settings: dict[str, Any] = {}
        if self.config_file.is_file():
            try:
                self.settings = json.loads(self.config_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        self.bin_dir = Path(self.settings.get("bin_dir", str(default_bin_dir))).resolve()
        self.database = DatabaseService(self.bin_dir)
        self.jobs = JobManager(self.data_dir, self.bin_dir, self.database)
        self.token = secrets.token_urlsafe(32)
        self.server: ThreadingHTTPServer | None = None
        self._tool_status: dict[str, Any] | None = None
        self._tool_lock = threading.Lock()
        self._dialog_lock = threading.Lock()

    def bootstrap(self) -> dict[str, Any]:
        return {
            "version": __version__,
            "root": str(self.root),
            "output_dir": str(self.root / "output"),
            "settings": self.settings,
            "tools": self.get_tools(),
            "active_job": self.jobs.active.public() if self.jobs.active else None,
        }

    def get_tools(self, *, refresh: bool = False) -> dict[str, Any]:
        with self._tool_lock:
            if self._tool_status is None or refresh:
                self._tool_status = tool_status(self.bin_dir)
            return self._tool_status

    def save_settings(self, raw: Any) -> dict[str, Any]:
        if self.jobs.active:
            raise ValidationError("任务运行期间不能修改工具目录")
        if not isinstance(raw, dict):
            raise ValidationError("设置格式不正确")
        bin_value = raw.get("bin_dir", str(self.bin_dir))
        if not isinstance(bin_value, str):
            raise ValidationError("工具目录格式不正确")
        bin_dir = Path(bin_value).expanduser().resolve()
        if not bin_dir.is_dir():
            raise ValidationError("工具目录不存在")
        profiles: dict[str, Any] = {}
        for role in ("source", "target"):
            value = raw.get(role)
            if isinstance(value, dict):
                profile = {key: value[key] for key in ("host", "port", "username") if key in value}
                profiles[role] = profile
        self.settings = dict(profiles)
        # A one-file build extracts tools into a different temporary directory
        # on every launch. Save only an explicit external tools directory.
        if bin_dir != self.bundled_bin_dir:
            self.settings["bin_dir"] = str(bin_dir)
        write_json(self.config_file, self.settings)
        self.bin_dir = bin_dir
        self.database = DatabaseService(bin_dir)
        self.jobs.bin_dir = bin_dir
        self.jobs.database = self.database
        self._tool_status = None
        return self.bootstrap()

    def dialog(self, kind: str, initial: str = "") -> dict[str, str]:
        if kind not in {"directory", "file"}:
            raise ValidationError("选择器类型无效")
        if not self._dialog_lock.acquire(blocking=False):
            raise ValidationError("已有文件选择窗口打开")
        try:
            with tempfile.TemporaryDirectory(prefix="dm_gui_dialog_") as directory:
                result_file = Path(directory) / "selection.json"
                if getattr(sys, "frozen", False):
                    command = [sys.executable]
                else:
                    command = [sys.executable, "-X", "utf8", str(self.root / "app.py")]
                command.extend(["--dialog", kind, "--initial", initial, "--dialog-result", str(result_file)])
                result = subprocess.run(command, cwd=self.root, capture_output=True, timeout=300, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode != 0 or not result_file.is_file():
                    raise ValidationError("无法打开文件选择窗口，请直接输入完整路径")
                return json.loads(result_file.read_text(encoding="utf-8"))
        finally:
            self._dialog_lock.release()

    def open_directory(self, raw: Any) -> dict[str, bool]:
        if not isinstance(raw, dict):
            raise ValidationError("目录请求格式无效")
        if raw.get("job_id"):
            record = self.jobs.get(raw["job_id"])
            path = Path(record["artifact_dir"])
        else:
            path = self.bin_dir if raw.get("kind") == "bin" else self.root / "output"
        if not path.is_dir():
            raise ValidationError("工作目录尚未生成")
        if os.name == "nt":
            os.startfile(str(path))
        return {"opened": True}


class Handler(BaseHTTPRequestHandler):
    server_version = "DamengMigration"
    protocol_version = "HTTP/1.1"

    @property
    def app(self) -> Application:
        return self.server.app  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        # Request bodies and credentials never enter console/access logs.
        pass

    def _send(self, content: bytes, content_type: str, status: int = 200, *, attachment: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if attachment:
            self.send_header("Content-Disposition", f'attachment; filename="{attachment}"')
        self.end_headers()
        self.wfile.write(content)

    def _json(self, value: Any, status: int = 200) -> None:
        self._send(json.dumps(value, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def _local_request(self) -> bool:
        expected = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != expected:
            self._json({"error": "请使用应用启动时打开的本地地址"}, 403)
            return False
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{expected}":
            self._json({"error": "不接受来自其他网站的请求"}, 403)
            return False
        return True

    def _authorized(self) -> bool:
        token = self.headers.get("X-App-Token", "")
        if not hmac.compare_digest(token, self.app.token):
            self._json({"error": "会话已失效，请通过启动程序重新打开界面", "code": "session_expired"}, 403)
            return False
        return True

    def do_GET(self) -> None:
        if not self._local_request():
            return
        parsed = urlsplit(self.path)
        path = parsed.path
        try:
            if path.startswith("/api/"):
                if not self._authorized():
                    return
                if path == "/api/bootstrap":
                    return self._json(self.app.bootstrap())
                if path == "/api/tools":
                    return self._json(self.app.get_tools(refresh=True))
                if path == "/api/jobs":
                    return self._json({"jobs": self.app.jobs.list()})
                if path.startswith("/api/jobs/"):
                    parts = path.strip("/").split("/")
                    job_id = parts[2]
                    if len(parts) == 4 and parts[3] == "log":
                        return self._send(self.app.jobs.log_text(job_id).encode("utf-8-sig"), "text/plain; charset=utf-8", attachment=f"{job_id}.log")
                    if len(parts) == 3:
                        after = int(parse_qs(parsed.query).get("after", ["0"])[0])
                        return self._json(self.app.jobs.get(job_id, max(0, after)))
                return self._json({"error": "接口不存在"}, 404)
            relative = "index.html" if path == "/" else path.lstrip("/")
            file = (self.app.static_dir / relative).resolve()
            if not file.is_relative_to(self.app.static_dir.resolve()) or not file.is_file():
                return self._json({"error": "文件不存在"}, 404)
            # Windows registry mappings can classify .js as text/plain.
            content_type = {".js":"text/javascript", ".css":"text/css", ".html":"text/html", ".svg":"image/svg+xml"}.get(file.suffix) or mimetypes.guess_type(str(file))[0] or "application/octet-stream"
            if file.suffix in {".html", ".js", ".css", ".svg"}:
                content_type += "; charset=utf-8"
            self._send(file.read_bytes(), content_type)
        except (ValidationError, ValueError) as exc:
            self._json({"error": str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self._json({"error": "读取失败，请重新启动应用后再试"}, 500)

    def do_POST(self) -> None:
        if not self._local_request() or not self._authorized():
            return
        body: Any = None
        try:
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0]
            if content_type != "application/json":
                raise ValidationError("请求必须使用 JSON 格式")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4 * 1024 * 1024:
                raise ValidationError("请求大小无效")
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            path = urlsplit(self.path).path
            if path == "/api/database/test":
                return self._json(self.app.database.test(body.get("connection")))
            if path == "/api/database/tables":
                return self._json(self.app.database.tables(body.get("connection"), body.get("schema")))
            if path == "/api/settings":
                return self._json(self.app.save_settings(body))
            if path == "/api/dialog":
                return self._json(self.app.dialog(body.get("kind", ""), body.get("initial", "")))
            if path == "/api/open-directory":
                return self._json(self.app.open_directory(body))
            if path in {"/api/jobs", "/api/preview"}:
                preview_body = {**body, "destructive_confirmation": body.get("target_schema")} if path == "/api/preview" else body
                request = MigrationRequest.parse(preview_body, self.app.root / "output")
                if path == "/api/preview":
                    artifact_dir = request.output_dir / "<任务编号>"
                    commands = build_commands(request, self.app.bin_dir, artifact_dir)
                    return self._json({"commands": [command.preview() for command in commands]})
                return self._json(self.app.jobs.start(request), 201)
            if path.startswith("/api/jobs/") and path.endswith("/cancel"):
                return self._json(self.app.jobs.cancel(path.strip("/").split("/")[2]))
            if path == "/api/quit":
                if self.app.jobs.active:
                    raise ValidationError("任务运行中，请先停止当前任务再退出")
                self._json({"stopped": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            self._json({"error": "接口不存在"}, 404)
        except (ValidationError, DatabaseError, ValueError, TypeError, AttributeError) as exc:
            message = str(exc)
            if isinstance(body, dict):
                for role in ("connection", "source", "target"):
                    value = body.get(role)
                    if isinstance(value, dict) and isinstance(value.get("password"), str) and value["password"]:
                        message = message.replace(value["password"], "******")
            self._json({"error": message}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self._json({"error": "操作失败，请检查目录是否可写或重新启动应用"}, 500)


def create_server(app: Application, port: int = 0) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.app = app  # type: ignore[attr-defined]
    app.server = server
    return server
