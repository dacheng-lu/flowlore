#!/usr/bin/env python3
"""Validate the FlowLore catalog.

Two layers:

1. Schema conformance against ``catalog/schema.json`` using a small validator for the
   subset of JSON Schema the schema actually uses (no third-party dependency, so this runs
   in any CI without an install step).
2. Semantic rules that a schema cannot express: unique ids, resolvable sources, existing
   paths, status/evidence coupling and type-specific fields.

Usage::

    python3 scripts/validate_catalog.py                 # schema + semantics
    python3 scripts/validate_catalog.py --links         # + reachability of external urls
    python3 scripts/validate_catalog.py --json          # machine-readable output

Exit codes: 0 valid, 1 rule violated, 2 usage or parse error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "catalog" / "catalog.json"
SCHEMA = REPO_ROOT / "catalog" / "schema.json"

SOURCE_TYPES = {"source", "skill", "doc", "learning-path"}
STATUS_WITH_EVIDENCE = {"field-tested", "verified"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# --------------------------------------------------------------------------- schema


class SchemaError(Exception):
    """Raised when the schema itself uses a keyword this validator does not implement."""


def _resolve_ref(ref: str, root: dict) -> dict:
    if not ref.startswith("#/"):
        raise SchemaError(f"unsupported $ref {ref!r}; only local references are supported")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise SchemaError(f"unsupported type {expected!r}")


def _is_date(value: str) -> bool:
    if not DATE_RE.match(value):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_schema(value: Any, schema: dict, root: dict, where: str = "$") -> list[str]:
    """Validate ``value`` against the JSON Schema subset used by catalog/schema.json."""
    errors: list[str] = []

    if "$ref" in schema:
        return validate_schema(value, _resolve_ref(schema["$ref"], root), root, where)

    expected = schema.get("type")
    if expected and not _type_matches(value, expected):
        return [f"{where}: expected {expected}, got {type(value).__name__}"]

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {value!r} is not one of {schema['enum']}")

    if "const" in schema and value != schema["const"]:
        errors.append(f"{where}: expected constant {schema['const']!r}")

    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{where}: {value!r} does not match pattern {schema['pattern']!r}")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{where}: shorter than {schema['minLength']} characters")
        if schema.get("format") == "date" and not _is_date(value):
            errors.append(f"{where}: {value!r} is not an ISO date (YYYY-MM-DD)")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{where}: {value} is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{where}: {value} is above maximum {schema['maximum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{where}: fewer than {schema['minItems']} items")
        if schema.get("uniqueItems"):
            seen = [json.dumps(item, sort_keys=True) for item in value]
            duplicates = {item for item in seen if seen.count(item) > 1}
            for duplicate in sorted(duplicates):
                errors.append(f"{where}: duplicate item {duplicate}")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, item_schema, root, f"{where}[{index}]"))

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{where}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{where}: unexpected property {key!r}")
        for key, sub_schema in properties.items():
            if key in value:
                errors.extend(validate_schema(value[key], sub_schema, root, f"{where}.{key}"))

    for keyword in ("anyOf", "oneOf", "allOf"):
        if keyword not in schema:
            continue
        branches = schema[keyword]
        branch_results = [
            validate_schema(value, branch, root, where) for branch in branches
        ]
        passing = sum(1 for result in branch_results if not result)
        if keyword == "anyOf" and passing == 0:
            errors.append(f"{where}: matches none of the allowed shapes")
        if keyword == "oneOf" and passing != 1:
            errors.append(f"{where}: matches {passing} of the allowed shapes, expected exactly 1")
        if keyword == "allOf":
            for result in branch_results:
                errors.extend(result)

    return errors


# ----------------------------------------------------------------------- semantics


def validate_semantics(catalog: dict) -> list[str]:
    errors: list[str] = []
    entries = catalog["entries"]
    reviewed = catalog["reviewed"]

    ids: dict[str, dict] = {}
    for index, entry in enumerate(entries):
        entry_id = entry["id"]
        if entry_id in ids:
            errors.append(f"entries[{index}]: duplicate id {entry_id!r}")
        ids[entry_id] = entry

    for entry in entries:
        entry_id = entry["id"]
        has_url, has_path = "url" in entry, "path" in entry
        if has_url == has_path:
            errors.append(f"{entry_id}: exactly one of 'url' or 'path' is required")

        if has_path:
            relative = entry["path"]
            target = (REPO_ROOT / relative).resolve()
            if not str(target).startswith(str(REPO_ROOT)):
                errors.append(f"{entry_id}: path {relative!r} escapes the repository")
            elif not target.is_file():
                errors.append(f"{entry_id}: path {relative!r} does not exist")

        for source_id in entry.get("sources", []):
            if source_id == entry_id:
                errors.append(f"{entry_id}: references itself as a source")
                continue
            target = ids.get(source_id)
            if target is None:
                errors.append(f"{entry_id}: source {source_id!r} is not in the catalog")
            elif target["type"] not in SOURCE_TYPES:
                errors.append(
                    f"{entry_id}: source {source_id!r} has type {target['type']!r}, "
                    f"expected one of {sorted(SOURCE_TYPES)}"
                )

        status = entry["status"]
        if status in STATUS_WITH_EVIDENCE:
            for field in ("verifiedOn", "evidence"):
                if field not in entry:
                    errors.append(f"{entry_id}: status {status!r} requires {field!r}")
        elif "verifiedOn" in entry:
            errors.append(f"{entry_id}: status {status!r} must not carry 'verifiedOn'")

        if "verifiedOn" in entry:
            verified_on = entry["verifiedOn"]
            if _is_date(verified_on) and _is_date(reviewed) and verified_on > reviewed:
                errors.append(
                    f"{entry_id}: verifiedOn {verified_on} is later than reviewed {reviewed}"
                )

        entry_type = entry["type"]
        if entry_type == "recipe":
            for field in ("input", "output"):
                if field not in entry:
                    errors.append(f"{entry_id}: recipe requires {field!r}")
        if entry_type == "learning-path" and "lessons" not in entry:
            errors.append(f"{entry_id}: learning-path requires 'lessons'")
        if entry_type in {"source", "skill"} and "url" not in entry:
            errors.append(f"{entry_id}: type {entry_type!r} requires 'url'")

    return errors


# -------------------------------------------------------------------------- links


def check_links(catalog: dict, timeout: float = 10.0) -> tuple[list[str], list[str]]:
    """Return (failures, warnings) for external urls. 403/429 are warnings, not failures."""
    failures: list[str] = []
    warnings: list[str] = []
    for entry in catalog["entries"]:
        url = entry.get("url")
        if not url:
            continue
        request = Request(url, method="GET", headers={"User-Agent": "flowlore-catalog-check"})
        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status >= 400:
                    failures.append(f"{entry['id']}: {url} answered {response.status}")
        except HTTPError as error:
            if error.code in (401, 403, 429):
                warnings.append(f"{entry['id']}: {url} answered {error.code} (bot wall or rate limit)")
            else:
                failures.append(f"{entry['id']}: {url} answered {error.code}")
        except (URLError, TimeoutError) as error:
            failures.append(f"{entry['id']}: {url} unreachable ({error})")
    return failures, warnings


# ---------------------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the FlowLore catalog.")
    parser.add_argument("--links", action="store_true", help="also check external urls")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: cannot read catalog or schema: {error}", file=sys.stderr)
        return 2

    try:
        errors = validate_schema(catalog, schema, schema)
        errors += validate_semantics(catalog)
    except SchemaError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    warnings: list[str] = []
    if args.links:
        link_failures, warnings = check_links(catalog)
        errors += link_failures

    entries = catalog["entries"]
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1

    if args.json:
        print(
            json.dumps(
                {
                    "valid": not errors,
                    "entries": len(entries),
                    "byStatus": counts,
                    "errors": errors,
                    "warnings": warnings,
                },
                indent=2,
            )
        )
    else:
        for warning in warnings:
            print(f"warning: {warning}")
        for error in errors:
            print(f"error: {error}")
        if errors:
            print(f"\nINVALID — {len(errors)} problem(s) in {len(entries)} entries")
        else:
            summary = ", ".join(f"{count} {status}" for status, count in sorted(counts.items()))
            print(f"OK — {len(entries)} entries valid ({summary})")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
