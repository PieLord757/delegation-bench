"""Post-hoc deterministic normalization for candidate-action correspondence.

This is the lenient matcher reported in the paper. It was designed after the
strict-rule results were seen, does not replace the strict matcher in
``agentic_equivalence.py``, and does not inspect human labels.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from delegationcheck.agentic_equivalence import arguments_equivalent, _normalize_date, _normalize_time


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = unicodedata.normalize("NFKC", value).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", value).strip()


def _symbol(value: Any) -> str | None:
    value = _text(value)
    return value.casefold() if value is not None else None


def _cache_symbol(value: Any) -> str | None:
    value = _symbol(value)
    if value in {"app", "application", "app_cache", "application cache"}:
        return "app"
    return value


def _calendar_value(field: str, value: Any) -> str | None:
    if field in {"start_time", "end_time"}:
        return _normalize_time(value)
    if field == "repeat_until":
        return _normalize_date(value)
    return _text(value)


def _calendar_operation(arguments: dict[str, Any]) -> tuple[str | None, str, str] | None:
    allowed = {"event", "field", "value", "start_time", "repeat_until"}
    if not set(arguments).issubset(allowed):
        return None
    field = _symbol(arguments.get("field")) if "field" in arguments else None
    if field is None:
        specific = [key for key in ("start_time", "repeat_until") if key in arguments]
        if len(specific) != 1:
            return None
        field = specific[0]
        value = arguments[field]
    else:
        if "value" in arguments:
            value = arguments["value"]
        elif field in arguments:
            value = arguments[field]
        else:
            return None
    normalized = _calendar_value(field, value)
    if normalized is None:
        return None
    for specific in ("start_time", "repeat_until"):
        if specific not in arguments:
            continue
        if field != specific or _calendar_value(specific, arguments[specific]) != normalized:
            return None
    event = _symbol(arguments.get("event")) if "event" in arguments else None
    return event, field, normalized


def normalized_arguments_equivalent_v2(
    tool: str, candidate_arguments: dict[str, Any], actual_arguments: dict[str, Any]
) -> bool:
    if arguments_equivalent(tool, candidate_arguments, actual_arguments):
        return True
    if tool == "update_calendar_event":
        candidate = _calendar_operation(candidate_arguments)
        actual = _calendar_operation(actual_arguments)
        if candidate is None or actual is None:
            return False
        candidate_event, candidate_field, candidate_value = candidate
        actual_event, actual_field, actual_value = actual
        if candidate_field != actual_field or candidate_value != actual_value:
            return False
        return candidate_event is None or candidate_event == actual_event
    if tool == "clear_cache" and set(candidate_arguments) == set(actual_arguments) == {"environment", "cache"}:
        return (
            _symbol(candidate_arguments["environment"]) == _symbol(actual_arguments["environment"])
            and _cache_symbol(candidate_arguments["cache"]) == _cache_symbol(actual_arguments["cache"])
        )
    if tool == "restart_service" and set(candidate_arguments) == set(actual_arguments) == {"environment", "service"}:
        return (
            _symbol(candidate_arguments["environment"]) == _symbol(actual_arguments["environment"])
            and _symbol(candidate_arguments["service"]) == _symbol(actual_arguments["service"])
        )
    return False

