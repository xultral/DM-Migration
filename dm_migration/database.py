from __future__ import annotations

import ctypes
import os
from pathlib import Path
import threading
import uuid
from typing import Any

from .models import Connection, ValidationError, identifier, sql_literal


class DatabaseError(RuntimeError):
    pass


class DamengDriver:
    """Call the shipped ODBC driver's exports directly, without driver registration."""

    def __init__(self, bin_dir: Path):
        self.bin_dir = bin_dir
        if os.name != "nt":
            raise DatabaseError("当前附带的达梦工具为 Windows 版本，请在 Windows 上运行")
        path = bin_dir / "dodbc.dll"
        if not path.is_file():
            raise DatabaseError("bin 中缺少 dodbc.dll，请复制官方安装包内的 ODBC 驱动及依赖")
        self.dll_directories: list[Any] = []
        for directory in (bin_dir, bin_dir / "dependencies", bin_dir / "dependencies" / "thirdparty"):
            if directory.is_dir():
                self.dll_directories.append(os.add_dll_directory(str(directory)))
        try:
            self.lib = ctypes.WinDLL(str(path))
        except OSError as exc:
            raise DatabaseError(f"达梦驱动加载失败，请保留 bin 中的配套 DLL；{exc}") from exc
        handle = ctypes.c_void_p
        short = ctypes.c_short
        integer = ctypes.c_int
        signatures = {
            "SQLAllocHandle": ([short, handle, ctypes.POINTER(handle)], short),
            "SQLFreeHandle": ([short, handle], short),
            "SQLSetEnvAttr": ([handle, integer, handle, integer], short),
            "SQLSetConnectAttr": ([handle, integer, handle, integer], short),
            "SQLDriverConnectW": ([handle, handle, ctypes.c_wchar_p, short, ctypes.c_wchar_p, short, ctypes.POINTER(short), ctypes.c_ushort], short),
            "SQLConnectW": ([handle, ctypes.c_wchar_p, short, ctypes.c_wchar_p, short, ctypes.c_wchar_p, short], short),
            "SQLDisconnect": ([handle], short),
            "SQLGetDiagRecW": ([short, handle, short, ctypes.c_wchar_p, ctypes.POINTER(integer), ctypes.c_wchar_p, short, ctypes.POINTER(short)], short),
            "SQLExecDirectW": ([handle, ctypes.c_wchar_p, integer], short),
            "SQLNumResultCols": ([handle, ctypes.POINTER(short)], short),
            "SQLFetch": ([handle], short),
            "SQLGetData": ([handle, ctypes.c_ushort, short, handle, ctypes.c_ssize_t, ctypes.POINTER(ctypes.c_ssize_t)], short),
            "SQLSetStmtAttr": ([handle, integer, handle, integer], short),
        }
        try:
            for name, (arguments, result) in signatures.items():
                function = getattr(self.lib, name)
                function.argtypes = arguments
                function.restype = result
        except AttributeError as exc:
            raise DatabaseError("达梦驱动缺少标准 ODBC 接口，请使用与工具匹配的 64 位驱动") from exc

    def diagnostic(self, kind: int, handle: ctypes.c_void_p) -> str:
        messages = []
        for record in range(1, 9):
            state = ctypes.create_unicode_buffer(6)
            message = ctypes.create_unicode_buffer(4096)
            native = ctypes.c_int()
            length = ctypes.c_short()
            result = self.lib.SQLGetDiagRecW(kind, handle, record, state, ctypes.byref(native), message, len(message), ctypes.byref(length))
            if result not in (0, 1):
                break
            messages.append(f"[{state.value}/{native.value}] {message.value}")
        return "；".join(messages) or "达梦驱动未返回详细错误"

    def check(self, result: int, kind: int, handle: ctypes.c_void_p) -> None:
        if result not in (0, 1):
            raise DatabaseError(self.diagnostic(kind, handle))

    def connect(self, config: Connection) -> ODBCConnection:
        return ODBCConnection(self, config)


