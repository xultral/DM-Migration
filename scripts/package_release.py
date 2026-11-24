"""Create Windows release assets without local connections, dumps, or test databases."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dm_migration import __version__


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Dameng migration release assets")
    parser.add_argument("--standalone", action="store_true", help="Include the separately built standalone EXE")
    arguments = parser.parse_args()
    name = f"DM-Migration-{__version__}"
    executable = ROOT / f"{name}.exe"
    if not executable.is_file():
        raise SystemExit("Build the application with build.ps1 first.")
    for tool in ("dexp.exe", "dimp.exe", "dodbc.dll"):
        if not (ROOT / "bin" / tool).is_file():
            raise SystemExit(f"The portable package requires bin/{tool} and its official dependencies.")
    standalone = ROOT / f"{name}-standalone.exe"
    if arguments.standalone and not standalone.is_file():
        raise SystemExit("Build the standalone EXE with build.ps1 -BundleBin first.")
    release_dir = ROOT / "dist" / "releases" / __version__
    release_dir.mkdir(parents=True, exist_ok=True)
    assets = []
    destination = release_dir / executable.name
    shutil.copy2(executable, destination)
    assets.append(destination)

    folder = f"{name}-windows-x64"
    portable = release_dir / f"{folder}-portable.zip"
    files = [executable, ROOT / "start.bat", ROOT / "README.md"]
    files.extend(file for file in (ROOT / "bin").rglob("*") if file.is_file())
    files.extend(file for file in (ROOT / "docs" / "images").rglob("*") if file.is_file())
    with zipfile.ZipFile(portable, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in sorted(files):
            archive.write(file, f"{folder}/{file.relative_to(ROOT).as_posix()}")
    assets.append(portable)
    if arguments.standalone:
        destination = release_dir / standalone.name
        shutil.copy2(standalone, destination)
        assets.append(destination)
    checksum_lines = []
    for asset in assets:
        with asset.open("rb") as stream:
            checksum = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                checksum.update(chunk)
            digest = checksum.hexdigest()
        checksum_lines.append(f"{digest}  {asset.name}")
        print(f"Packaged {asset.name}: {asset.stat().st_size / 1024**2:.1f} MiB", flush=True)
    (release_dir / "SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"Release assets: {release_dir}", flush=True)


if __name__ == "__main__":
    main()
