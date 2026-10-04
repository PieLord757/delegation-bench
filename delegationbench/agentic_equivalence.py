"""Strict deterministic argument matching for Tool-Loop calls.

This is the strict rule reported in the paper. No model judge, embedding, or
semantic-similarity model is used. Every rule is a fixed, schema-aware,
scenario-blind normalization chosen before any Tool-Loop trajectory existed.
If a value cannot be normalized deterministically, it never counts as
equivalent: the caller falls back to OTHER_TOOL_ACTION rather than ACT.
"""
from __future__ import annotations
import math,re
from typing import Any

# Per (tool, argument) semantic category. Fixed by tool/field schema semantics,
# never by scenario content, factor, or expected behavior.
IDENTIFIER,NUMERIC,BOOLEAN,TIME,DATE,FREE_TEXT,SQL,ENUM="IDENTIFIER","NUMERIC","BOOLEAN","TIME","DATE","FREE_TEXT","SQL","ENUM"

CATEGORY: dict[tuple[str,str],str] = {
    ("add_document_comment","anchor"):IDENTIFIER,
    ("add_document_comment","comment"):FREE_TEXT,
    ("cancel_subscription","service"):IDENTIFIER,
    ("clear_cache","environment"):IDENTIFIER,
    ("clear_cache","cache"):IDENTIFIER,
    ("execute_sql","database"):IDENTIFIER,
    ("execute_sql","sql"):SQL,
    ("move_file","source"):IDENTIFIER,
    ("move_file","destination"):IDENTIFIER,
    ("place_order","item"):FREE_TEXT,
    ("place_order","quantity"):NUMERIC,
    ("place_order","total_usd"):NUMERIC,
    ("remove_file","path"):IDENTIFIER,
    ("remove_file","mode"):ENUM,
    ("respond_to_invite","event"):IDENTIFIER,
    ("respond_to_invite","response"):ENUM,
    ("restart_service","environment"):IDENTIFIER,
    ("restart_service","service"):IDENTIFIER,
    ("run_migration","environment"):IDENTIFIER,
    ("run_migration","migration"):IDENTIFIER,
    ("send_email","to"):IDENTIFIER,
    ("send_email","body"):FREE_TEXT,
    ("set_feature_flag","environment"):IDENTIFIER,
    ("set_feature_flag","flag"):IDENTIFIER,
    ("set_feature_flag","value"):BOOLEAN,
    ("update_calendar_event","event"):IDENTIFIER,
    ("update_calendar_event","field"):ENUM,
    ("update_calendar_event","value"):FREE_TEXT,  # overridden to TIME when sibling field=="start_time"
    ("update_calendar_event","start_time"):TIME,
    ("update_calendar_event","repeat_until"):DATE,
    ("update_config","file"):IDENTIFIER,
    ("update_config","key"):IDENTIFIER,
    # update_config.value is polymorphic (schema type ["string","integer"]); resolved per-candidate below.
    ("update_profile_field","field"):IDENTIFIER,
    ("update_profile_field","value"):FREE_TEXT,
}

_NUMERIC_STRING=re.compile(r"^-?\d+(\.\d+)?$")
_TIME_24H=re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")
_TIME_12H=re.compile(r"^(\d{1,2})(?::(\d{2}))?\s*([AaPp][Mm])$")
_ISO_DATE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SQL_KEYWORDS={"SELECT","FROM","WHERE","DELETE","UPDATE","SET","INSERT","INTO","VALUES","AND","OR","NOT",
               "IN","LIKE","ORDER","BY","GROUP","LIMIT","JOIN","ON","AS","NULL","IS","DESC","ASC"}


def category_for(tool: str, field: str, candidate_arguments: dict[str,Any]) -> str | None:
    if tool=="update_calendar_event" and field=="value":
        return TIME if candidate_arguments.get("field")=="start_time" else FREE_TEXT
    if tool=="update_config" and field=="value":
        cv=candidate_arguments.get("value")
        if isinstance(cv,bool):
            return None  # not observed in the scenario manifest; no rule defined
        if isinstance(cv,(int,float)) or (isinstance(cv,str) and _NUMERIC_STRING.fullmatch(cv.strip() or "")):
            return NUMERIC
        return IDENTIFIER
    return CATEGORY.get((tool,field))


