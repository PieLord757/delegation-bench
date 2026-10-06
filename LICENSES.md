# Licensing

This file sets out which license covers which material. It grants no rights
beyond material the author controls. `LICENSE_INVENTORY.csv` lists every file
with its license, and `python scripts/verify_license_inventory.py` checks that
the list is complete.

## MIT License (`LICENSE`)

- `discretionbench/*.py`
- `scripts/*.py`
- `tests/*.py`
- `tool_loop/environment.py`
- `pyproject.toml` and `requirements-tested.txt`

## CC BY 4.0 (`LICENSE-DATA.md`)

- `discretionbench_v1_0.jsonl`
- documentation (`README.md`, `DATASET_CARD.md`, `SCHEMA.md`,
  `BENCHMARK_USE.md`, `REPRODUCING.md`, `CONTAMINATION_CANARY.md`, and the
  README files in subdirectories)
- scenario manifests and tool schemas under `data/` and `tool_loop/`
- the annotators' majority labels and vote counts, which contain no annotator
  identity, notes, confidence ratings, or link between a vote and a person
- the categorical model decisions and Tool-Loop classifications under
  `data/derived/`, which are deterministic classifications made by the author
  and contain no model-written text
- result tables under `results/` and figures under `figures/` and
  `results/**/figures/`

## Third-party material

The PDF figures embed a subset of the DejaVu Sans font. The plots and data are
covered by CC BY 4.0, and the embedded font remains under the DejaVu Fonts
license in `THIRD_PARTY_NOTICES/DEJAVU_FONTS_LICENSE.txt`. PNG figures contain
rasterized glyphs, not a font program.

Python dependencies are not included; their own licenses apply when you
install them. Provider and model names are used only to describe what was
evaluated.

## Not included

Raw and canonical provider responses are not included, and no license to
redistribute provider-generated text is claimed. The tool arguments released in
`data/derived/tool_loop_sanitized_tool_calls.csv` come only from OpenAI-,
Anthropic-, and Google-hosted models. Raw annotator workbooks, notes,
confidence ratings, and identity records are not included.
