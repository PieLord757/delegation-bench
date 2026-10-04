"""Render a presentation figure from two already-computed audit columns."""

import argparse
from pathlib import Path
import csv
import os
import tempfile

_CACHE_ROOT = Path(tempfile.gettempdir()) / "delegationbench-figure-cache"
os.environ.setdefault("SOURCE_DATE_EPOCH", "1787443200")
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results/policy_consistency_lexical_audit/policy_consistency_rule_model_comparison.csv"
SHORT = {
    "GPT-5.6 Sol": "Sol", "GPT-OSS-120B (Groq)": "OSS-120B",
    "GPT-OSS-20B (Groq)": "OSS-20B", "GPT-5.6 Terra": "Terra",
    "GPT-5.6 Luna": "Luna", "Claude Sonnet 5": "Sonnet",
    "Claude Opus 4.8": "Opus", "Gemini 3.6 Flash": "Flash",
    "Gemini 3.5 Flash-Lite": "Flash-Lite",
    "Qwen 3.6 27B (Groq preview)": "Qwen",
}
OFFSETS = {
    "Sol": (3, -10), "OSS-120B": (3, 5), "OSS-20B": (3, -10),
    "Terra": (3, -10), "Luna": (4, 5), "Sonnet": (3, 5),
    "Opus": (3, -10), "Flash": (-30, 5), "Flash-Lite": (-40, -10),
    "Qwen": (4, -3),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reproduction_outputs/agreement_coherence"),
        help="directory for regenerated figures (the packaged figures are never overwritten)",
    )
    args = parser.parse_args()
    rows = list(csv.DictReader(INPUT.open(newline="")))
    models = [r for r in rows if r["policy"] != "Compact visible rule"]
    rule = next(r for r in rows if r["policy"] == "Compact visible rule")
    fig, ax = plt.subplots(figsize=(6.2, 3.35))
    xs = [100 * float(r["primary_four_way_agreement"]) for r in models]
    ys = [100 * float(r["mean_core_expected_rate"]) for r in models]
    ax.scatter(xs, ys, s=42, color="#2667a7", edgecolor="white", linewidth=.65, zorder=3)
    for r in models:
        name = SHORT[r["policy"]]
        x = 100 * float(r["primary_four_way_agreement"])
        y = 100 * float(r["mean_core_expected_rate"])
        ax.annotate(name, (x, y), xytext=OFFSETS[name], textcoords="offset points", fontsize=7.2)
    rx = 100 * float(rule["primary_four_way_agreement"])
    ry = 100 * float(rule["mean_core_expected_rate"])
    # Same strict authored-direction sign diagnostic as the plotted policies,
    # applied to the three-person panel's ACT-vote share: 20 of 48 pairs.
    # This is a descriptive comparator, not an accuracy target.
    panel_y = 100 * 20 / 48
    ax.axhline(panel_y, color="#777777", lw=.8, ls=(0, (4, 3)), zorder=1)
    ax.text(49.05, panel_y + 1.0, "Annotators' ACT-vote share moves in\nthe designed direction: 20/48",
            ha="left", va="bottom", fontsize=7.0, color="#666666")
    ax.scatter([rx], [ry], marker="*", s=155, color="#b42318", edgecolor="black", linewidth=.55, zorder=4)
    ax.annotate("Keyword rule\n69.1% agreement; 9/48 pairs", (rx, ry),
                xytext=(-6, 14), textcoords="offset points", ha="right", fontsize=7.4,
                color="#8a1c13", arrowprops={"arrowstyle": "-", "color": "#8a1c13", "lw": .7})
    ax.set(xlim=(48.5, 75.5), ylim=(12, 76),
           xlabel="Four-way agreement with the annotators' majority label (%)",
           ylabel="Pair responsiveness:\nshare of 48 pairs that move as designed (%)")
    ax.xaxis.label.set_size(8.5); ax.yaxis.label.set_size(8.5)
    ax.tick_params(labelsize=7.5)
    ax.grid(True, color="#d7dce2", linewidth=.55); ax.set_axisbelow(True)
    ax.text(.01, .985, "Responsiveness measures reaction to the change, not correctness", transform=ax.transAxes,
            va="top", fontsize=7.2, color="#555555")
    for spine in ax.spines.values():
        spine.set_color("#777777"); spine.set_linewidth(.6)
    outdir = args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=.55)
    fig.savefig(outdir / "agreement_vs_controlled_coherence.pdf", bbox_inches="tight")
    fig.savefig(outdir / "agreement_vs_controlled_coherence.png", dpi=300, bbox_inches="tight")
    print(f"WROTE: {outdir.resolve()}")


if __name__ == "__main__":
    main()
