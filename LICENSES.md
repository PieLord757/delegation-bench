# Licensing

This file sets out which license covers which material. It grants no rights
beyond material the author controls. `LICENSE_INVENTORY.csv` lists every file
with its license, and `python scripts/verify_license_inventory.py` checks that
the list is complete.

## MIT License (`LICENSE`)

- `delegationcheck/*.py` (including `delegationcheck/explicit_rules.py`)
- `scripts/*.py`
- `tests/*.py`
- `tool_loop/environment.py`
- `pyproject.toml` and `requirements-tested.txt`

## CC BY 4.0 (`LICENSE-DATA.md`)

- `delegationcheck_v1_0.jsonl`
- documentation (`README.md`, `DATASET_CARD.md`, `DATASHEET.md`, `SCHEMA.md`,
  `BENCHMARK_USE.md`, `REPRODUCING.md`, `CONTAMINATION_CANARY.md`, the
  Hugging Face card and notes in `hf_dataset/`, and the README files in
  subdirectories)
- the Croissant metadata file `croissant.json`
- scenario manifests and tool schemas under `data/` and `tool_loop/`
- the annotators' majority labels and vote counts, which contain no annotator
  identity, notes, confidence ratings, or link between a vote and a person
- the categorical model decisions and Tool-Loop classifications under
  `data/derived/`, which are deterministic classifications made by the author
  and contain no model-written text
- result tables under `results/` and figures under `figures/` and
  `results/**/figures/`
- the explicit-rule cases, categorical outcomes, and documentation under
  `explicit_rules/`, except `explicit_rules/third_party/`

## Third-party material

The PDF figures embed a subset of the DejaVu Sans font. The plots and data are
covered by CC BY 4.0, and the embedded font remains under the DejaVu Fonts
license in `THIRD_PARTY_NOTICES/DEJAVU_FONTS_LICENSE.txt`. PNG figures contain
rasterized glyphs, not a font program.

`explicit_rules/third_party/tau_bench/` contains nine unmodified files from
tau-bench (<https://github.com/sierra-research/tau-bench>, revision
`59a200c6d575d595120f1cb70fea53cef0632f6b`): the retail policy, the test task
list, the user and order databases, the tool base class, and three retail
tools. They remain under tau-bench's MIT License, copyright 2024 Sierra, which
is reproduced in that directory and in
`THIRD_PARTY_NOTICES/TAU_BENCH_LICENSE.txt`. The tau-bench decision points in
`explicit_rules/cases/tau_bench_decision_points.json` copy task instructions
and user and order records from those files; that copied material stays under
tau-bench's MIT License, and the rest of the file is under CC BY 4.0.

Python dependencies are not included; their own licenses apply when you
install them. Provider and model names are used only to describe what was
evaluated.

## Not included

Raw and canonical provider responses are not included, and no license to
redistribute provider-generated text is claimed. The tool arguments released in
`data/derived/tool_loop_sanitized_tool_calls.csv` come only from OpenAI-,
Anthropic-, and Google-hosted models. Raw annotator workbooks, notes,
confidence ratings, and identity records are not included.
