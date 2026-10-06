#!/usr/bin/env python3
"""Verify file checksums, dataset counts, and headline invariants of the release."""

from pathlib import Path
import csv
from collections import Counter
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


manifest = ROOT / "SHA256SUMS"
checked = 0
for line in manifest.read_text(encoding="utf-8").splitlines():
    expected, rel = line.split(maxsplit=1)
    rel = rel.lstrip("*")
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing manifest file: {rel}")
    if digest(path) != expected:
        fail(f"hash mismatch: {rel}")
    checked += 1

dataset_hash = digest(ROOT / "discretionbench_v1_0.jsonl")
expected_dataset_hash = "3ecc96cb79946f46afc27161c59b7a0661a545be8f0b6e46cc289fba514ac405"
if dataset_hash != expected_dataset_hash:
    fail("dataset hash mismatch")

reference = list(csv.DictReader((ROOT / "data/reference/expert_majority_reference.csv").open()))
resolved = [r for r in reference if r["reference_status"] != "UNRESOLVED"]
if len(reference) != 156 or len(resolved) != 149:
    fail(f"unexpected reference counts: {len(reference)} total, {len(resolved)} resolved")

votes = list(csv.DictReader((ROOT / "data/reference/panel_vote_distribution.csv").open()))
vote_columns = [
    "vote_count_ACT",
    "vote_count_ASK_AUTHORIZATION",
    "vote_count_REQUEST_INFORMATION",
    "vote_count_REFUSE",
]
if len(votes) != 156 or any(sum(int(r[c]) for c in vote_columns) != 3 for r in votes):
    fail("panel vote projection must contain 156 rows with three unlinkable votes each")
if any(any(key.startswith("expert_") for key in r) for r in votes):
    fail("panel vote projection exposes an annotator-linked field")

comparison = list(csv.DictReader((ROOT / "results/policy_consistency_lexical_audit/policy_consistency_rule_model_comparison.csv").open()))
rule = next(r for r in comparison if r["policy"] == "Compact visible rule")
if abs(float(rule["primary_four_way_agreement"]) - 0.6912751677852349) > 1e-12:
    fail("compact-rule agreement drift")
if abs(float(rule["mean_core_expected_rate"]) - 0.1875) > 1e-12:
    fail("compact-rule controlled-pair drift")
model_expected = [float(r["mean_core_expected_rate"]) for r in comparison if r["policy"] != "Compact visible rule"]
if abs(min(model_expected) - 22 / 48) > 1e-12 or abs(max(model_expected) - 34 / 48) > 1e-12:
    fail("model controlled-pair range drift")

core = list(csv.DictReader((ROOT / "results/policy_consistency_lexical_audit/policy_consistency_core_pairs.csv").open()))
panel_rows = [r for r in core if r["row_type"] == "summary" and r["policy"] == "Expert panel ACT-vote share"]
if sum(int(r["expected_count"]) for r in panel_rows) != 20 or sum(int(r["n_pairs"]) for r in panel_rows) != 48:
    fail("panel 20/48 controlled-response comparator drift")

model_reference = list(csv.DictReader((ROOT / "data/reference/final_model_vs_expert_reference.csv").open()))
primary = [float(r["four_way_agreement_propensity"]) for r in model_reference if r["population"] == "all_resolved_149"]
if abs(min(primary) - 0.5060402684563758) > 1e-12 or abs(max(primary) - 0.734228187919463) > 1e-12:
    fail("primary model-reference agreement range drift")

calibration = list(csv.DictReader((ROOT / "results/next_existing_data_analyses/probabilistic_expert_calibration.csv").open()))
all156 = [float(r["multiclass_brier"]) for r in calibration if r["population"] == "all_156" and r["invalid_handling"] == "invalid_retained"]
if abs(min(all156) - 0.33629629629629637) > 1e-12 or abs(max(all156) - 0.6480911680911681) > 1e-12:
    fail("panel-vote Brier range drift")

