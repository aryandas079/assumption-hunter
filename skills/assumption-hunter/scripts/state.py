"""Shared parser, validation, ranking and comparison for audit snapshots."""

import json
import math
import re
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

MAX_BYTES = 2 * 1024 * 1024
SCHEMA_VERSION = "1.0.0"
ID = re.compile(r"ASM-[0-9]{3,12}")
UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)")
CATEGORIES = {"observed", "inferred", "hypothesis", "preference", "unknown"}
STATUSES = {"untested", "supported", "contradicted", "inconclusive", "not_testable"}
EXECUTION_STATUSES = {"not_run", "passed", "failed", "inconclusive"}
PRIORITY_FIELDS = ("impact", "uncertainty", "test_cost")


class StateError(ValueError):
    """Invalid input or an unsafe snapshot operation."""


def require(condition: bool, location: str, message: str) -> None:
    if not condition:
        raise StateError(f"{location}: {message}")


def unique_keys(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(items)
    require(len(result) == len(items), "JSON", "duplicate object key")
    return result


def finite_float(value: str) -> float:
    number = float(value)
    require(math.isfinite(number), "JSON", "numbers must be finite")
    return number


def parse_snapshot(raw: str | bytes) -> dict[str, Any]:
    try:
        raw = raw.encode("utf-8") if isinstance(raw, str) else raw
        require(len(raw) <= MAX_BYTES, "JSON", f"exceeds {MAX_BYTES} bytes")
        snapshot = json.loads(
            raw.decode("utf-8-sig"),
            object_pairs_hook=unique_keys,
            parse_float=finite_float,
            parse_constant=finite_float,
        )
    except json.JSONDecodeError as error:
        raise StateError(f"JSON: {error.msg} at line {error.lineno}, column {error.colno}") from None
    except UnicodeError:
        raise StateError("JSON: expected UTF-8 text") from None
    except (RecursionError, ValueError) as error:
        if isinstance(error, StateError):
            raise
        raise StateError("JSON: nesting or integer size exceeds the parser limit") from None
    validate_snapshot(snapshot)
    return snapshot


def load_snapshot(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return parse_snapshot(stream.read(MAX_BYTES + 1))


def member(obj: dict[str, Any], key: str, location: str) -> Any:
    require(key in obj, f"{location}.{key}", "required field is missing")
    return obj[key]


def required_text(value: Any, location: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), location, "expected non-empty text")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise StateError(f"{location}: expected valid Unicode") from None


def timestamp(value: Any, location: str) -> datetime:
    require(isinstance(value, str) and UTC.fullmatch(value) is not None, location,
            "expected an ISO 8601 UTC timestamp ending in Z or +00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise StateError(f"{location}: invalid calendar date or time") from None


def enum(value: Any, options: set[str], location: str) -> None:
    require(isinstance(value, str) and value in options, location,
            f"expected one of {', '.join(sorted(options))}")


def object_list(obj: dict[str, Any], key: str, location: str):
    items = member(obj, key, location)
    require(isinstance(items, list), f"{location}.{key}", "expected an array")
    for index, item in enumerate(items):
        item_location = f"{location}.{key}[{index}]"
        require(isinstance(item, dict), item_location, "expected an object")
        yield item, item_location


def validate_source(source: dict[str, Any], location: str) -> None:
    path = member(source, "path", location)
    required_text(path, f"{location}.path")
    require(
        not any(part in {"", ".", ".."} for part in path.split("/"))
        and not any(character in path for character in ':\\<>"|?*')
        and not any(ord(character) < 32 or ord(character) == 127 for character in path),
        f"{location}.path",
        "expected a project-relative path using / with no traversal",
    )
    start = member(source, "line_start", location)
    end = member(source, "line_end", location)
    require(type(start) is int and type(end) is int and 1 <= start <= end,
            location, "expected positive integer lines with line_start <= line_end")


def validate_evidence(evidence: dict[str, Any], location: str) -> None:
    enum(member(evidence, "kind", location), {"support", "contradict"}, f"{location}.kind")
    for key in ("source", "summary", "verified_by"):
        value = member(evidence, key, location)
        if value is not None or key == "summary":
            required_text(value, f"{location}.{key}")
    observed_at = member(evidence, "observed_at", location)
    if observed_at is not None:
        timestamp(observed_at, f"{location}.observed_at")


def validate_test(test: Any, location: str) -> None:
    require(isinstance(test, dict), location, "expected an object")
    for key in ("procedure", "failure_criterion", "prerequisites"):
        required_text(member(test, key, location), f"{location}.{key}")
    for key in ("expected_observation", "estimated_effort"):
        if key in test:
            required_text(test[key], f"{location}.{key}")
    enum(member(test, "execution_status", location), EXECUTION_STATUSES,
         f"{location}.execution_status")


def validate_assumption(assumption: dict[str, Any], location: str) -> None:
    for key in ("statement", "mitigation"):
        required_text(member(assumption, key, location), f"{location}.{key}")
    for key in ("last_changed_reason", "consequence"):
        if assumption.get(key) is not None:
            required_text(assumption[key], f"{location}.{key}")
    enum(member(assumption, "category", location), CATEGORIES, f"{location}.category")
    enum(member(assumption, "status", location), STATUSES, f"{location}.status")
    for key in PRIORITY_FIELDS:
        value = member(assumption, key, location)
        require(type(value) is int and 1 <= value <= 5, f"{location}.{key}",
                "expected an integer from 1 to 5")
    for source, source_location in object_list(assumption, "source_locations", location):
        validate_source(source, source_location)
    for evidence, evidence_location in object_list(assumption, "evidence", location):
        validate_evidence(evidence, evidence_location)
    test = member(assumption, "falsification_test", location)
    if test is not None or assumption["status"] != "not_testable":
        validate_test(test, f"{location}.falsification_test")


def validate_snapshot(snapshot: Any) -> None:
    require(isinstance(snapshot, dict), "$", "expected an object")
    require(member(snapshot, "schema_version", "$") == SCHEMA_VERSION,
            "$.schema_version", f"expected schema version {SCHEMA_VERSION}")
    required_text(member(snapshot, "project_id", "$"), "$.project_id")
    timestamp(member(snapshot, "audited_at", "$"), "$.audited_at")
    seen = set()
    for assumption, location in object_list(snapshot, "assumptions", "$"):
        identifier = member(assumption, "id", location)
        require(isinstance(identifier, str) and ID.fullmatch(identifier) is not None,
                f"{location}.id", "expected ASM- followed by 3 to 12 digits")
        require(identifier not in seen, f"{location}.id", "duplicate assumption ID")
        seen.add(identifier)
        validate_assumption(assumption, location)


def score(assumption: dict[str, Any]) -> Fraction:
    return Fraction(assumption["impact"] * assumption["uncertainty"], assumption["test_cost"])


def priority(assumption: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: assumption[key] for key in PRIORITY_FIELDS},
        "score": round(float(score(assumption)), 4),
        "critical_unresolved": (
            assumption["impact"] == 5 and assumption["status"] in {"untested", "inconclusive"}
        ),
    }


def sort_key(assumption: dict[str, Any]) -> tuple:
    return (
        not priority(assumption)["critical_unresolved"],
        -score(assumption),
        -assumption["impact"],
        -assumption["uncertainty"],
        assumption["id"],
    )


def rank_assumptions(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": assumption["id"], "status": assumption["status"], **priority(assumption)}
        for assumption in sorted(snapshot["assumptions"], key=sort_key)
    ]


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def change_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    fields = []
    for field in sorted(before.keys() | after.keys()):
        if field == "last_changed_reason":
            continue
        old = before.get(field)
        new = after.get(field)
        if field in {"evidence", "source_locations"}:
            changed = sorted(map(canonical, old)) != sorted(map(canonical, new))
        else:
            changed = field not in before or field not in after or canonical(old) != canonical(new)
        if changed:
            fields.append(field)
    return fields


def compare_snapshots(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    require(old["project_id"] == new["project_id"], "$.project_id", "snapshots describe different projects")
    before = {item["id"]: item for item in old["assumptions"]}
    after = {item["id"]: item for item in new["assumptions"]}
    result = {
        "added": sorted(after.keys() - before.keys()),
        "retired": sorted(before.keys() - after.keys()),
        "statement_changed": [],
        "status_changed": [],
        "evidence_changed": [],
        "priority_changed": [],
        "changes": [],
    }
    for identifier in sorted(before.keys() & after.keys()):
        previous = before[identifier]
        current = after[identifier]
        fields = change_fields(previous, current)
        if not fields:
            continue
        entry = {"id": identifier, "fields": fields, "reason": None}
        reason = current.get("last_changed_reason")
        if reason != previous.get("last_changed_reason"):
            entry["reason"] = reason
        for field in ("statement", "evidence", "status"):
            if field in fields:
                result[f"{field}_changed"].append(identifier)
        if "status" in fields:
            entry["status"] = {"before": previous["status"], "after": current["status"]}
        old_priority, new_priority = priority(previous), priority(current)
        if old_priority != new_priority:
            entry["priority"] = {"before": old_priority, "after": new_priority}
            result["priority_changed"].append(identifier)
        result["changes"].append(entry)
    return result
