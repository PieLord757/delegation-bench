from pathlib import Path
import hashlib
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_croissant_file_hashes_match_released_files():
    doc = json.loads((ROOT / "croissant.json").read_text(encoding="utf-8"))
    assert "http://mlcommons.org/croissant/1.0" in doc["conformsTo"]
    assert doc["license"] == "https://creativecommons.org/licenses/by/4.0/"
    files = doc["distribution"]
    assert files
    for item in files:
        path = ROOT / item["contentUrl"]
        assert path.is_file(), item["contentUrl"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], item["contentUrl"]
    record_sets = {rs["@id"] for rs in doc["recordSet"]}
    assert {"scenarios", "vote_distribution", "model_decisions"} <= record_sets


def test_hf_card_configs_point_to_built_files(tmp_path):
    out = tmp_path / "hf_upload"
    result = subprocess.run(
        [sys.executable, "scripts/build_hf_dataset.py", "--output", str(out)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    card = (out / "README.md").read_text(encoding="utf-8")
    header = card.split("---")[1]
    assert "license: cc-by-4.0" in header
    paths = [line.split("path:")[1].strip() for line in header.splitlines() if "path:" in line]
    assert len(paths) == 6
    for rel in paths:
        assert (out / rel).is_file(), rel
    assert (out / "delegationcheck_v1_0.jsonl").read_bytes() == (ROOT / "delegationcheck_v1_0.jsonl").read_bytes()
    counts = {rel: sum(1 for _ in (out / rel).open(encoding="utf-8")) for rel in paths}
    assert counts == {
        "delegationcheck_v1_0.jsonl": 156,
        "data/annotator_votes.jsonl": 156,
        "data/model_decisions.jsonl": 7800,
        "data/tool_loop_outcomes.jsonl": 1435,
        "data/explicit_policy_outcomes.jsonl": 4728,
        "data/paraphrase_outcomes.jsonl": 1152,
    }
    first = json.loads((out / "data/annotator_votes.jsonl").open(encoding="utf-8").readline())
    assert isinstance(first["vote_count_ACT"], int)