agreement_summary = {r["metric"]: float(r["value"]) for r in csv.DictReader((ROOT / "data/reference/final_expert_agreement_summary.csv").open())}
if abs(agreement_summary["four_way_krippendorff_alpha"] - 0.43679306057019573) > 1e-12:
    fail("four-way panel alpha drift")
if abs(agreement_summary["binary_krippendorff_alpha"] - 0.543170911775563) > 1e-12:
    fail("binary panel alpha drift")

correlations = list(csv.DictReader((ROOT / "results/posthoc_tool_loop_mismatch_scenario_correlations.csv").open()))
equiv = [float(r["corr_offline_vs_candidate_equivalent"]) for r in correlations]
tool = [float(r["corr_offline_vs_candidate_tool"]) for r in correlations]
if abs(min(equiv) - 0.276596768283603) > 1e-12 or abs(max(equiv) - 0.46701319447402534) > 1e-12:
    fail("candidate-equivalent correlation range drift")
if abs(min(tool) - 0.4134795504132383) > 1e-12 or abs(max(tool) - 0.6712885682588444) > 1e-12:
    fail("candidate-tool correlation range drift")

license_code = (ROOT / "LICENSE").read_text(encoding="utf-8")
license_data = (ROOT / "LICENSE-DATA.md").read_text(encoding="utf-8")
inventory = (ROOT / "LICENSES.md").read_text(encoding="utf-8")
if "MIT License" not in license_code:
    fail("code license is not the expected MIT license")
if "Creative Commons Attribution 4.0 International" not in license_data:
    fail("data license is not the expected CC BY 4.0 license")
if "Raw and canonical provider responses are not included" not in inventory:
    fail("licensing inventory does not document withheld provider responses")
font_notice = (ROOT / "THIRD_PARTY_NOTICES/DEJAVU_FONTS_LICENSE.txt").read_text(
    encoding="utf-8"
)
if "Bitstream Vera Fonts Copyright" not in font_notice:
    fail("DejaVu embedded-font license notice is missing or incomplete")
license_check = subprocess.run(
    [sys.executable, str(ROOT / "scripts/verify_license_inventory.py")],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
if license_check.returncode != 0:
    fail("file-level licensing inventory is incomplete or stale: " + license_check.stdout.strip())

trial_path_file = ROOT / "results/tool_loop_three_stage/three_stage_trial_paths.csv"
trial_paths = list(csv.DictReader(trial_path_file.open()))
conditions = {r["condition"] for r in trial_paths}
scenarios = {r["scenario_id"] for r in trial_paths}
group_counts = Counter((r["condition"], r["scenario_id"]) for r in trial_paths)
binary_columns = (
    "offline_act",
    "candidate_tool",
    "candidate_equivalent",
    "joint_a_t_e",
    "same_tool_non_equivalent",
    "no_candidate_tool",
)
if len(trial_paths) != 580 or len(conditions) != 4 or len(scenarios) != 29:
    fail("unexpected Tool-Loop audit-view dimensions")
if set(group_counts.values()) != {5}:
    fail("Tool-Loop audit view does not contain five trials per condition/scenario")
if any(r[col] not in {"0", "1"} for r in trial_paths for col in binary_columns):
    fail("Tool-Loop audit view contains a non-binary derived classification")

for script_name in ("verify_derived_release.py",):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script_name)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    if check.returncode != 0:
        fail(f"{script_name} failed: " + check.stderr.strip())

print(f"VERIFIED: {checked} manifest files")
print("VERIFIED: dataset hash and 156/149 reference counts")
print("VERIFIED: 156-row unlinkable panel vote-count projection")
print("VERIFIED: compact-rule 69.1% agreement and 9/48 controlled-pair response")
print("VERIFIED: model agreement/Brier/coherence, panel 20/48 and alpha, and Tool-Loop correlation ranges")
print("VERIFIED: MIT/CC BY 4.0 licensing boundary and withheld-output disclosure")
print("VERIFIED: deterministic file-level license inventory")
print("VERIFIED: 580-row four-model Tool-Loop audit view")
print("VERIFIED: released categorical decision/Tool-Loop projections")
