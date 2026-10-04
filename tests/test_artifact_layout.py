from pathlib import Path
import csv
import hashlib
import importlib.util
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_documented_artifact_verifier():
    result = subprocess.run(
        [sys.executable, "scripts/verify_artifact.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "VERIFIED" in result.stdout


def test_documented_dataset_summary():
    result = subprocess.run(
        [sys.executable, "scripts/summarize_dataset.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "scenarios: 156" in result.stdout
    assert "core matched pairs: 48" in result.stdout


def test_file_level_license_inventory():
    result = subprocess.run(
        [sys.executable, "scripts/verify_license_inventory.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "LICENSE INVENTORY VERIFIED" in result.stdout


def test_license_classifier_fails_closed_on_unknown_files():
    script = ROOT / "scripts/verify_license_inventory.py"
    spec = importlib.util.spec_from_file_location("license_inventory", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="classify it explicitly"):
        module.license_for(Path("unexpected-third-party.bin"))
    with pytest.raises(ValueError, match="not releasable"):
        module.license_for(Path("results/another_dataset.jsonl"))
    with pytest.raises(ValueError, match="not releasable"):
        module.license_for(Path("results/raw_provider_responses.json"))


def test_tested_direct_dependency_versions_are_recorded():
    requirements = set(
        (ROOT / "requirements-tested.txt").read_text(encoding="utf-8").splitlines()
    )
    assert requirements == {
        "pydantic==2.12.0",
        "pytest==7.4.4",
        "matplotlib==3.9.2",
        "numpy==1.26.4",
        "scipy==1.13.1",
        "scikit-learn==1.5.1",
    }


def test_panel_projection_is_unlinkable():
    path = ROOT / "data/reference/panel_vote_distribution.csv"
    rows = list(csv.DictReader(path.open(newline="")))
    assert len(rows) == 156
    assert not any(key.startswith("expert_") for key in rows[0])
    assert not (ROOT / "data/reference/final_expert_unresolved_scenarios.csv").exists()


def test_tool_loop_summary_reconstructs(tmp_path):
    output = tmp_path / "summary.csv"
    result = subprocess.run(
        [sys.executable, "scripts/reconstruct_tool_loop_summary.py", "--output", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "RECONSTRUCTED AND MATCHED: 4 conditions" in result.stdout
    assert output.is_file()


def test_released_categorical_views_verify():
    result = subprocess.run(
        [sys.executable, "scripts/verify_derived_release.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "7,800 categorical primary decisions" in result.stdout


def test_hero_figure_reproduces_byte_for_byte(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/make_agreement_coherence_figure.py",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    for suffix in ("pdf", "png"):
        expected = ROOT / (
            "figures/policy_consistency_lexical_audit/"
            f"agreement_vs_controlled_coherence.{suffix}"
        )
        reproduced = tmp_path / f"agreement_vs_controlled_coherence.{suffix}"
        assert hashlib.sha256(expected.read_bytes()).digest() == hashlib.sha256(
            reproduced.read_bytes()
        ).digest()


def test_ask_and_action_figure_reproduces_byte_for_byte(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/make_ask_and_action_figure.py", "--output-dir", str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    for suffix in ("pdf", "png"):
        expected = ROOT / f"figures/final_reviewer_first/ask_and_action_stages.{suffix}"
        reproduced = tmp_path / f"ask_and_action_stages.{suffix}"
        assert expected.read_bytes() == reproduced.read_bytes()