class ODBCConnection:
    def __init__(self, driver: DamengDriver, config: Connection):
        self.driver = driver
        self.environment = ctypes.c_void_p()
        self.connection = ctypes.c_void_p()
        self.connected = False
        try:
            driver.check(driver.lib.SQLAllocHandle(1, None, ctypes.byref(self.environment)), 1, self.environment)
            driver.check(driver.lib.SQLSetEnvAttr(self.environment, 200, ctypes.c_void_p(3), 0), 1, self.environment)
            driver.check(driver.lib.SQLAllocHandle(2, self.environment, ctypes.byref(self.connection)), 1, self.environment)
            driver.check(driver.lib.SQLSetConnectAttr(self.connection, 103, ctypes.c_void_p(8), 0), 2, self.connection)

            # This version of dodbc preserves braces in connection-string
            # values instead of implementing standard ODBC escaping. SQLConnectW
            # takes credentials as separate strings and handles punctuation.
            # A temporary, user-level DSN contains only server/port/driver path;
            # it requires no driver registration and is deleted after login.
            import winreg

            name = f"DM_MIGRATION_TMP_{os.getpid()}_{uuid.uuid4().hex}"
            registry_path = "\\".join(("SOFTWARE", "ODBC", "ODBC.INI", name))
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
                    for attribute, value in (("Driver", str(driver.bin_dir / "dodbc.dll")), ("SERVER", config.host.strip("[]")), ("TCP_PORT", str(config.port))):
                        winreg.SetValueEx(key, attribute, 0, winreg.REG_SZ, value)
                result = driver.lib.SQLConnectW(self.connection, name, -3, config.username, -3, config.password, -3)
                driver.check(result, 2, self.connection)
            finally:
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, registry_path)
                except FileNotFoundError:
                    pass
            self.connected = True
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self.connection.value:
            if self.connected:
                self.driver.lib.SQLDisconnect(self.connection)
            self.driver.lib.SQLFreeHandle(2, self.connection)
            self.connection = ctypes.c_void_p()
        if self.environment.value:
            self.driver.lib.SQLFreeHandle(1, self.environment)
            self.environment = ctypes.c_void_p()

    def __enter__(self) -> ODBCConnection:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def query(self, sql: str, *, maximum: int = 50000) -> list[list[str | None]]:
        statement = ctypes.c_void_p()
        lib = self.driver.lib
        self.driver.check(lib.SQLAllocHandle(3, self.connection, ctypes.byref(statement)), 2, self.connection)
        try:
            lib.SQLSetStmtAttr(statement, 0, ctypes.c_void_p(30), 0)
            self.driver.check(lib.SQLExecDirectW(statement, sql, -3), 3, statement)
            count = ctypes.c_short()
            self.driver.check(lib.SQLNumResultCols(statement, ctypes.byref(count)), 3, statement)
            if count.value == 0:
                return []
            rows: list[list[str | None]] = []
            while True:
                result = lib.SQLFetch(statement)
                if result == 100:
                    return rows
                self.driver.check(result, 3, statement)
                if len(rows) >= maximum:
                    raise DatabaseError(f"查询返回超过 {maximum} 条记录，请缩小范围")
                row: list[str | None] = []
                for column in range(1, count.value + 1):
                    parts: list[str] = []
                    while True:
                        buffer = ctypes.create_unicode_buffer(4096)
                        indicator = ctypes.c_ssize_t()
                        result = lib.SQLGetData(statement, column, -8, buffer, ctypes.sizeof(buffer), ctypes.byref(indicator))
                        if result == 100:
                            break
                        self.driver.check(result, 3, statement)
                        if indicator.value == -1:
                            parts = []
                            break
                        parts.append(buffer.value)
                        if result == 0:
                            break
                    row.append(None if indicator.value == -1 else "".join(parts))
                rows.append(row)
        finally:
            lib.SQLFreeHandle(3, statement)


class DatabaseService:
    def __init__(self, bin_dir: Path):
        self.bin_dir = bin_dir
        self._driver: DamengDriver | None = None
        self._lock = threading.Lock()

    @property
    def driver(self) -> DamengDriver:
        with self._lock:
            if self._driver is None:
                self._driver = DamengDriver(self.bin_dir)
            return self._driver

    def schemas(self, connection: ODBCConnection, username: str) -> list[str]:
        for query in (
            "SELECT NAME FROM SYS.SYSOBJECTS WHERE TYPE$='SCH' ORDER BY NAME",
            "SELECT NAME FROM SYS.SYSSCHEMAS ORDER BY NAME",
            "SELECT DISTINCT OWNER FROM ALL_TABLES ORDER BY OWNER",
        ):
            try:
                result = connection.query(query)
                names = {row[0] for row in result if row[0]}
                names.add(username)
                return sorted(names)
            except DatabaseError:
                continue
        return [username]

    def test(self, raw: Any) -> dict[str, Any]:
        config = Connection.parse(raw)
        with self.driver.connect(config) as connection:
            rows = connection.query("SELECT USER FROM DUAL", maximum=1)
            user = rows[0][0] if rows else config.username
            schemas = self.schemas(connection, user or config.username)
            version = "Dameng Database"
            try:
                rows = connection.query("SELECT BANNER FROM V$VERSION", maximum=20)
                if rows and rows[0][0]:
                    version = rows[0][0]
            except DatabaseError:
                pass
            return {"connected": True, "username": user, "schemas": schemas, "version": version}

    def tables(self, raw: Any, schema: Any) -> dict[str, Any]:
        config = Connection.parse(raw)
        schema = identifier(schema, "源 Schema")
        where = sql_literal(schema)
        with self.driver.connect(config) as connection:
            queries = (
                f"SELECT T.TABLE_NAME, T.NUM_ROWS, C.COMMENTS FROM ALL_TABLES T LEFT JOIN ALL_TAB_COMMENTS C ON C.OWNER=T.OWNER AND C.TABLE_NAME=T.TABLE_NAME WHERE T.OWNER={where} ORDER BY T.TABLE_NAME",
                f"SELECT TABLE_NAME, NUM_ROWS FROM ALL_TABLES WHERE OWNER={where} ORDER BY TABLE_NAME",
                f"SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER={where} ORDER BY TABLE_NAME",
            )
            last_error: Exception | None = None
            for query in queries:
                try:
                    rows = connection.query(query)
                    tables = []
                    for row in rows:
                        try:
                            estimated_rows = int(row[1]) if len(row) > 1 and row[1] is not None else None
                        except ValueError:
                            estimated_rows = None
                        tables.append({"name": row[0], "schema": schema, "estimated_rows": estimated_rows, "comment": row[2] if len(row) > 2 else ""})
                    return {"schema": schema, "tables": tables}
                except DatabaseError as exc:
                    last_error = exc
            raise DatabaseError(f"读取表清单失败，可使用手动输入表名；{last_error}")
