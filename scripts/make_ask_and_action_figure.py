#!/usr/bin/env python3
"""Rebuild the paper's judging-versus-acting figure from two released tables."""

import argparse
import csv
import os
import tempfile
from pathlib import Path

_CACHE_ROOT = Path(tempfile.gettempdir()) / "discretionbench-figure-cache"
os.environ.setdefault("SOURCE_DATE_EPOCH", "1787443200")
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

SHORT = {
    "GPT-5.6 Sol": "Sol", "GPT-5.6 Terra": "Terra", "GPT-5.6 Luna": "Luna",
    "GPT-OSS-120B": "OSS-120B", "GPT-OSS-20B": "OSS-20B",
    "Claude Sonnet 5": "Sonnet", "Claude Opus 4.8": "Opus",
    "Gemini 3.6 Flash": "Flash", "Gemini 3.5 Flash-Lite": "Flash-Lite",
    "Qwen 3.6 27B": "Qwen",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class Row(dict):
    __getattr__ = dict.__getitem__


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reproduction_outputs/ask_and_action_stages"),
        help="directory for regenerated figures (the packaged figures are never overwritten)",
    )
    out = parser.parse_args().output_dir
    out.mkdir(parents=True, exist_ok=True)
    ask_rows = read_rows(ROOT / "results/reviewer_extraction/same48_ask_by_endpoint.csv")
    stage_rows = read_rows(ROOT / "results/story_first/action_stage_profile.csv")
    rename = {"Gemini 3.6 Flash (corrected)": "Gemini 3.6 Flash"}
    ask_by_model = {rename.get(r["model"], r["model"]): r for r in ask_rows}
    stage_by_model = {r["model"]: r for r in stage_rows}
    order = [r["model"] for r in sorted(stage_rows, key=lambda r: -float(r["offline_act_rate"]))]
    ask = [Row({k: (float(v) if k.endswith("_rate") else v) for k, v in ask_by_model[m].items()}) for m in order]
    stages = [Row({k: (float(v) if k.endswith("_rate") else v) for k, v in stage_by_model[m].items()}) for m in order]
    labels = [SHORT[x] for x in order]
    y = np.arange(len(order))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.85), gridspec_kw={"wspace": .33})

    ax = axes[0]
    for i, row in enumerate(ask):
        ax.plot([100*row.offline_ask_rate, 100*row.tool_loop_ask_rate], [i, i],
                color="#b8b8b8", lw=1.1, zorder=1)
    ax.scatter([100*r.offline_ask_rate for r in ask], y, label="Judging a shown action", color="#7b3294",
               s=30, marker="o", edgecolor="white", lw=.4, zorder=3)
    ax.scatter([100*r.tool_loop_ask_rate for r in ask], y, label="Acting with tools (Tool-Loop)", color="#008837",
               s=34, marker="s", edgecolor="white", lw=.4, zorder=3)
    ax.set_title("A. Asking the user: judging vs acting", loc="left", fontweight="bold")
    ax.set_xlabel("Scenarios ending in a question to the user (%)")
    ax.set_xlim(0, 52)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(.5, -.16), fontsize=7.5)

    ax = axes[1]
    specs = [
        ("offline_act_rate", "Judged act rate", "#4d4d4d", "o"),
        ("candidate_tool_rate", "Proposed tool called", "#2166ac", "s"),
    ]
    for i, row in enumerate(stages):
        xs = [100*row[c] for c, _, _, _ in specs]
        ax.plot(xs, [i]*len(specs), color="#d3d3d3", lw=1.1, zorder=1)
    for col, label, color, marker in specs:
        ax.scatter([100*r[col] for r in stages], y, label=label, color=color, marker=marker,
                   s=31, edgecolor="white", lw=.4, zorder=3)
    ax.set_title("B. Model orderings differ", loc="left", fontweight="bold")
    ax.set_xlabel("Rate on the 29 measurable scenarios (%)")
    ax.set_xlim(25, 87)
    ax.set_yticks(y, [])
    # Panel B reuses panel A\'s row labels, so both panels must share orientation.
    ax.invert_yaxis()
    assert axes[0].yaxis_inverted() == axes[1].yaxis_inverted(), (
        "panel A and panel B must share the same y-axis orientation since panel B relies on "
        "panel A's labels for row identity"
    )
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(.5, -.16), fontsize=7.5)
    ax.text(.98, .02,
            "Calls to the proposed tool that match it:\nstrict 59.3%; lenient 89.0%; reviewers 93.9%, 96.0%",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.2,
            color="#333333", bbox={"boxstyle": "round,pad=.25", "fc": "white", "ec": "#cccccc"})

    for ax in axes:
        ax.grid(axis="x", color="#eeeeee", lw=.7)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)

    fig.subplots_adjust(left=.12, right=.995, top=.91, bottom=.22)
    fig.savefig(out / "ask_and_action_stages.pdf", bbox_inches="tight", pad_inches=.02)
    fig.savefig(out / "ask_and_action_stages.png", dpi=300, bbox_inches="tight", pad_inches=.02)
    print(f"WROTE: {out.resolve()}")


if __name__ == "__main__":
    main()
