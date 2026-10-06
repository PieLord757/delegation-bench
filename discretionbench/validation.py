"""Cross-record validation that never mutates the authoring dataset."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .schemas import Scenario


@dataclass
class ValidationReport:
    records: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    split_counts: Counter[str] = field(default_factory=Counter)
    domain_counts: Counter[str] = field(default_factory=Counter)

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_dataset(path: str | Path) -> ValidationReport:
    report = ValidationReport()
    scenarios: list[Scenario] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                report.warnings.append(f"line {line_no}: blank line")
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                report.errors.append(f"line {line_no}: invalid JSON: {exc.msg}")
                continue
            try:
                scenarios.append(Scenario.model_validate(value))
            except ValidationError as exc:
                details = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
                report.errors.append(f"line {line_no}: schema error: {details}")

    report.records = len(scenarios)
    report.split_counts.update(s.split for s in scenarios)
    report.domain_counts.update(s.domain for s in scenarios)
    by_id: dict[str, Scenario] = {}
    for scenario in scenarios:
        if scenario.scenario_id in by_id:
            report.errors.append(f"duplicate scenario_id: {scenario.scenario_id}")
        else:
            by_id[scenario.scenario_id] = scenario

        if scenario.candidate_action.tool != scenario.tool_schema_id:
            report.errors.append(f"{scenario.scenario_id}: candidate tool and tool_schema_id differ")
        if scenario.available_decisions != ["ACT", "ASK", "REFUSE", "DEFER"]:
            report.errors.append(f"{scenario.scenario_id}: available_decisions must be ACT, ASK, REFUSE, DEFER")
        if scenario.authoring_expectation_is_ground_truth:
            report.errors.append(f"{scenario.scenario_id}: authoring expectation is incorrectly marked as ground truth")
        if scenario.split == "ambiguity_control":
            if scenario.information_complete:
                report.errors.append(f"{scenario.scenario_id}: ambiguity control must be informationally incomplete")
            if scenario.target_factor != "missing_information":
                report.errors.append(f"{scenario.scenario_id}: ambiguity control target must be missing_information")
        elif not scenario.information_complete:
            report.errors.append(f"{scenario.scenario_id}: only ambiguity controls may be incomplete")
        split_targets = {
            "core_factor": {"reversibility", "external_visibility", "stakes", "scope"},
            "lexical_decorrelation": {"lexical_vs_consequence_risk"},
            "ambiguity_control": {"missing_information"},
            "paraphrase_robustness": {"wording"},
            "adversarial_disagreement": {"authorization_boundary"},
        }
        if scenario.target_factor not in split_targets[scenario.split]:
            report.errors.append(f"{scenario.scenario_id}: target_factor is inconsistent with split {scenario.split}")

    family_members: dict[str, list[Scenario]] = defaultdict(list)
    pair_members: dict[str, list[Scenario]] = defaultdict(list)
    for scenario in scenarios:
        family_members[scenario.family_id].append(scenario)
        if scenario.pair_id:
            pair_members[scenario.pair_id].append(scenario)

        if scenario.paired_with:
            other = by_id.get(scenario.paired_with)
            if other is None:
                report.errors.append(f"{scenario.scenario_id}: paired_with target does not exist: {scenario.paired_with}")
            else:
                if other.paired_with != scenario.scenario_id:
                    report.errors.append(f"{scenario.scenario_id}: paired_with is not reciprocal")
                if other.pair_id != scenario.pair_id or other.family_id != scenario.family_id:
                    report.errors.append(f"{scenario.scenario_id}: pair target has inconsistent pair/family IDs")
        if scenario.parent_scenario_id:
            parent = by_id.get(scenario.parent_scenario_id)
            if parent is None:
                report.errors.append(f"{scenario.scenario_id}: parent does not exist: {scenario.parent_scenario_id}")
            elif scenario.split != "paraphrase_robustness":
                report.errors.append(f"{scenario.scenario_id}: only paraphrases may have a parent")
            elif parent.family_id != scenario.family_id:
                report.errors.append(f"{scenario.scenario_id}: parent belongs to another family")

    for pair_id, members in pair_members.items():
        if len(members) != 2:
            report.errors.append(f"{pair_id}: expected 2 pair members, found {len(members)}")
            continue
        if any(m.split != "core_factor" for m in members):
            report.errors.append(f"{pair_id}: matched pairs must belong to core_factor")
        if {m.variant for m in members} != {"low", "high"}:
            report.errors.append(f"{pair_id}: matched pair variants must be low/high")
        if len({m.target_factor for m in members}) != 1:
            report.errors.append(f"{pair_id}: matched pair target_factor differs")

    for scenario in scenarios:
        in_pair = scenario.pair_id is not None and scenario.paired_with is not None
        if scenario.split == "core_factor" and not in_pair:
            report.errors.append(f"{scenario.scenario_id}: core_factor scenario lacks complete pair references")
        if scenario.split != "core_factor" and (scenario.pair_id or scenario.paired_with):
            report.errors.append(f"{scenario.scenario_id}: non-core scenario has pair references")
        if scenario.split == "paraphrase_robustness" and not scenario.parent_scenario_id:
            report.errors.append(f"{scenario.scenario_id}: paraphrase lacks parent")
        if scenario.split != "paraphrase_robustness" and scenario.parent_scenario_id:
            report.errors.append(f"{scenario.scenario_id}: non-paraphrase has parent")

    for family_id, members in family_members.items():
        core = [m for m in members if m.split == "core_factor"]
        if core and len({m.domain for m in core}) != 1:
            report.errors.append(f"{family_id}: core family spans multiple domains")
        if core and len({m.target_factor for m in core}) != 1:
            report.errors.append(f"{family_id}: core family spans multiple target factors")

    if not report.split_counts.get("core_factor"):
        report.errors.append("dataset has no core_factor scenarios")
    for split, count in report.split_counts.items():
        if count < 2:
            report.warnings.append(f"split {split} contains only {count} scenario(s)")
    return report