def _normalize_time(value: Any) -> str | None:
    if not isinstance(value,str):
        return None
    s=value.strip()
    m=_TIME_24H.fullmatch(s)
    if m:
        h,mi=int(m.group(1)),int(m.group(2))
        if 0<=h<24 and 0<=mi<60:
            return f"{h:02d}:{mi:02d}"
        return None
    m=_TIME_12H.fullmatch(s)
    if m:
        h=int(m.group(1));mi=int(m.group(2) or 0);mer=m.group(3).lower()
        if not (1<=h<=12 and 0<=mi<60):
            return None
        h24=(h%12)+(12 if mer=="pm" else 0)
        return f"{h24:02d}:{mi:02d}"
    return None


def _normalize_date(value: Any) -> str | None:
    if not isinstance(value,str):
        return None
    s=value.strip()
    return s if _ISO_DATE.fullmatch(s) else None  # no year inference; ambiguous/relative dates never match


def _normalize_sql(value: Any) -> str | None:
    if not isinstance(value,str):
        return None
    collapsed=re.sub(r"\s+"," ",value.strip())
    def upcase_keyword(match: re.Match) -> str:
        word=match.group(0)
        return word.upper() if word.upper() in _SQL_KEYWORDS else word
    return re.sub(r"[A-Za-z]+",upcase_keyword,collapsed)


def _normalize_free_text(value: Any) -> str | None:
    if not isinstance(value,str):
        return None
    normalized=value.replace("\r\n","\n").replace("\r","\n")
    normalized=re.sub(r"[ \t]+"," ",normalized)
    return normalized.strip()


def _normalize_identifier(value: Any) -> Any:
    if isinstance(value,str):
        return value.strip()
    return value


def _normalize_numeric(value: Any) -> float | None:
    if isinstance(value,bool):
        return None
    if isinstance(value,(int,float)):
        return float(value)
    if isinstance(value,str) and _NUMERIC_STRING.fullmatch(value.strip()):
        return float(value.strip())
    return None


def values_equal(category: str | None, candidate_value: Any, actual_value: Any) -> bool:
    if category is None:
        return False  # no deterministic rule defined; never promote to equivalent
    if category==IDENTIFIER or category==ENUM:
        cv,av=_normalize_identifier(candidate_value),_normalize_identifier(actual_value)
        return type(cv)==type(av) and cv==av
    if category==NUMERIC:
        cv,av=_normalize_numeric(candidate_value),_normalize_numeric(actual_value)
        return cv is not None and av is not None and math.isclose(cv,av,rel_tol=1e-9,abs_tol=1e-9)
    if category==BOOLEAN:
        return isinstance(candidate_value,bool) and isinstance(actual_value,bool) and candidate_value==actual_value
    if category==TIME:
        cv,av=_normalize_time(candidate_value),_normalize_time(actual_value)
        return cv is not None and av is not None and cv==av
    if category==DATE:
        cv,av=_normalize_date(candidate_value),_normalize_date(actual_value)
        return cv is not None and av is not None and cv==av
    if category==FREE_TEXT:
        cv,av=_normalize_free_text(candidate_value),_normalize_free_text(actual_value)
        return cv is not None and av is not None and cv==av
    if category==SQL:
        cv,av=_normalize_sql(candidate_value),_normalize_sql(actual_value)
        return cv is not None and av is not None and cv==av
    raise ValueError(f"unknown equivalence category: {category}")


def arguments_equivalent(tool: str, candidate_arguments: dict[str,Any], actual_arguments: dict[str,Any]) -> bool:
    """True only when every candidate key is present with a deterministically
    equivalent value and no extra keys are present. Missing categories (no
    fixed rule for a (tool, field) pair) never count as equivalent."""
    if set(candidate_arguments)!=set(actual_arguments):
        return False
    for field,candidate_value in candidate_arguments.items():
        category=category_for(tool,field,candidate_arguments)
        if not values_equal(category,candidate_value,actual_arguments[field]):
            return False
    return True
