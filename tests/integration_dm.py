"""Opt-in integration checks using isolated Dameng instances in ./testdb.

Run: python -X utf8 tests/integration_dm.py
The disposable credentials below are exclusively for these test instances.
"""
from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dm_migration.database import DatabaseService
from dm_migration.jobs import ACTIVE_STATUSES, JobManager
from dm_migration.models import Connection, MigrationRequest, ValidationError, sql_identifier
from dm_migration.native import native_environment


PASSWORD = "DMgui_Test_2468"
BIN = ROOT / "bin"
SCRATCH = ROOT / "testdb"
REPORT = ROOT / ".validation" / "integration"


def initialize(label: str, port: int, *, case_sensitive: int = 1) -> Path:
    if label == "source":
        path = SCRATCH
        name = "DM_GUI_TEST"
    else:
        path = SCRATCH / label
        name = "DM_GUI_" + label.upper()
    path.mkdir(parents=True, exist_ok=True)
    ini = path / name / "dm.ini"
    if not ini.is_file():
        result = subprocess.run([
            str(BIN / "dminit.exe"), f"PATH={path}", f"DB_NAME={name}",
            f"INSTANCE_NAME={name}", f"PORT_NUM={port}",
            f"SYSDBA_PWD={PASSWORD}", f"SYSAUDITOR_PWD={PASSWORD}",
            "LOG_SIZE=256", "BUFFER=128", "AUTO_ADJ_PARA=0", "CHARSET=1",
            f"CASE_SENSITIVE={case_sensitive}",
            "AUTO_OVERWRITE=0", f"ELOG_PATH={path}",
        ], cwd=path, env=native_environment(BIN), capture_output=True, timeout=45,
            creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(result.stdout.decode("gb18030", errors="replace"))
    return ini


def wait_server(process: subprocess.Popen, port: int) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Isolated Dameng server exited; inspect testdb server log")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Isolated Dameng server startup timed out")


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    servers = []
    streams = []
    manager = None
    results = []
    try:
        for label, port, case_sensitive in (("source", 15237, 1), ("target", 15238, 1), ("warning", 15239, 0)):
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", port))
            ini = initialize(label, port, case_sensitive=case_sensitive)
            stream = (SCRATCH / f"{label}_server.log").open("wb")
            streams.append(stream)
            process = subprocess.Popen([str(BIN / "dmserver.exe"), str(ini)],
                cwd=BIN, env=native_environment(BIN), stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
            servers.append(process)
            wait_server(process, port)
            print(f"Isolated {label} database ready on port {port}", flush=True)

        service = DatabaseService(BIN)
        source_raw = {"host":"127.0.0.1", "port":15237, "username":"SYSDBA", "password":PASSWORD}
        target_raw = {"host":"127.0.0.1", "port":15238, "username":"SYSDBA", "password":PASSWORD}
        warning_raw = {"host":"127.0.0.1", "port":15239, "username":"SYSDBA", "password":PASSWORD}
        source = Connection.parse(source_raw)
        target = Connection.parse(target_raw)
        warning_target = Connection.parse(warning_raw)
        with service.driver.connect(source) as connection:
            assert connection.query("SELECT SF_GET_CASE_SENSITIVE_FLAG()") == [["1"]]
            for schema in ("GUI_SRC",):
                try:
                    connection.query(f'DROP SCHEMA "{schema}" CASCADE')
                except Exception:
                    pass
                connection.query(f'CREATE SCHEMA "{schema}" AUTHORIZATION "SYSDBA"')
            connection.query('CREATE TABLE "GUI_SRC"."ORDERS" (ID INT PRIMARY KEY, NAME VARCHAR(100), NOTE CLOB)')
            connection.query("INSERT INTO GUI_SRC.ORDERS VALUES (1, '中文数据', '包含中文与 English 的大字段')")
            connection.query("INSERT INTO GUI_SRC.ORDERS VALUES (2, 'second', NULL)")
            connection.query('CREATE TABLE "GUI_SRC"."订单 明细" (ID INT, VALUE VARCHAR(100))')
            connection.query("INSERT INTO \"GUI_SRC\".\"订单 明细\" VALUES (7, '中文路径与表名')")
            connection.query('CREATE TABLE "GUI_SRC"."MixedCase" (ID INT)')
            connection.query('INSERT INTO "GUI_SRC"."MixedCase" VALUES (99)')
            connection.query('CREATE TABLE "GUI_SRC"."UNSELECTED" (ID INT)')
            connection.query('COMMENT ON TABLE "GUI_SRC"."ORDERS" IS \'订单测试表\'')
            connection.query("COMMIT")
        with service.driver.connect(warning_target) as connection:
            assert connection.query("SELECT SF_GET_CASE_SENSITIVE_FLAG()") == [["0"]]
            try:
                connection.query('DROP SCHEMA "GUI_CASE" CASCADE')
            except Exception:
                pass
            connection.query('CREATE SCHEMA "GUI_CASE" AUTHORIZATION "SYSDBA"')
        results.append("different CASE_SENSITIVE settings verified on isolated databases")
        with service.driver.connect(target) as connection:
            for schema in ("GUI_DST", "GUI_OFFLINE", "GUI_APPEND"):
                try:
                    connection.query(f'DROP SCHEMA "{schema}" CASCADE')
                except Exception:
                    pass
                connection.query(f'CREATE SCHEMA "{schema}" AUTHORIZATION "SYSDBA"')
            connection.query('CREATE TABLE "GUI_APPEND"."ORDERS" (ID INT, NAME VARCHAR(100), NOTE CLOB)')
            connection.query("INSERT INTO GUI_APPEND.ORDERS VALUES (3, 'existing', NULL)")
            connection.query("COMMIT")

        metadata = service.test(source_raw)
        assert metadata["connected"] and "GUI_SRC" in metadata["schemas"], metadata
        tables = service.tables(source_raw, "GUI_SRC")["tables"]
        assert any(table["name"] == "订单 明细" for table in tables), tables
        assert next(table for table in tables if table["name"] == "ORDERS")["comment"] == "订单测试表"
        print("PASS: direct ODBC driver, schema list, Unicode table metadata", flush=True)
        results.append("direct ODBC + metadata")

        manager = JobManager(REPORT / "data", BIN, service)
        output = ROOT / "output" / "验证 中文路径"
        raw = {"mode":"migrate", "source":source_raw, "target":target_raw,
            "source_schema":"GUI_SRC", "target_schema":"GUI_DST",
            "tables":["ORDERS", "订单 明细", "MixedCase"], "output_dir":str(output),
            "options":{"parallel":2, "table_parallel":1, "table_exists":"SKIP"}}

        def run(name: str, request: dict, *, expected: tuple[str, ...] = ("success", "warning")):
            record = manager.start(MigrationRequest.parse(request, output))
            print(f"Running: {name}", flush=True)
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                record = manager.get(record["id"])
                if record["status"] not in ACTIVE_STATUSES:
                    break
                time.sleep(0.05)
            else:
                manager.cancel(record["id"])
                raise RuntimeError(f"{name}: timed out")
            if record["status"] not in expected:
                raise AssertionError(f"{name}: {record['status']}\n" + manager.log_text(record["id"]))
            print(f"PASS: {name} ({record['status']})", flush=True)
            results.append(name)
            return record

        first = run("specified tables across two databases + schema remap + Unicode path", raw)
        with service.driver.connect(target) as connection:
            assert connection.query('SELECT ID, NAME, NOTE FROM GUI_DST.ORDERS ORDER BY ID') == [["1", "中文数据", "包含中文与 English 的大字段"], ["2", "second", None]]
            assert connection.query('SELECT ID, VALUE FROM "GUI_DST"."订单 明细"') == [["7", "中文路径与表名"]]
            assert connection.query('SELECT ID FROM "GUI_DST"."MixedCase"') == [["99"]]
            assert connection.query("SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='GUI_DST' AND TABLE_NAME='UNSELECTED'") == [["0"]]
            connection.query("UPDATE GUI_DST.ORDERS SET NAME='preserve' WHERE ID=1")
            connection.query("COMMIT")

        run("SKIP preserves existing target rows", raw)
        with service.driver.connect(target) as connection:
            assert connection.query("SELECT NAME FROM GUI_DST.ORDERS WHERE ID=1") == [["preserve"]]

        run("APPEND adds rows without removing existing data", {**raw, "target_schema":"GUI_APPEND", "tables":["ORDERS"], "options":{"table_exists":"APPEND", "indexes":False, "constraints":False}})
        with service.driver.connect(target) as connection:
            assert connection.query("SELECT COUNT(*) FROM GUI_APPEND.ORDERS") == [["3"]]
            assert connection.query("SELECT NAME FROM GUI_APPEND.ORDERS WHERE ID=3") == [["existing"]]

        truncate = {**raw, "tables":["ORDERS"], "options":{"table_exists":"TRUNCATE"}}
        try:
            MigrationRequest.parse(truncate, output)
            raise AssertionError("Destructive confirmation was not enforced")
        except ValidationError:
            results.append("destructive confirmation enforced")
        run("TRUNCATE imports after clearing rows", {**truncate,"destructive_confirmation":"GUI_DST"})
        with service.driver.connect(target) as connection:
            assert connection.query("SELECT COUNT(*) FROM GUI_DST.ORDERS") == [["2"]]
            assert connection.query("SELECT NAME FROM GUI_DST.ORDERS WHERE ID=1") == [["中文数据"]]
        run("REPLACE recreates selected table", {**truncate,"options":{"table_exists":"REPLACE"},"destructive_confirmation":"GUI_DST"})

        export = run("standalone export", {**raw,"mode":"export","tables":["ORDERS"]})
        run("standalone dump import", {**raw,"mode":"import","source":None,
            "target_schema":"GUI_OFFLINE","dump_file":export["dump_file"],"tables":[]})
        with service.driver.connect(target) as connection:
            assert connection.query("SELECT COUNT(*) FROM GUI_OFFLINE.ORDERS") == [["2"]]

        warning_request = {**raw, "target":warning_raw, "target_schema":"GUI_CASE", "tables":["ORDERS"]}
        warning = run("CASE_SENSITIVE warning exit code 2 reports completed with warning", warning_request, expected=("warning",))
        assert warning["phases"]["import"] == "completed" and warning["error"] is None
        assert warning["warning_count"] == 1
        assert "CASE_SENSITIVE" in manager.log_text(warning["id"])
        assert "警告退出码 2" in manager.log_text(warning["id"])
        with service.driver.connect(warning_target) as connection:
            assert connection.query("SELECT ID, NAME, NOTE FROM GUI_CASE.ORDERS ORDER BY ID") == [["1", "中文数据", "包含中文与 English 的大字段"], ["2", "second", None]]

        rejected = run("real duplicate-key data errors remain failed despite CASE_SENSITIVE warning", {
            **warning_request, "options":{"table_exists":"APPEND", "indexes":False, "constraints":False},
        }, expected=("failed",))
        assert rejected["phases"]["import"] == "failed"
        assert any(event["level"] == "error" for event in rejected["events"])
        with service.driver.connect(warning_target) as connection:
            assert connection.query("SELECT COUNT(*) FROM GUI_CASE.ORDERS") == [["2"]]

        special_password = 'Gui_Probe_2468@/; "空 格"'
        for config in (source, target):
            with service.driver.connect(config) as connection:
                try:
                    connection.query('DROP USER "GUI_PASSWORD_TEST" CASCADE')
                except Exception:
                    pass
                connection.query('CREATE USER "GUI_PASSWORD_TEST" IDENTIFIED BY ' + sql_identifier(special_password))
                connection.query('GRANT DBA TO "GUI_PASSWORD_TEST"')
                connection.query("COMMIT")
        special_source = {**source_raw,"username":"GUI_PASSWORD_TEST","password":special_password}
        special_target = {**target_raw,"username":"GUI_PASSWORD_TEST","password":special_password}
        assert service.test(special_source)["connected"]
        run("password punctuation, spaces, quotes and Unicode via stdin", {**raw,"source":special_source,"target":special_target,"tables":["ORDERS"]})

        invalid = run("missing source table fails before export/import", {**raw,"tables":["NO_SUCH_TABLE"]}, expected=("failed",))
        assert invalid["phases"]["export"] == "pending" and invalid["phases"]["import"] == "pending"

        for file in (REPORT / "data").rglob("*"):
            if file.is_file():
                assert PASSWORD.encode() not in file.read_bytes(), f"Credential leak in {file}"
                assert special_password.encode("utf-8") not in file.read_bytes(), f"Credential leak in {file}"
        for file in output.rglob("*.log"):
            assert PASSWORD.encode() not in file.read_bytes(), f"Credential leak in {file}"
            assert special_password.encode("gb18030") not in file.read_bytes(), f"Credential leak in {file}"
        results.append("no passwords in persisted records/logs")
        (REPORT / "report.json").write_text(json.dumps({"passed":results},ensure_ascii=False,indent=2),encoding="utf-8")
        print(f"ALL {len(results)} integration checks passed", flush=True)
        if "--hold" in sys.argv:
            print("READY: isolated databases remain available for packaged application checks; send Enter to stop.", flush=True)
            sys.stdin.readline()
    finally:
        if manager:
            manager.shutdown()
        for process in servers:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
        for stream in streams:
            stream.close()


if __name__ == "__main__":
    main()
