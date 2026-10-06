"""The rendered prompts must stay identical to the ones used in the paper."""

import hashlib
import json
from pathlib import Path

from discretionbench import study_prompts as sp
from discretionbench.prompts_main import build_prompt
from discretionbench.schemas import load_scenarios

ROOT = Path(__file__).resolve().parents[1]

# SHA-256 over every rendered main-study, Tool-Loop, Post-Approval, and
# elicitation prompt, in dataset order.
EXPECTED_PROMPTS_SHA256 = "6c3dd626161279a9b35dedf2d3bf29efcba1eb72ff35bd73acdad8dc3b0f03c3"
EXPECTED_STRICT_ENVELOPE_SHA256 = "d19afadb1172c4504b635555f788e8d27a9c17b6b14d4eb2b7b0e6bb31600eb9"


def test_rendered_prompts_match_paper_versions():
    scenarios = load_scenarios(str(ROOT / "discretionbench_v1_0.jsonl"))
    manifest = json.loads((ROOT / "data/measurement_robustness_v1_ids.json").read_text())
    elicitation_ids = set(manifest["scenario_ids"])
    digest = hashlib.sha256()
    for scenario in scenarios:
        digest.update(build_prompt(scenario).encode())
        digest.update(sp.tool_loop_prompt(scenario).encode())
        digest.update(sp.post_approval_prompt(scenario, "Q?").encode())
        if scenario.scenario_id in elicitation_ids:
            for fmt in sp.ELICITATION_FORMATS:
                digest.update(sp.elicitation_prompt(scenario, fmt).encode())
    assert digest.hexdigest() == EXPECTED_PROMPTS_SHA256


def test_agent_envelope_schema_is_stable():
    schema = sp.agent_envelope_schema(strict_arguments=True)
    encoded = json.dumps(schema, sort_keys=True).encode()
    assert hashlib.sha256(encoded).hexdigest() == EXPECTED_STRICT_ENVELOPE_SHA256
    assert len(sp.tool_loop_tools()) == 15


def test_tool_loop_prompt_hides_candidate_action():
    scenario = load_scenarios(str(ROOT / "discretionbench_v1_0.jsonl"))[0]
    prompt = sp.tool_loop_prompt(scenario)
    assert scenario.candidate_action.description not in prompt
    assert "candidate" not in prompt.lower()
