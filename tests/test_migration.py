from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from dm_migration.database import DatabaseError
from dm_migration.jobs import ACTIVE_STATUSES, JobManager
from dm_migration.models import MigrationRequest, ValidationError
from dm_migration.native import build_commands
from dm_migration.server import Application, create_server


ROOT = Path(__file__).resolve().parents[1]
SECRET = 'DoNotPersist_123@/ ;"中文'


def fixture(output: Path) -> dict:
    return {
        "mode":"migrate",
        "source":{"host":"127.0.0.1", "port":5236, "username":"SYSDBA", "password":SECRET},
        "target":{"host":"127.0.0.1", "port":5237, "username":"SYSDBA", "password":SECRET},
        "source_schema":"SOURCE",
        "target_schema":"TARGET",
        "tables":["ITEMS"],
        "output_dir":str(output),
    }


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def query(self, sql, **kwargs):
        if sql == "SELECT USER FROM DUAL":
            return [["SYSDBA"]]
        if "FROM ALL_TABLES" in sql:
            return [["ITEMS"]]
        return []


class FakeDriver:
    def connect(self, config):
        if config.host == "unreachable.example":
            raise DatabaseError("connection rejected " + config.password)
        return FakeConnection()


class FakeDatabase:
    driver = FakeDriver()

    def schemas(self, connection, username):
        return ["SOURCE", "TARGET", "SYSDBA"]


HELPER = r'''
import pathlib, sys, time
sys.stdout.reconfigure(encoding="gb18030")
scenario, phase, directory = sys.argv[1:4]
input_bytes = sys.stdin.buffer.readline()
input_utf8 = False
if phase == "import" and scenario in ("encoding_login", "encoding_after_start"):
    try:
        password = input_bytes.decode("utf-8").rstrip("\r\n")
        input_utf8 = True
    except UnicodeDecodeError:
        password = input_bytes.decode("gb18030").rstrip("\r\n")
else:
    password = input_bytes.decode("gb18030").rstrip("\r\n")
assert password and not any(password in value for value in sys.argv)
print("password echo: " + password, flush=True)
path = pathlib.Path(directory)
if phase == "import" and scenario in ("encoding_login", "encoding_after_start"):
    attempt = path / "import_attempts"
    count = int(attempt.read_text()) if attempt.exists() else 0
    attempt.write_text(str(count + 1))
    if not input_utf8:
        print("本地编码：PG_GBK, 导入文件编码：PG_UTF8", flush=True)
        if scenario == "encoding_after_start":
            print("开始校验文件MD5", flush=True)
        print("[警告]Error Code:-2501,用户名或密码错误", flush=True)
        print("[警告]登录失败，请验证用户名密码是否正确", flush=True)
        sys.exit(2)
if scenario == "slow":
    print("worker-ready", flush=True)
    time.sleep(20)
if phase == "export":
    if scenario == "export_failure":
        print("[错误] export rejected", flush=True)
        sys.exit(4)
    if scenario != "missing_dump":
        (path / "migration.dmp").write_bytes(b"fake-dump")
elif phase == "import":
    (path / "import_started").write_text("yes")
    if scenario == "import_failure":
        print("[错误] import rejected", flush=True)
        sys.exit(4)
if phase == "export" and scenario in ("export_warning", "warning_both_stages"):
    count = 2 if scenario == "warning_both_stages" else 1
    print("[警告]导出时出现对象警告", flush=True)
    print(f"成功终止导出, 出现{count}个警告", flush=True)
    sys.exit(2)
if phase == "import" and scenario in (
    "import_warning", "warning_both_stages", "import_warning_summary_only",
    "warning_without_completion", "object_success_with_warning",
    "import_error_with_warning_summary", "import_error_after_warning_summary",
    "non_warning_exit_with_summary", "wrong_phase_summary",
):
    if scenario != "import_warning_summary_only":
        print("[警告]服务器与文件内数据的 CASE_SENSITIVE 参数不匹配", flush=True)
    if scenario == "import_error_with_warning_summary":
        print("[错误]Error Code:-6602,违反唯一性约束", flush=True)
    if scenario == "object_success_with_warning":
        print("[7/39][表: ITEMS]导入成功……", flush=True)
    if scenario not in ("warning_without_completion", "object_success_with_warning"):
        operation = "导出" if scenario == "wrong_phase_summary" else "导入"
        count = 2 if scenario == "import_warning_summary_only" else 1
        print("[39/39]整个导入过程共花费 17.917 s", flush=True)
        print(f"成功终止{operation}, 出现{count}个警告", flush=True)
    if scenario == "import_error_after_warning_summary":
        print("[错误]Error Code:-6602,违反唯一性约束", flush=True)
    print("dimp V8", flush=True)
    sys.exit(4 if scenario == "non_warning_exit_with_summary" else 2)
print("stage completed", flush=True)
'''


