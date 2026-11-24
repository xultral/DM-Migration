from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from pathlib import Path
import re
from typing import Any


class ValidationError(ValueError):
    """An actionable error that can be displayed in the interface."""


def text(value: Any, label: str, *, required: bool = True, limit: int = 256) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label}必须是文本")
    if required and not value.strip():
        raise ValidationError(f"请填写{label}")
    if len(value) > limit or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValidationError(f"{label}过长或包含换行、控制字符")
    return value


def identifier(value: Any, label: str) -> str:
    return text(value, label, limit=128)


def sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def native_text(value: str) -> str:
    try:
        value.encode("gb18030")
    except UnicodeEncodeError as exc:
        raise ValidationError("当前 Windows 版达梦工具无法编码该文本，请使用常用中文或英文名称") from exc
    return value


@dataclass(frozen=True)
class Connection:
    host: str
    port: int
    username: str
    password: str

    @classmethod
    def parse(cls, raw: Any, label: str = "数据库") -> Connection:
        if not isinstance(raw, dict):
            raise ValidationError(f"请配置{label}连接")
        host = text(raw.get("host", ""), f"{label}地址").strip()
        unbracketed = host[1:-1] if host.startswith("[") and host.endswith("]") else host
        try:
            ipaddress.ip_address(unbracketed.split("%", 1)[0])
        except ValueError:
            if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.\-]{0,251}[A-Za-z0-9])?", host):
                raise ValidationError(f"{label}地址应为 IP 或主机名，不包含协议和端口")
        port_value = raw.get("port", 5236)
        if isinstance(port_value, bool) or not isinstance(port_value, (str, int)):
            raise ValidationError(f"{label}端口必须是整数")
        try:
            port = int(port_value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{label}端口必须是整数") from exc
        if isinstance(raw.get("port"), bool) or not 1 <= port <= 65535:
            raise ValidationError(f"{label}端口应在 1–65535 之间")
        username = identifier(raw.get("username", ""), f"{label}用户名")
        password = text(raw.get("password", ""), f"{label}密码", limit=1024)
        native_text(username)
        native_text(password)
        return cls(host, port, username, password)

    @property
    def userid(self) -> str:
        """The official tools prompt on stdin; the password stays out of argv."""
        host = self.host
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        return f"{sql_identifier(self.username)}@{host}:{self.port}"

    def public(self) -> dict[str, Any]:
        return {"host": self.host, "port": self.port, "username": self.username}

    def same_server(self, other: Connection) -> bool:
        def canonical(host: str) -> str:
            host = host.strip("[]").casefold().rstrip(".")
            return "loopback" if host in {"localhost", "127.0.0.1", "::1"} else host
        return canonical(self.host) == canonical(other.host) and self.port == other.port


@dataclass(frozen=True)
class Options:
    rows: bool = True
    indexes: bool = True
    constraints: bool = True
    triggers: bool = True
    grants: bool = False
    compress: bool = True
    parallel: int = 4
    table_parallel: int = 2
    table_exists: str = "SKIP"

    @classmethod
    def parse(cls, raw: Any) -> Options:
        if raw is None:
            return cls()
        if not isinstance(raw, dict):
            raise ValidationError("迁移选项格式不正确")
        defaults = cls()
        values: dict[str, Any] = {}
        for key in ("rows", "indexes", "constraints", "triggers", "grants", "compress"):
            value = raw.get(key, getattr(defaults, key))
            if not isinstance(value, bool):
                raise ValidationError(f"选项 {key} 必须是布尔值")
            values[key] = value
        for key, maximum in (("parallel", 100), ("table_parallel", 50)):
            value = raw.get(key, getattr(defaults, key))
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
                raise ValidationError(f"{key} 应为 1–{maximum} 的整数")
            values[key] = value
        action = raw.get("table_exists", defaults.table_exists)
        if action not in {"SKIP", "APPEND", "TRUNCATE", "REPLACE"}:
            raise ValidationError("目标表处理策略无效")
        values["table_exists"] = action
        return cls(**values)

    def public(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass(frozen=True)
class MigrationRequest:
    mode: str
    source: Connection | None
    target: Connection | None
    source_schema: str
    target_schema: str
    tables: tuple[str, ...]
    output_dir: Path
    dump_file: Path | None
    options: Options

    @classmethod
    def parse(cls, raw: Any, default_output: Path) -> MigrationRequest:
        if not isinstance(raw, dict):
            raise ValidationError("任务格式不正确")
        mode = raw.get("mode", "migrate")
        if mode not in {"migrate", "export", "import"}:
            raise ValidationError("任务类型无效")
        source = Connection.parse(raw.get("source"), "源库") if mode != "import" else None
        target = Connection.parse(raw.get("target"), "目标库") if mode != "export" else None
        source_schema = identifier(raw.get("source_schema", ""), "源 Schema")
        target_schema = identifier(raw.get("target_schema", ""), "目标 Schema") if target else ""
        raw_tables = raw.get("tables", [])
        if not isinstance(raw_tables, list) or len(raw_tables) > 20000:
            raise ValidationError("请选择最多 20000 张表")
        tables = tuple(dict.fromkeys(identifier(item, "表名") for item in raw_tables))
        if mode != "import" and not tables:
            raise ValidationError("请至少选择一张需要迁移的表")
        output_value = text(raw.get("output_dir", str(default_output)), "工作目录", limit=2048).strip()
        output_dir = Path(output_value).expanduser().resolve()
        if output_dir.exists() and not output_dir.is_dir():
            raise ValidationError("工作目录指向了文件，请选择文件夹")
        dump_file = None
        if mode == "import":
            dump_value = text(raw.get("dump_file", ""), "导入文件路径", limit=2048).strip()
            dump_file = Path(dump_value).expanduser().resolve()
            if not dump_file.is_file():
                raise ValidationError("导入文件不存在，请选择 dexp 生成的 .dmp 文件")
        options = Options.parse(raw.get("options"))
        if source and target and source.same_server(target) and source_schema == target_schema:
            raise ValidationError("源库和目标库的地址、端口、Schema 相同，请选择不同的目标 Schema 或数据库")
        if mode != "export" and options.table_exists in {"TRUNCATE", "REPLACE"}:
            if raw.get("destructive_confirmation") != target_schema:
                raise ValidationError("清空或替换目标表前，请输入目标 Schema 确认")
        for value in (source_schema, target_schema, str(output_dir), *(tables or ())):
            native_text(value)
        if dump_file:
            native_text(str(dump_file))
        return cls(mode, source, target, source_schema, target_schema, tables, output_dir, dump_file, options)

    def public(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "source": self.source.public() if self.source else None,
            "target": self.target.public() if self.target else None,
            "source_schema": self.source_schema,
            "target_schema": self.target_schema,
            "tables": list(self.tables),
            "output_dir": str(self.output_dir),
            "dump_file": str(self.dump_file) if self.dump_file else None,
            "options": self.options.public(),
        }
