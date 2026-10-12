#!/usr/bin/env python3
"""Validate a DelegationCheck JSONL file without changing it."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from delegationcheck.validation import validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", nargs="?", default="delegationcheck_v1_0.jsonl")
    args = parser.parse_args()
    report = validate_dataset(Path(args.data))
    print(f"Validated records: {report.records}")
    print("Splits: " + ", ".join(f"{k}={v}" for k, v in sorted(report.split_counts.items())))
    print("Domains: " + ", ".join(f"{k}={v}" for k, v in sorted(report.domain_counts.items())))
    print(f"Errors: {len(report.errors)}")
    for error in report.errors:
        print(f"  ERROR: {error}")
    print(f"Warnings: {len(report.warnings)}")
    for warning in report.warnings:
        print(f"  WARNING: {warning}")
    print("VALID" if report.valid else "INVALID")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
