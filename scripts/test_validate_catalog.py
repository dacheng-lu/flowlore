#!/usr/bin/env python3
"""Test the catalog validator.

Each case builds a throw-away repository (schema, catalog, one document), runs the real
``scripts/validate_catalog.py`` against it and asserts the exit code and the error text.
Testing the CLI instead of an imported function keeps the test honest: it proves the path a
contributor and a CI job actually use.

Usage::

    python3 scripts/test_validate_catalog.py

Exit code 0 when every case passes, 1 otherwise.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = REPO_ROOT / "catalog" / "schema.json"
VALIDATOR = REPO_ROOT / "scripts" / "validate_catalog.py"

BASE_ENTRY = {
    "id": "n8n-docs",
    "type": "source",
    "title": "n8n documentation",
    "summary": "Vendor documentation used as the primary source for this catalog.",
    "status": "verified",
    "verifiedOn": "2026-11-02",
    "evidence": "Read on 2026-11-02; version 2.46.4.",
    "url": "https://docs.n8n.io",
    "tags": ["documentation"],
}

DOC_ENTRY = {
    "id": "sample-doc",
    "type": "doc",
    "title": "Sample document",
    "summary": "A document that exists on disk and is referenced by the catalog.",
    "status": "draft",
    "path": "docs/sample.md",
    "tags": ["sample"],
}


def build(directory: Path, entries: list[dict], reviewed: str = "2026-11-03") -> Path:
    (directory / "catalog").mkdir(parents=True)
    (directory / "scripts").mkdir()
    (directory / "docs").mkdir()
    shutil.copy2(SCHEMA, directory / "catalog" / "schema.json")
    shutil.copy2(VALIDATOR, directory / "scripts" / "validate_catalog.py")
    (directory / "docs" / "sample.md").write_text("# Sample\n", encoding="utf-8")
    catalog = {"catalogVersion": "0.2", "reviewed": reviewed, "entries": entries}
    (directory / "catalog" / "catalog.json").write_text(
        json.dumps(catalog, indent=2), encoding="utf-8"
    )
    return directory / "scripts" / "validate_catalog.py"


def run(script: Path) -> tuple[int, str]:
    completed = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=str(script.parent.parent),
    )
    return completed.returncode, completed.stdout + completed.stderr


CASES: list[tuple[str, list[dict], str, int, str]] = [
    (
        "valid minimal catalog",
        [BASE_ENTRY, DOC_ENTRY],
        "2026-11-03",
        0,
        "OK",
    ),
    (
        "missing required field",
        [{k: v for k, v in BASE_ENTRY.items() if k != "tags"}, DOC_ENTRY],
        "2026-11-03",
        1,
        "missing required property 'tags'",
    ),
    (
        "duplicate id",
        [BASE_ENTRY, DOC_ENTRY, dict(DOC_ENTRY)],
        "2026-11-03",
        1,
        "duplicate id",
    ),
    (
        "unknown status",
        [dict(BASE_ENTRY, status="production-ready"), DOC_ENTRY],
        "2026-11-03",
        1,
        "is not one of",
    ),
    (
        "source reference does not exist",
        [BASE_ENTRY, dict(DOC_ENTRY, sources=["nope"])],
        "2026-11-03",
        1,
        "is not in the catalog",
    ),
    (
        "recipe used as a source",
        [
            BASE_ENTRY,
            {
                "id": "some-recipe",
                "type": "recipe",
                "title": "Some recipe",
                "summary": "A recipe entry used elsewhere as if it were a primary source.",
                "status": "draft",
                "path": "docs/sample.md",
                "input": "a",
                "output": "b",
                "tags": ["sample"],
            },
            dict(DOC_ENTRY, sources=["some-recipe"]),
        ],
        "2026-11-03",
        1,
        "expected one of",
    ),
    (
        "field-tested without evidence",
        [
            {
                "id": "field-note",
                "type": "recipe",
                "title": "Field note",
                "summary": "A recipe that claims field evidence but does not provide any.",
                "status": "field-tested",
                "verifiedOn": "2026-11-01",
                "path": "docs/sample.md",
                "input": "a",
                "output": "b",
                "tags": ["sample"],
            }
        ],
        "2026-11-03",
        1,
        "requires 'evidence'",
    ),
    (
        "draft carrying a verified date",
        [dict(DOC_ENTRY, verifiedOn="2026-11-01")],
        "2026-11-03",
        1,
        "must not carry 'verifiedOn'",
    ),
    (
        "verifiedOn later than reviewed",
        [dict(BASE_ENTRY, verifiedOn="2026-12-24"), DOC_ENTRY],
        "2026-11-03",
        1,
        "later than reviewed",
    ),
    (
        "path does not exist",
        [dict(DOC_ENTRY, path="docs/missing.md")],
        "2026-11-03",
        1,
        "does not exist",
    ),
    (
        "external url is not https",
        [dict(BASE_ENTRY, url="http://docs.n8n.io"), DOC_ENTRY],
        "2026-11-03",
        1,
        "does not match pattern",
    ),
    (
        "unknown property",
        [dict(BASE_ENTRY, homepage="https://example.com"), DOC_ENTRY],
        "2026-11-03",
        1,
        "unexpected property",
    ),
    (
        "recipe without output",
        [
            {
                "id": "half-recipe",
                "type": "recipe",
                "title": "Half recipe",
                "summary": "A recipe entry that forgot to declare what it produces.",
                "status": "draft",
                "path": "docs/sample.md",
                "input": "a",
                "tags": ["sample"],
            }
        ],
        "2026-11-03",
        1,
        "recipe requires 'output'",
    ),
    (
        "learning path without lesson count",
        [
            {
                "id": "some-path",
                "type": "learning-path",
                "title": "Some path",
                "summary": "A learning path entry without the number of lessons it covers.",
                "status": "draft",
                "path": "docs/sample.md",
                "tags": ["sample"],
            }
        ],
        "2026-11-03",
        1,
        "learning-path requires 'lessons'",
    ),
    (
        "source without url",
        [
            {
                "id": "bare-source",
                "type": "source",
                "title": "Bare source",
                "summary": "A source entry that points at a repository file instead of a url.",
                "status": "draft",
                "path": "docs/sample.md",
                "tags": ["sample"],
            }
        ],
        "2026-11-03",
        1,
        "requires 'url'",
    ),
    (
        "both url and path",
        [dict(BASE_ENTRY, path="docs/sample.md")],
        "2026-11-03",
        1,
        "exactly one of",
    ),
]


def main() -> int:
    failures = 0
    for index, (name, entries, reviewed, expected_code, expected_text) in enumerate(CASES, 1):
        with tempfile.TemporaryDirectory() as temporary:
            script = build(Path(temporary), entries, reviewed)
            code, output = run(script)
        ok = code == expected_code and expected_text in output
        failures += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'} {index:2d}. {name}")
        if not ok:
            print(f"      expected exit {expected_code} and {expected_text!r}")
            print(f"      got exit {code}:\n{output}")

    # The real catalog must stay valid too.
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR)], capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    ok = completed.returncode == 0
    failures += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'} {len(CASES) + 1:2d}. repository catalog validates")
    if not ok:
        print(completed.stdout + completed.stderr)

    print(f"\n{len(CASES) + 1 - failures}/{len(CASES) + 1} cases passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
