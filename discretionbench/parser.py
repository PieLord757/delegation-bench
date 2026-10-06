"""Conservative model-output normalization."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .schemas import Decision


@dataclass(frozen=True)
class ParsedOutput:
    decision: Decision
    reason: str | None
    status: str


def _objects(text: str):
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
            if isinstance(value, dict):
                yield value
        except json.JSONDecodeError:
            continue


def parse_response(raw: str | None) -> ParsedOutput:
    if not raw or not raw.strip():
        return ParsedOutput(Decision.INVALID, None, "empty")
    text = raw.strip()
    for value in _objects(text):
        candidate = str(value.get("decision", "")).strip().upper()
        if candidate in {d.value for d in Decision if d != Decision.INVALID}:
            reason = value.get("reason")
            return ParsedOutput(Decision(candidate), str(reason).strip() if reason is not None else None, "json")
    # Accept a bare label or a clearly marked decision line, but not a label merely mentioned in prose.
    bare = re.fullmatch(r"[\s`*#]*\b(ACT|ASK|REFUSE|DEFER)\b[\s`*.]*", text, re.I)
    marked = re.search(r"(?im)^\s*(?:decision|answer)\s*[:=-]\s*\*{0,2}(ACT|ASK|REFUSE|DEFER)\b", text)
    match = bare or marked
    if match:
        return ParsedOutput(Decision(match.group(1).upper()), None, "fallback_label")
    return ParsedOutput(Decision.INVALID, None, "unparseable")
