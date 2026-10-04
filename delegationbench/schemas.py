"""Typed representations of authoring scenarios and model results."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Decision(str, Enum):
    ACT = "ACT"
    ASK = "ASK"
    REFUSE = "REFUSE"
    DEFER = "DEFER"
    INVALID = "INVALID"


class CandidateAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str = Field(min_length=1)
    arguments: dict[str, Any]
    description: str = Field(min_length=1)


class Factors(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reversibility: Literal["reversible", "partially_reversible", "irreversible"]
    external_visibility: Literal[
        "private", "team_internal", "external", "public", "vendor", "system_users", "not_targeted"
    ]
    stakes: Literal["low", "medium", "high"]
    scope: Literal["explicit", "instrumentally_necessary", "ambiguous_mandate", "expansion"]
    lexical_risk: Literal["low", "high", "not_targeted"]
    consequence_risk: Literal["low", "high", "not_targeted"]


class HumanReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    n_labels: int | None = None
    act_proportion: float | None = None
    ask_proportion: float | None = None
    refuse_proportion: float | None = None
    defer_proportion: float | None = None
    severity_mean: float | None = None


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    pair_id: str | None
    parent_scenario_id: str | None
    split: Literal[
        "core_factor", "lexical_decorrelation", "ambiguity_control",
        "paraphrase_robustness", "adversarial_disagreement",
    ]
    domain: Literal["files", "calendar", "code_system", "communication", "publishing_social", "purchasing"]
    target_factor: Literal[
        "reversibility", "external_visibility", "stakes", "scope",
        "lexical_vs_consequence_risk", "missing_information", "wording", "authorization_boundary",
    ]
    variant: str = Field(min_length=1)
    user_instruction: str = Field(min_length=1)
    context: str = Field(min_length=1)
    candidate_action: CandidateAction
    factors: Factors
    information_complete: bool
    authoring_expectation: Literal["ACT_LEANING", "ASK_LEANING", "DEFER_CONTROL", "DISAGREEMENT_TARGET"]
    authoring_note: str
    possible_confound: str
    human_reference: HumanReference
    quality_status: Literal["draft_unvalidated"]
    paired_with: str | None
    edit_summary: str
    tool_schema_id: str = Field(min_length=1)
    available_decisions: list[Literal["ACT", "ASK", "REFUSE", "DEFER"]]
    authoring_expectation_is_ground_truth: bool


def load_scenarios(path: str) -> list[Scenario]:
    """Load and type-check a JSONL scenario file."""
    import json

    scenarios: list[Scenario] = []
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    scenarios.append(Scenario.model_validate(json.loads(line)))
                except Exception as exc:
                    raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return scenarios
