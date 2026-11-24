from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from typing import Any
import uuid

from .database import DatabaseService
from .models import MigrationRequest, ValidationError, sql_literal
from .native import NativeCommand, build_commands, native_environment
from .process_guard import ProcessGuard


ACTIVE_STATUSES = {"queued", "preparing", "exporting", "importing"}
NATIVE_ERROR = re.compile(r"\[错误\]|\bERROR\b|失败", re.IGNORECASE)
WARNING_COMPLETION = re.compile(
    r"^(?:\[\d+/\d+\]\s*)?成功(?:终止)?(?P<operation>导出|导入)\s*[,，]\s*"
    r"出现\s*(?P<count>[1-9]\d*)\s*个警告[。.]?$"
)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


class Job:
    def __init__(self, job_id: str, request: MigrationRequest, storage: Path, artifact_dir: Path):
        self.id = job_id
        self.directory = storage / job_id
        self.directory.mkdir(parents=True, exist_ok=False)
        self.artifact_dir = artifact_dir
        self.request = request.public()
        self.status = "queued"
        self.phase = "validate"
        self.created_at = timestamp()
        self.started_at: str | None = None
        self.finished_at: str | None = None
        self.error: str | None = None
        self.warning_count = 0
        self.native_progress: float | None = None
        self.process: subprocess.Popen[bytes] | None = None
        self.cancel_event = threading.Event()
        self.lock = threading.RLock()
        self.events: list[dict[str, Any]] = []
        self.secrets = [connection.password for connection in (request.source, request.target) if connection]
        self.phases = {"validate": "pending", "export": "pending" if request.source else "skipped", "import": "pending" if request.target else "skipped"}
        self.persist()

    def redact(self, value: str) -> str:
        for secret in sorted(self.secrets, key=len, reverse=True):
            if secret:
                value = value.replace(secret, "******")
        return value

    def public(self) -> dict[str, Any]:
        with self.lock:
            return {
                "id": self.id,
                "request": self.request,
                "status": self.status,
                "phase": self.phase,
                "phases": dict(self.phases),
                "created_at": self.created_at,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "error": self.error,
                "warning_count": self.warning_count,
                "native_progress": self.native_progress,
                "artifact_dir": str(self.artifact_dir),
                "dump_file": str(self.artifact_dir / "migration.dmp") if self.request["mode"] != "import" else self.request["dump_file"],
                "last_sequence": len(self.events),
            }

    def persist(self) -> None:
        with self.lock:
            write_json(self.directory / "job.json", self.public())

    def log(self, message: str, level: str = "info", *, phase: str | None = None) -> None:
        message = self.redact(message)
        with self.lock:
            event = {"sequence": len(self.events) + 1, "time": timestamp(), "level": level, "phase": phase or self.phase, "message": message}
            self.events.append(event)
            with (self.directory / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    def set_phase(self, phase: str, status: str) -> None:
        with self.lock:
            self.phase = phase
            self.status = status
            self.phases[phase] = "running"
            self.native_progress = None
            self.persist()


class JobCancelled(Exception):
    pass


class JobManager:
    def __init__(self, data_dir: Path, bin_dir: Path, database: DatabaseService):
        self.storage = data_dir / "jobs"
        self.storage.mkdir(parents=True, exist_ok=True)
        self.bin_dir = bin_dir
        self.database = database
        self.jobs: dict[str, Job] = {}
        self.lock = threading.RLock()
        self._recover()

    def _recover(self) -> None:
        for path in self.storage.glob("*/job.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if record.get("status") in ACTIVE_STATUSES:
                    record["status"] = "interrupted"
                    record["finished_at"] = timestamp()
                    record["error"] = "应用上次运行时中断。请检查目标库后重新创建任务。"
                    for phase, status in record.get("phases", {}).items():
                        if status == "running":
                            record["phases"][phase] = "failed"
                    write_json(path, record)
            except (OSError, ValueError, TypeError):
                continue

    @property
    def active(self) -> Job | None:
        with self.lock:
            return next((job for job in self.jobs.values() if job.status in ACTIVE_STATUSES), None)

    def start(self, request: MigrationRequest) -> dict[str, Any]:
        with self.lock:
            if self.active:
                raise ValidationError("已有任务正在运行，请等待完成或先停止当前任务")
            for name, needed in (("dexp.exe", request.source is not None), ("dimp.exe", request.target is not None)):
                if needed and not (self.bin_dir / name).is_file():
                    raise ValidationError(f"工具目录中缺少 {name}")
            job_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
            artifact_dir = request.output_dir / job_id
            job = Job(job_id, request, self.storage, artifact_dir)
            self.jobs[job_id] = job
            threading.Thread(target=self._run, args=(job, request), name=f"migration-{job_id}", daemon=True).start()
            return job.public()

    def _check_cancelled(self, job: Job) -> None:
        if job.cancel_event.is_set():
            raise JobCancelled()

    def _preflight(self, job: Job, request: MigrationRequest) -> MigrationRequest:
        canonical_connections = {}
        for label, config in (("源库", request.source), ("目标库", request.target)):
            if config is None:
                continue
            self._check_cancelled(job)
            job.log(f"正在验证{label}连接：{config.host}:{config.port}")
            with self.database.driver.connect(config) as connection:
                user = connection.query("SELECT USER FROM DUAL", maximum=1)[0][0] or config.username
                canonical_connections["source" if label == "源库" else "target"] = replace(config, username=user)
                if label == "源库":
                    rows = connection.query(f"SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER={sql_literal(request.source_schema)}")
                    existing = {row[0] for row in rows}
                    missing = [name for name in request.tables if name not in existing]
                    if missing:
                        names = "、".join(missing[:10])
                        raise ValidationError(f"源 Schema 中不存在或当前用户无权访问这些表：{names}")
                else:
                    schemas = self.database.schemas(connection, user)
                    if request.target_schema not in schemas:
                        raise ValidationError(f"目标 Schema「{request.target_schema}」不存在或无法访问，请先在目标库创建")
            job.log(f"{label}连接验证通过", "success")
        return replace(request, **canonical_connections)

    def _execute(self, job: Job, command: NativeCommand, parameter_file: Path, *, password_encoding: str = "gb18030") -> str | None:
        self._check_cancelled(job)
        parameter_file.write_bytes(("\n".join(command.file_parameters) + "\n").encode("gb18030"))
        label = "导出" if command.phase == "export" else "导入"
        job.set_phase(command.phase, "exporting" if command.phase == "export" else "importing")
        job.log(f"启动 {command.executable.name}，开始{label}")
        warnings_before = job.warning_count
        completion_warnings = 0
        native_error_seen = False
        process = None
        guard = None
        try:
            guard = ProcessGuard()
            with job.lock:
                self._check_cancelled(job)
                process = subprocess.Popen(
                    command.argv(parameter_file),
                    cwd=parameter_file.parent,
                    env=native_environment(self.bin_dir),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                job.process = process
                guard.attach(process)
            assert process.stdin is not None and process.stdout is not None
            try:
                # The official prompt accepts redirected stdin, including @, /,
                # spaces and quotes in passwords. No password is written to disk.
                process.stdin.write((command.connection.password + "\r\n").encode(password_encoding))
                process.stdin.close()
            except BrokenPipeError:
                pass
            pending = bytearray()
            # dimp switches its password input encoding to the dump encoding.
            # Buffer only the initial login messages for non-ASCII passwords.
            # A retry is permitted strictly before any verification/import
            # milestone, and only for its explicit initial login rejection.
            awaiting_login = command.phase == "import" and not command.connection.password.isascii() and password_encoding == "gb18030"
            login_lines: list[bytes] = []

            def record_line(line: bytes) -> None:
                nonlocal completion_warnings, native_error_seen
                message = self._native_line(job, line, command.phase)
                if NATIVE_ERROR.search(message):
                    native_error_seen = True
                summary = WARNING_COMPLETION.fullmatch(message)
                if summary and summary.group("operation") == label:
                    completion_warnings = max(completion_warnings, int(summary.group("count")))

            def accept_line(line: bytes) -> None:
                nonlocal awaiting_login
                if awaiting_login:
                    login_lines.append(line)
                    message = line.decode("gb18030", errors="replace")
                    if re.search(r"开始校验文件MD5|导入文件校验MD5正常|导入表[:：]|开始导入|成功导入", message) or sum(map(len, login_lines)) > 1048576:
                        awaiting_login = False
                        for saved in login_lines:
                            record_line(saved)
                        login_lines.clear()
                else:
                    record_line(line)

            while True:
                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                pending.extend(chunk)
                lines = re.split(rb"[\r\n]+", pending)
                pending = bytearray(lines.pop())
                for line in lines:
                    accept_line(line)
                if len(pending) > 131072:
                    accept_line(bytes(pending))
                    pending.clear()
            if pending:
                accept_line(bytes(pending))
            result = process.wait()
            self._check_cancelled(job)
            if awaiting_login:
                initial_output = b"\n".join(login_lines).decode("gb18030", errors="replace")
                if result != 0 and re.search(r"Error\s*Code\s*:\s*-2501", initial_output, re.IGNORECASE) and "登录失败" in initial_output and re.search(r"导入文件编码[:：]\s*PG_UTF8", initial_output):
                    job.log("转储文件使用 UTF-8 编码，正在调整密码输入编码并重新连接。")
                    return "utf-8"
                for saved in login_lines:
                    record_line(saved)
            if result != 0:
                # Exit code 2 also occurs on login failures. Accept it only
                # after the matching final success-with-warnings summary,
                # and never when native output contains an actual error.
                if result != 2 or not completion_warnings or native_error_seen:
                    raise RuntimeError(f"{command.executable.name} {label}失败（退出码 {result}），请查看日志中的达梦错误信息")
                job.log(f"{label}已完成，官方工具返回警告退出码 2；请检查上方警告。", "warning")
            if completion_warnings:
                job.warning_count = max(job.warning_count, warnings_before + completion_warnings)
            job.phases[command.phase] = "completed"
            has_warnings = job.warning_count > warnings_before
            job.log(f"{label}阶段完成" + ("，有警告" if has_warnings else ""), "warning" if has_warnings else "success")
            job.persist()
        finally:
            if process:
                if process.poll() is None:
                    self._terminate(process)
                if process.stdout:
                    process.stdout.close()
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
            if guard:
                guard.close()
            with job.lock:
                job.process = None
            parameter_file.unlink(missing_ok=True)

    def _native_line(self, job: Job, raw: bytes, phase: str) -> str:
        message = job.redact(raw.decode("gb18030", errors="replace").strip())
        if not message:
            return ""
        level = "info"
        if re.search(r"\[警告\]|\bWARNING\b", message, re.IGNORECASE):
            level = "warning"
            job.warning_count += 1
        summary = WARNING_COMPLETION.fullmatch(message)
        if summary:
            level = "warning"
            job.warning_count = max(job.warning_count, int(summary.group("count")))
        if NATIVE_ERROR.search(message):
            level = "error"
        if re.search(r"导出|导入|进度|export|import", message, re.IGNORECASE):
            percent = re.search(r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*%", message)
            if percent and 0 <= float(percent.group(1)) <= 100:
                job.native_progress = float(percent.group(1))
        job.log(message, level, phase=phase)
        return message

    def _run(self, job: Job, request: MigrationRequest) -> None:
        final_status = "failed"
        try:
            job.started_at = timestamp()
            job.set_phase("validate", "preparing")
            job.log(f"任务已创建：{'指定表迁移' if request.mode == 'migrate' else '仅导出' if request.mode == 'export' else '从文件导入'}")
            request = self._preflight(job, request)
            job.request = request.public()
            self._check_cancelled(job)
            job.phases["validate"] = "completed"
            job.artifact_dir.mkdir(parents=True, exist_ok=False)
            job.log(f"工作目录：{job.artifact_dir}")
            for command in build_commands(request, self.bin_dir, job.artifact_dir):
                self._check_cancelled(job)
                if command.phase == "import" and request.mode == "migrate":
                    dump = job.artifact_dir / "migration.dmp"
                    if not dump.is_file() or dump.stat().st_size == 0:
                        raise RuntimeError("导出未生成有效的 migration.dmp 文件，已停止后续导入")
                parameter_file = job.artifact_dir / f"{command.phase}.par"
                retry_encoding = self._execute(job, command, parameter_file)
                if retry_encoding:
                    self._execute(job, command, parameter_file, password_encoding=retry_encoding)
            final_status = "warning" if job.warning_count else "success"
            job.phase = "done"
            job.native_progress = None
            if job.warning_count:
                job.log("任务完成，存在警告；请检查日志并核对目标库数据" if request.mode != "export" else "导出完成，存在警告，转储文件已保留", "warning")
            else:
                job.log("任务完成，请核对目标库数据" if request.mode != "export" else "导出完成，转储文件已保留", "success")
        except JobCancelled:
            final_status = "cancelled"
            if job.phases.get(job.phase) == "running":
                job.phases[job.phase] = "cancelled"
            job.log("任务已停止。已导入的数据会保留，请检查目标库后再重试。", "warning")
        except Exception as exc:
            final_status = "failed"
            job.error = job.redact(str(exc))
            if job.phases.get(job.phase) == "running":
                job.phases[job.phase] = "failed"
            job.log(job.error, "error")
        finally:
            with job.lock:
                job.finished_at = timestamp()
                job.status = final_status
                job.persist()
                job.secrets.clear()

    @staticmethod
    def _terminate(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
        else:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def cancel(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job or job.status not in ACTIVE_STATUSES:
                raise ValidationError("该任务已经结束")
            job.cancel_event.set()
            with job.lock:
                process = job.process
            if process:
                self._terminate(process)
            job.log("收到停止请求，正在结束任务", "warning")
            return job.public()

    def shutdown(self) -> None:
        job = self.active
        if job:
            self.cancel(job.id)
            deadline = time.monotonic() + 12
            while job.status in ACTIVE_STATUSES and time.monotonic() < deadline:
                time.sleep(0.1)

    def _validate_id(self, job_id: str) -> None:
        if not re.fullmatch(r"\d{8}_\d{6}_[a-f0-9]{8}", job_id):
            raise ValidationError("任务编号无效")

    def get(self, job_id: str, after: int = 0) -> dict[str, Any]:
        self._validate_id(job_id)
        with self.lock:
            job = self.jobs.get(job_id)
        if job:
            with job.lock:
                record = job.public()
                record["events"] = [event for event in job.events if event["sequence"] > after][:1000]
                return record
        directory = self.storage / job_id
        try:
            record = json.loads((directory / "job.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValidationError("任务不存在") from exc
        events = []
        path = directory / "events.jsonl"
        if path.is_file():
            with path.open(encoding="utf-8") as stream:
                for line in stream:
                    event = json.loads(line)
                    if event["sequence"] > after:
                        events.append(event)
                        if len(events) >= 1000:
                            break
        record["events"] = events
        return record

    def list(self) -> list[dict[str, Any]]:
        records = []
        for path in sorted(self.storage.glob("*/job.json"), reverse=True)[:200]:
            try:
                records.append(self.get(path.parent.name, after=2**53))
            except (OSError, ValueError, ValidationError):
                continue
        for record in records:
            record.pop("events", None)
        return records

    def log_text(self, job_id: str) -> str:
        self._validate_id(job_id)
        path = self.storage / job_id / "events.jsonl"
        if not path.is_file():
            raise ValidationError("任务日志不存在")
        lines = []
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                event = json.loads(line)
                lines.append(f"{event['time']} [{event['level'].upper()}] [{event['phase']}] {event['message']}")
        return "\n".join(lines)
