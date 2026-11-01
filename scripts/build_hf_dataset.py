#!/usr/bin/env python3
"""Assemble the folder that is uploaded as the Hugging Face dataset.

The Hugging Face loader uses one file format per dataset repository, so the
released CSV tables are written as JSON Lines next to an unchanged copy of
delegationcheck_v1_0.jsonl. Integer columns are written as integers and empty
cells as null; nothing else changes. See hf_dataset/UPLOAD.md.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "data/annotator_votes.jsonl": "data/reference/panel_vote_distribution.csv",
    "data/model_decisions.jsonl": "data/derived/decision_by_scenario_trial.csv",
    "data/tool_loop_outcomes.jsonl": "data/derived/tool_loop_trial_classification.csv",
    "data/explicit_policy_outcomes.jsonl": "explicit_rules/outcomes/explicit_policy_outcomes.csv",
    "data/paraphrase_outcomes.jsonl": "explicit_rules/outcomes/paraphrase_outcomes.csv",
}
INTEGER = re.compile(r"-?\d+")


def convert(source: Path, target: Path) -> int:
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    columns = list(rows[0])
    integer_columns = {
        c for c in columns
        if all(INTEGER.fullmatch(r[c]) for r in rows if r[c] != "") and any(r[c] != "" for r in rows)
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as out:
        for r in rows:
            record = {
                c: (None if r[c] == "" else int(r[c]) if c in integer_columns else r[c])
                for c in columns
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path, help="empty or new folder to write")
    args = parser.parse_args()
    out = args.output
    if out.exists() and any(out.iterdir()):
        print(f"refusing to write into non-empty folder: {out}", file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "hf_dataset/README.md", out / "README.md")
    shutil.copyfile(ROOT / "delegationcheck_v1_0.jsonl", out / "delegationcheck_v1_0.jsonl")
    print(f"delegationcheck_v1_0.jsonl: 156 scenarios (unchanged copy)")
    for target, source in TABLES.items():
        n = convert(ROOT / source, out / target)
        print(f"{target}: {n} rows from {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
