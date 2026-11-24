from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess

from .models import Connection, MigrationRequest, sql_identifier


@dataclass(frozen=True)
class NativeCommand:
    phase: str
    executable: Path
    connection: Connection
    parameters: tuple[str, ...]

    @property
    def file_parameters(self) -> tuple[str, ...]:
        return tuple(line for line in self.parameters if line.split("=", 1)[0] not in {"FILE", "DIRECTORY", "LOG"})

    def argv(self, parameter_file: Path) -> list[str]:
        # PARFILE tokenizes raw path values containing whitespace and preserves
        # quotes around paths. Supply paths as individual argv entries instead.
        # Keep object lists in the file to avoid Windows' command length limit.
        paths = [line for line in self.parameters if line.split("=", 1)[0] in {"FILE", "DIRECTORY", "LOG"}]
        return [str(self.executable), self.connection.userid, f"PARFILE={parameter_file.name}", *paths]

    def preview(self) -> dict[str, str]:
        return {
            "phase": self.phase,
            "command": subprocess.list2cmdline([self.executable.name, self.connection.userid, "PARFILE=<参数文件>", *[line for line in self.parameters if line.split("=", 1)[0] in {"FILE", "DIRECTORY", "LOG"}]]),
            "parameters": "\n".join(self.file_parameters),
        }


def table_parameter(request: MigrationRequest) -> str:
    names = ",".join(f"{sql_identifier(request.source_schema)}.{sql_identifier(name)}" for name in request.tables)
    return f"TABLES=({names})"


def build_commands(request: MigrationRequest, bin_dir: Path, artifact_dir: Path) -> list[NativeCommand]:
    options = request.options
    common = [
        f"PARALLEL={options.parallel}",
        f"ROWS={'Y' if options.rows else 'N'}",
        f"INDEXES={'Y' if options.indexes else 'N'}",
        f"CONSTRAINTS={'Y' if options.constraints else 'N'}",
        f"TRIGGERS={'Y' if options.triggers else 'N'}",
        f"GRANTS={'Y' if options.grants else 'N'}",
        "EXCLUDE=(STATISTICS)",
        "LOG_WRITE=Y",
        "DUMMY=Y",
        "FEEDBACK=10000",
    ]
    commands: list[NativeCommand] = []
    if request.source:
        parameters = [
            "FILE=migration.dmp",
            # PARFILE preserves literal quotes around paths: write raw values.
            f"DIRECTORY={artifact_dir}",
            table_parameter(request),
            f"LOG={artifact_dir / 'export.log'}",
            f"TABLE_PARALLEL={options.table_parallel}",
            f"COMPRESS={'Y' if options.compress else 'N'}",
            "TABLESPACE=N",
            "DROP=N",
            "CTRL_INFO=2",
            *common,
        ]
        commands.append(NativeCommand("export", bin_dir / "dexp.exe", request.source, tuple(parameters)))
    if request.target:
        dump = request.dump_file or artifact_dir / "migration.dmp"
        parameters = [
            f"FILE={dump.name}",
            f"DIRECTORY={dump.parent}",
            table_parameter(request) if request.tables else "FULL=Y",
            f"LOG={artifact_dir / 'import.log'}",
            f"TABLE_EXISTS_ACTION={options.table_exists}",
            "IGNORE=N",
            "FAST_LOAD=N",
            *common,
        ]
        if request.source_schema != request.target_schema:
            parameters.append(f"REMAP_SCHEMA=({sql_identifier(request.source_schema)}:{sql_identifier(request.target_schema)})")
        commands.append(NativeCommand("import", bin_dir / "dimp.exe", request.target, tuple(parameters)))
    return commands


def native_environment(bin_dir: Path) -> dict[str, str]:
    environment = os.environ.copy()
    directories = [bin_dir, bin_dir / "dependencies", bin_dir / "dependencies" / "thirdparty", bin_dir / "thirdparty"]
    environment["PATH"] = os.pathsep.join(str(item) for item in directories if item.is_dir()) + os.pathsep + environment.get("PATH", "")
    return environment


def tool_status(bin_dir: Path) -> dict[str, object]:
    tools = []
    for name in ("dexp.exe", "dimp.exe", "dodbc.dll"):
        path = bin_dir / name
        item: dict[str, object] = {"name": name, "available": path.is_file(), "path": str(path)}
        if path.is_file() and name.endswith(".exe"):
            try:
                result = subprocess.run([str(path), "HELP"], cwd=bin_dir, env=native_environment(bin_dir), capture_output=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                output = (result.stdout + result.stderr).decode("gb18030", errors="replace")
                lines = [line.strip() for line in output.splitlines() if line.strip()]
                item["runnable"] = result.returncode == 0
                item["version"] = next((line for line in lines if line.lower().startswith("version:")), lines[0] if lines else "未知版本")
                if result.returncode != 0:
                    item["error"] = output[:500] or f"进程退出码 {result.returncode}"
            except (OSError, subprocess.TimeoutExpired) as exc:
                item["runnable"] = False
                item["error"] = str(exc)
        tools.append(item)
    return {"bin_dir": str(bin_dir), "tools": tools, "ready": all(item.get("runnable", item["available"]) for item in tools)}
