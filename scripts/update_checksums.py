#!/usr/bin/env python3
"""Rewrite SHA256SUMS for every released file, or check it with --check."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SHA256SUMS"
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", "reproduction_outputs", ".venv", "venv"}
IGNORED_NAMES = {"SHA256SUMS", ".gitignore", ".DS_Store"}


def released_files() -> list[Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if IGNORED_PARTS.intersection(relative.parts) or relative.name in IGNORED_NAMES:
            continue
        if any(part.endswith(".egg-info") for part in relative.parts) or relative.suffix == ".pyc":
            continue
        files.append(relative)
    return files


def manifest_text() -> str:
    lines = []
    for relative in released_files():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        lines.append(f"{digest}  {relative.as_posix()}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if SHA256SUMS is stale")
    args = parser.parse_args()
    text = manifest_text()
    if args.check:
        if not MANIFEST.is_file() or MANIFEST.read_text(encoding="utf-8") != text:
            print("SHA256SUMS is stale; run python scripts/update_checksums.py")
            return 1
        print(f"SHA256SUMS up to date: {text.count(chr(10))} files")
        return 0
    MANIFEST.write_text(text, encoding="utf-8")
    print(f"WROTE: SHA256SUMS ({text.count(chr(10))} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