class FakeCommand:
    def __init__(self, phase, connection, helper, scenario, artifact_dir):
        self.phase = phase
        self.connection = connection
        self.executable = Path(sys.executable)
        self.file_parameters = ("TABLES=(SOURCE.ITEMS)",)
        self.helper = helper
        self.scenario = scenario
        self.artifact_dir = artifact_dir

    def argv(self, parameter_file):
        return [sys.executable, "-u", str(self.helper), self.scenario, self.phase, str(self.artifact_dir)]


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dm_validation_")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_destructive_strategy_requires_exact_schema_confirmation(self):
        for strategy in ("TRUNCATE", "REPLACE"):
            raw = fixture(self.root)
            raw["options"] = {"table_exists":strategy}
            with self.assertRaises(ValidationError):
                MigrationRequest.parse(raw, self.root)
            raw["destructive_confirmation"] = "target"
            with self.assertRaises(ValidationError):
                MigrationRequest.parse(raw, self.root)
            raw["destructive_confirmation"] = "TARGET"
            self.assertEqual(MigrationRequest.parse(raw, self.root).options.table_exists, strategy)

    def test_self_migration_is_rejected_even_with_different_login_names(self):
        raw = fixture(self.root)
        raw["target"].update(host="localhost", port=5236, username="OTHER_USER")
        raw["target_schema"] = "SOURCE"
        with self.assertRaises(ValidationError):
            MigrationRequest.parse(raw, self.root)

    def test_control_characters_and_command_syntax_in_host_are_rejected(self):
        for value in ("127.0.0.1@other", "127.0.0.1;DROP=Y", "http://localhost", "127.0.0.1\nFULL=Y"):
            raw = fixture(self.root)
            raw["source"]["host"] = value
            with self.assertRaises(ValidationError):
                MigrationRequest.parse(raw, self.root)
        raw = fixture(self.root)
        raw["source"]["password"] = "password\nsecond line"
        with self.assertRaises(ValidationError):
            MigrationRequest.parse(raw, self.root)

    def test_password_is_absent_from_native_argv_parameters_and_public_request(self):
        request = MigrationRequest.parse(fixture(self.root), self.root)
        commands = build_commands(request, self.root / "bin", self.root / "中文 路径")
        for command in commands:
            self.assertNotIn(SECRET, " ".join(command.argv(self.root / "export.par")))
            self.assertNotIn(SECRET, "\n".join(command.file_parameters))
            self.assertNotIn(SECRET, json.dumps(command.preview(), ensure_ascii=False))
        self.assertNotIn("password", json.dumps(request.public()))


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dm_worker_")
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("dexp.exe", "dimp.exe"):
            (self.bin / name).write_bytes(b"stub")
        self.helper = self.root / "helper.py"
        self.helper.write_text(HELPER, encoding="utf-8")
        self.manager = JobManager(self.root / "data", self.bin, FakeDatabase())
        self.scenario = "success"

        def commands(request, bin_dir, artifact_dir):
            return [FakeCommand(phase, connection, self.helper, self.scenario, artifact_dir)
                for phase, connection in (("export", request.source), ("import", request.target)) if connection]

        self.patcher = patch("dm_migration.jobs.build_commands", side_effect=commands)
        self.patcher.start()

    def tearDown(self):
        self.manager.shutdown()
        self.patcher.stop()
        self.temp.cleanup()

    def start(self, raw=None):
        request = MigrationRequest.parse(raw or fixture(self.root / "output"), self.root / "output")
        return self.manager.start(request)

    def finish(self, record):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            record = self.manager.get(record["id"])
            if record["status"] not in ACTIVE_STATUSES:
                return record
            time.sleep(0.02)
        self.fail("Worker did not finish in time")

    def test_success_uses_stdin_redacts_logs_and_deletes_parameter_files(self):
        record = self.finish(self.start())
        self.assertEqual(record["status"], "success")
        self.assertIsNotNone(record["finished_at"])
        self.assertEqual(record["phases"]["export"], "completed")
        self.assertEqual(record["phases"]["import"], "completed")
        logs = self.manager.log_text(record["id"])
        self.assertIn("******", logs)
        self.assertNotIn(SECRET, logs)
        self.assertNotIn(SECRET, json.dumps(record, ensure_ascii=False))
        self.assertFalse(list(Path(record["artifact_dir"]).glob("*.par")))

    def test_export_failure_does_not_start_import(self):
        self.scenario = "export_failure"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["phases"]["import"], "pending")
        self.assertFalse((Path(record["artifact_dir"]) / "import_started").exists())

    def test_empty_or_missing_dump_does_not_start_import(self):
        self.scenario = "missing_dump"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "failed")
        self.assertIn("未生成有效", record["error"])
        self.assertFalse((Path(record["artifact_dir"]) / "import_started").exists())

    def test_import_failure_retains_dump_for_recovery(self):
        self.scenario = "import_failure"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "failed")
        self.assertTrue(Path(record["dump_file"]).is_file())
        self.assertFalse(list(Path(record["artifact_dir"]).glob("*.par")))

    def test_import_warning_exit_reports_completed_with_warning(self):
        self.scenario = "import_warning"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "warning")
        self.assertIsNone(record["error"])
        self.assertEqual(record["phases"]["import"], "completed")
        self.assertEqual(record["warning_count"], 1)
        self.assertTrue(Path(record["dump_file"]).is_file())
        self.assertFalse(list(Path(record["artifact_dir"]).glob("*.par")))
        self.assertFalse(any(event["level"] == "error" for event in record["events"]))
        self.assertIn("存在警告", self.manager.log_text(record["id"]))

    def test_export_warning_exit_can_continue_into_import(self):
        self.scenario = "export_warning"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "warning")
        self.assertEqual(record["phases"]["export"], "completed")
        self.assertEqual(record["phases"]["import"], "completed")
        self.assertTrue((Path(record["artifact_dir"]) / "import_started").is_file())

    def test_two_warning_stages_count_warnings_separately(self):
        self.scenario = "warning_both_stages"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "warning")
        self.assertEqual(record["warning_count"], 3)

    def test_warning_summary_without_details_still_counts(self):
        self.scenario = "import_warning_summary_only"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "warning")
        self.assertEqual(record["warning_count"], 2)
        self.assertTrue(any(event["level"] == "warning" and "出现2个警告" in event["message"] for event in record["events"]))

    def test_warning_exit_without_final_summary_is_failure(self):
        for scenario in ("warning_without_completion", "object_success_with_warning"):
            with self.subTest(scenario=scenario):
                self.scenario = scenario
                record = self.finish(self.start())
                self.assertEqual(record["status"], "failed")
                self.assertIn("退出码 2", record["error"])
                self.assertEqual(record["phases"]["import"], "failed")

    def test_warning_summary_does_not_hide_real_native_errors(self):
        for scenario in ("import_error_with_warning_summary", "import_error_after_warning_summary"):
            with self.subTest(scenario=scenario):
                self.scenario = scenario
                record = self.finish(self.start())
                self.assertEqual(record["status"], "failed")
                self.assertEqual(record["phases"]["import"], "failed")

    def test_warning_summary_does_not_accept_unexpected_exit_codes(self):
        self.scenario = "non_warning_exit_with_summary"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "failed")
        self.assertIn("退出码 4", record["error"])

    def test_wrong_operation_summary_does_not_complete_stage(self):
        self.scenario = "wrong_phase_summary"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["phases"]["import"], "failed")

    def test_unicode_password_encoding_retry_is_allowed_before_login_only(self):
        self.scenario = "encoding_login"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "success")
        self.assertEqual((Path(record["artifact_dir"]) / "import_attempts").read_text(), "2")
        self.assertEqual(record["warning_count"], 0)

    def test_encoding_retry_is_forbidden_after_verification_or_import_started(self):
        self.scenario = "encoding_after_start"
        record = self.finish(self.start())
        self.assertEqual(record["status"], "failed")
        self.assertEqual((Path(record["artifact_dir"]) / "import_attempts").read_text(), "1")

    def test_cancel_terminates_process_and_prevents_import(self):
        self.scenario = "slow"
        record = self.start()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            record = self.manager.get(record["id"])
            if any(event["message"] == "worker-ready" for event in record["events"]):
                break
            time.sleep(0.02)
        self.manager.cancel(record["id"])
        record = self.finish(record)
        self.assertEqual(record["status"], "cancelled")
        self.assertEqual(record["phases"]["import"], "pending")

    def test_concurrent_migration_is_rejected(self):
        self.scenario = "slow"
        record = self.start()
        with self.assertRaises(ValidationError):
            self.start()
        self.manager.cancel(record["id"])
        self.finish(record)

    def test_preflight_connection_error_is_redacted_before_persistence(self):
        raw = fixture(self.root / "output")
        raw["source"]["host"] = "unreachable.example"
        record = self.finish(self.start(raw))
        self.assertEqual(record["status"], "failed")
        self.assertNotIn(SECRET, record["error"])
        self.assertEqual(record["phases"]["export"], "pending")

    def test_restart_marks_incomplete_job_interrupted(self):
        record = self.finish(self.start())
        path = self.manager.storage / record["id"] / "job.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["status"] = "importing"
        data["phases"]["import"] = "running"
        path.write_text(json.dumps(data), encoding="utf-8")
        recovered = JobManager(self.root / "data", self.bin, FakeDatabase()).get(record["id"])
        self.assertEqual(recovered["status"], "interrupted")
        self.assertEqual(recovered["phases"]["import"], "failed")


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dm_http_")
        self.root = Path(self.temp.name)
        self.app = Application(self.root, ROOT / "web")
        self.server = create_server(self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def request(self, path, body=None, *, token=True, extra_headers=None):
        headers = {"X-App-Token":self.app.token} if token else {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        headers.update(extra_headers or {})
        request = urllib.request.Request(self.base + path,
            data=json.dumps(body).encode() if body is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, response.read(), response.headers
        except urllib.error.HTTPError as response:
            return response.code, response.read(), response.headers

    def test_api_requires_session_token_and_rejects_foreign_origin(self):
        self.assertEqual(self.request("/api/bootstrap", token=False)[0], 403)
        self.assertEqual(self.request("/api/settings", {}, extra_headers={"Origin":"https://example.com"})[0], 403)
        self.assertEqual(self.request("/api/bootstrap")[0], 200)

    def test_script_has_executable_mime_type_on_windows(self):
        code, content, headers = self.request("/app.js", token=False)
        self.assertEqual(code, 200)
        self.assertTrue(headers["Content-Type"].startswith("text/javascript"))

    def test_readonly_preview_does_not_require_destructive_confirmation(self):
        raw = fixture(self.root / "output")
        raw["options"] = {"table_exists":"REPLACE"}
        code, content, _ = self.request("/api/preview", raw)
        self.assertEqual(code, 200, content)
        self.assertNotIn(SECRET, content.decode())
        self.assertEqual(self.app.jobs.list(), [])
        code, content, _ = self.request("/api/jobs", raw)
        self.assertEqual(code, 400)
        self.assertIn("确认", content.decode())

    def test_settings_never_persist_passwords(self):
        raw = fixture(self.root)
        code, content, _ = self.request("/api/settings", {"bin_dir":str(self.root),"source":raw["source"],"target":raw["target"]})
        self.assertEqual(code, 200, content)
        persisted = self.app.config_file.read_text(encoding="utf-8")
        self.assertNotIn("password", persisted)
        self.assertNotIn(SECRET, persisted)

    def test_unknown_job_or_path_cannot_escape_storage(self):
        code, _, _ = self.request("/api/jobs/../../settings.json")
        self.assertIn(code, (400, 404))
        code, _, _ = self.request("/../../app.py", token=False)
        self.assertEqual(code, 404)


if __name__ == "__main__":
    unittest.main()
