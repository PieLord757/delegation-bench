"""In-memory tools; no real external or filesystem side effects."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SCHEMA_PATH = Path(__file__).resolve().parent / "tool_schemas.json"
_TOOL_SCHEMAS = {t["name"]: t["parameters"] for t in json.loads(_SCHEMA_PATH.read_text())["tools"]}

ALLOWED_TOOLS = set(_TOOL_SCHEMAS)


def _schema_error(tool_name: str, arguments: dict[str, Any]) -> str | None:
    """Return a structured error message, or None if arguments satisfy the schema."""
    schema = _TOOL_SCHEMAS[tool_name]
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    missing = [k for k in required if k not in arguments]
    if missing:
        return f"missing required arguments: {sorted(missing)}"
    if schema.get("additionalProperties") is False:
        extra = [k for k in arguments if k not in properties]
        if extra:
            return f"unsupported arguments: {sorted(extra)}"
    for key, value in arguments.items():
        allowed = properties.get(key, {}).get("enum")
        if allowed is not None and value not in allowed:
            return f"argument {key!r} must be one of {allowed}"
    return None


@dataclass
class MockToolEnvironment:
    calls: list[dict[str, Any]] = field(default_factory=list)

    def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in ALLOWED_TOOLS:
            raise ValueError(f"Unknown mock tool: {tool_name}")
        error = _schema_error(tool_name, arguments)
        if error is not None:
            event = {"tool": tool_name, "arguments": dict(arguments), "simulated": True}
            return {"status": "schema_error", "side_effect_applied": False, "error": error, "event": event}
        event = {"tool": tool_name, "arguments": dict(arguments), "simulated": True}
        self.calls.append(event)
        return {"status": "simulated_success", "side_effect_applied": False, "event": event}

    def snapshot(self) -> dict[str, Any]:
        return {"calls": list(self.calls), "real_side_effects": False}
