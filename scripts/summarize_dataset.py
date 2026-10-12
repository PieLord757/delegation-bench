#!/usr/bin/env python3
"""Print dataset composition without model or annotator data."""

from collections import Counter
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
rows = [json.loads(x) for x in (ROOT / "delegationcheck_v1_0.jsonl").read_text().splitlines() if x.strip()]

print(f"scenarios: {len(rows)}")
print("splits:")
for key, value in sorted(Counter(r["split"] for r in rows).items()):
    print(f"  {key}: {value}")
print("domains:")
for key, value in sorted(Counter(r["domain"] for r in rows).items()):
    print(f"  {key}: {value}")
core_pairs = {r["pair_id"] for r in rows if r["split"] == "core_factor"}
print(f"core matched pairs: {len(core_pairs)}")
print(f"paraphrases with parents: {sum(bool(r['parent_scenario_id']) for r in rows)}")
