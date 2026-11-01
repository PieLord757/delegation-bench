#!/usr/bin/env python3
"""Build or verify the deterministic file-level license inventory."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "LICENSE_INVENTORY.csv"
SPECIAL = {Path("SHA256SUMS"), Path("LICENSE_INVENTORY.csv")}
TOP_LEVEL_CC_FILES = {
    Path("BENCHMARK_USE.md"),
    Path("CONTAMINATION_CANARY.md"),
    Path("DATASET_CARD.md"),
    Path("DATASHEET.md"),
    Path("croissant.json"),
    Path("README.md"),
    Path("REPRODUCING.md"),
    Path("SCHEMA.md"),
    Path("delegationcheck_v1_0.jsonl"),
}
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", "reproduction_outputs", "hf_upload", ".venv", "venv"}
IGNORED_NAMES = {".gitignore", ".DS_Store"}
CC_ROOTS = {"data", "explicit_rules", "figures", "hf_dataset", "results", "tool_loop"}
TAU_BENCH_ROOT = Path("explicit_rules/third_party/tau_bench")
CC_SUFFIXES = {".csv", ".json", ".md", ".png", ".sha256"}
PRIVATE_OUTPUT_PATTERN = re.compile(
    r"(^|[_/-])(raw|canonical|provider)[^/]*(response|responses|output|outputs)([_./-]|$)",
    re.IGNORECASE,
)


def license_for(relative: Path) -> tuple[str, str]:
    if PRIVATE_OUTPUT_PATTERN.search(relative.as_posix()):
        raise ValueError(f"private/provider-output filename is not releasable: {relative}")
    if relative.suffix == ".jsonl" and relative != Path("delegationcheck_v1_0.jsonl"):
        raise ValueError(f"unexpected JSONL is not releasable: {relative}")
    if relative == Path("LICENSE"):
        return "license_notice", "MIT license text"
    if relative.name in {"LICENSE-DATA.md", "LICENSES.md"}:
        return "license_notice", "CC BY notice or licensing boundary"
    if relative == Path("THIRD_PARTY_NOTICES/DEJAVU_FONTS_LICENSE.txt"):
        return "DejaVu-font-license", "verbatim license for the font subset embedded in PDFs"
    if relative == Path("THIRD_PARTY_NOTICES/TAU_BENCH_LICENSE.txt"):
        return "MIT-tau-bench", "verbatim MIT license of the vendored tau-bench files (Sierra)"
    if relative == Path("explicit_rules/cases/tau_bench_decision_points.json"):
        return (
            "CC-BY-4.0 + MIT-tau-bench",
            "author-assembled decision points embedding tau-bench task instructions and user/order records (MIT, Sierra)",
        )
    if relative.parts[: len(TAU_BENCH_ROOT.parts)] == TAU_BENCH_ROOT.parts:
        return "MIT-tau-bench", "unmodified third-party file from tau-bench revision 59a200c (Sierra)"
    if relative.suffix == ".py" or relative in {
        Path("pyproject.toml"),
        Path("requirements-tested.txt"),
    }:
        return "MIT", "author-created code or software metadata"
    if relative.suffix == ".pdf":
        if not relative.parts or relative.parts[0] not in {"figures", "results"}:
            raise ValueError(f"unrecognized packaged PDF: {relative}")
        return (
            "CC-BY-4.0 + DejaVu-font-license",
            "author-created figure with an embedded DejaVu Sans font subset",
        )
    if relative in TOP_LEVEL_CC_FILES:
        return "CC-BY-4.0", "author-created data, documentation, figure, or derived result"
    if relative.parts and relative.parts[0] in CC_ROOTS and relative.suffix in CC_SUFFIXES:
        return "CC-BY-4.0", "author-created data, documentation, figure, or derived result"
    raise ValueError(
        f"unrecognized packaged file; classify it explicitly before release: {relative}"
    )


def expected_rows() -> list[dict[str, str]]:
    rows = []
    for file_name in sorted(ROOT.rglob("*")):
        if not file_name.is_file():
            continue
        relative = file_name.relative_to(ROOT)
        if (
            relative in SPECIAL
            or IGNORED_PARTS.intersection(relative.parts)
            or relative.name in IGNORED_NAMES
            or any(part.endswith(".egg-info") for part in relative.parts)
        ):
            continue
        try:
            license_id, rationale = license_for(relative)
        except ValueError as error:
            print(f"LICENSE INVENTORY FAIL: {error}", file=sys.stderr)
            raise
        rows.append({"path": relative.as_posix(), "license": license_id, "rationale": rationale})
    return rows


def write_inventory() -> None:
    rows = expected_rows()
    with INVENTORY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "license", "rationale"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"WROTE: {INVENTORY.relative_to(ROOT)}")


def verify_inventory() -> int:
    if not INVENTORY.is_file():
        print("FAIL: LICENSE_INVENTORY.csv is missing")
        return 1
    with INVENTORY.open(newline="", encoding="utf-8") as handle:
        actual = list(csv.DictReader(handle))
    expected = expected_rows()
    if actual != expected:
        actual_paths = {row.get("path", "") for row in actual}
        expected_paths = {row["path"] for row in expected}
        print("LICENSE INVENTORY FAIL")
        for missing in sorted(expected_paths - actual_paths):
            print(f"- unclassified packaged file: {missing}")
        for extra in sorted(actual_paths - expected_paths):
            print(f"- stale inventory entry: {extra}")
        if actual_paths == expected_paths:
            print("- one or more license classifications/rationales differ")
        return 1
    print(
        f"LICENSE INVENTORY VERIFIED: {len(actual)} packaged files classified; "
        "SHA256SUMS and the inventory itself are special factual/license metadata."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_inventory()
    return verify_inventory()


if __name__ == "__main__":
    sys.exit(main())
