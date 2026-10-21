#!/usr/bin/env python3
"""Extract the "Twentieth" (20th anniversary) theme from an installed Armoury Crate.

The theme is not a downloadable pack. It ships inside the Armoury Crate UWP
package as a set of XAML style dictionaries plus seven `Assets/Twentieth`
resource folders. This script copies those folders out, keeps the original
relative paths, and writes a manifest with SHA256 for every file.

Usage:
    python extract_twentieth.py --out ./extracted
    python extract_twentieth.py --list
    python extract_twentieth.py --verify ./extracted/manifest.json

Requires Windows and a local Armoury Crate installation. Read-only: nothing
under C:\\Program Files\\WindowsApps is modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

THEME_NAME = "Twentieth"
PACKAGE_PATTERN = "B9ECED6F.ArmouryCrate_*_x64__*"
DEFAULT_WINDOWS_APPS = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "WindowsApps"


# Windows caps paths at 260 characters unless the long-path prefix is used.
# Package asset paths get deep enough to hit that limit.
def long_path(path: Path | str) -> str:
    if os.name != "nt":
        return str(path)
    p = os.path.abspath(str(path))
    if p.startswith("\\\\?\\"):
        return p
    if p.startswith("\\\\"):
        return "\\\\?\\UNC\\" + p[2:]
    return "\\\\?\\" + p


def sha256(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(long_path(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_package(explicit: str | None) -> Path:
    if explicit:
        pkg = Path(explicit)
        if not pkg.is_dir():
            sys.exit(f"package path not found: {pkg}")
        return pkg

    try:
        candidates = sorted(DEFAULT_WINDOWS_APPS.glob(PACKAGE_PATTERN))
    except PermissionError:
        sys.exit(
            f"cannot list {DEFAULT_WINDOWS_APPS}. Run the script as a user that can "
            "read WindowsApps, or pass --package with the install path."
        )
    if not candidates:
        sys.exit(
            "Armoury Crate package not found. Check with:\n"
            "  powershell -c \"Get-AppxPackage *ArmouryCrate* | Select InstallLocation\""
        )
    return candidates[-1]


def find_theme_dirs(package: Path) -> list[Path]:
    hits = []
    for dirpath, dirnames, _ in os.walk(long_path(package)):
        for name in list(dirnames):
            if name.lower() == THEME_NAME.lower():
                hits.append(Path(dirpath[4:] if dirpath.startswith("\\\\?\\") else dirpath) / name)
                dirnames.remove(name)
    return sorted(hits)


def list_theme_files(package: Path) -> list[tuple[Path, Path]]:
    """Return (absolute source, path relative to package) for every theme file."""
    pairs = []
    for theme_dir in find_theme_dirs(package):
        for dirpath, _, filenames in os.walk(long_path(theme_dir)):
            clean = dirpath[4:] if dirpath.startswith("\\\\?\\") else dirpath
            for fn in filenames:
                src = Path(clean) / fn
                pairs.append((src, src.relative_to(package)))
    return pairs


def extract(package: Path, out: Path) -> Path:
    pairs = list_theme_files(package)
    if not pairs:
        sys.exit(
            f"no '{THEME_NAME}' resource folders inside {package}. "
            "The theme may have been removed in this Armoury Crate version."
        )

    records = []
    for src, rel in pairs:
        dst = out / "assets" / rel
        os.makedirs(long_path(dst.parent), exist_ok=True)
        shutil.copy2(long_path(src), long_path(dst))
        st = os.stat(long_path(dst))
        records.append(
            {
                "package_path": str(rel).replace("\\", "/"),
                "path": str(Path("assets") / rel).replace("\\", "/"),
                "size": st.st_size,
                "sha256": sha256(dst),
            }
        )

    pri = package / "resources.pri"
    if pri.is_file():
        dst = out / "resources.pri"
        shutil.copy2(long_path(pri), long_path(dst))
        records.append(
            {
                "package_path": "resources.pri",
                "path": "resources.pri",
                "size": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )

    manifest = {
        "theme": THEME_NAME,
        "package": package.name,
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "file_count": len(records),
        "total_bytes": sum(r["size"] for r in records),
        "files": records,
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def verify(manifest_path: Path) -> int:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    base = Path(manifest_path).parent
    bad = []
    for entry in manifest["files"]:
        target = base / entry["path"]
        if not target.is_file():
            bad.append(("missing", entry["path"]))
        elif sha256(target) != entry["sha256"]:
            bad.append(("mismatch", entry["path"]))
    print(f"{len(manifest['files'])} files, {len(bad)} problem(s)")
    for kind, path in bad[:20]:
        print(f"  {kind}: {path}")
    return 1 if bad else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package", help="Armoury Crate install path (auto-detected when omitted)")
    parser.add_argument("--out", default="extracted", help="output directory (default: ./extracted)")
    parser.add_argument("--list", action="store_true", help="list theme files without copying")
    parser.add_argument("--verify", metavar="MANIFEST", help="verify an existing extraction")
    args = parser.parse_args()

    if args.verify:
        return verify(Path(args.verify))

    package = find_package(args.package)
    print(f"package: {package}")

    if args.list:
        pairs = list_theme_files(package)
        for src, rel in pairs:
            print(f"  {rel}")
        print(f"{len(pairs)} files")
        return 0

    manifest = extract(package, Path(args.out))
    data = json.loads(manifest.read_text(encoding="utf-8"))
    print(f"wrote {data['file_count']} files, {data['total_bytes'] / 1048576:.2f} MB")
    print(f"manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
