# Catalog

`catalog/catalog.json` is the machine-readable form of this repository: every source, skill,
document and recipe with a stable id, a status and its provenance. Humans read the Markdown;
agents and tooling read the JSON. The two must agree — where they disagree, the JSON is the
bug.

**Status:** catalog `0.2`, reviewed 2026-11-03. Validated by
`scripts/validate_catalog.py` against `catalog/schema.json`; the validator's own rules are
covered by `scripts/test_validate_catalog.py`.

## Why a second representation

- **Search by intent, platform and verification state** without parsing Markdown headings.
- **Link entries to their sources**, so a recipe never claims more than the source behind it.
- **Make status a field, not a claim in prose.** "Draft" in a sentence is easy to forget;
  `"status": "draft"` in a validated file is not.
- **Break the build on drift.** A recipe that points at a file which no longer exists fails
  the validator, so the catalog cannot rot silently.

## Status vocabulary

Three values, used for every entry type. They describe **the evidence behind the entry**, not
how useful it looks.

| Status | Meaning | Requirements |
| --- | --- | --- |
| `draft` | Design or text only. Nobody has executed it. | — |
| `field-tested` | Exercised on at least one real instance or workflow. | `verifiedOn` + `evidence` |
| `verified` | Reproducible from pinned versions in an isolated environment, with published evidence. | `verifiedOn` + `evidence` that names the reproducible artifact |

`field-tested` is deliberately **not** a synonym for "verified". Evidence for this state is a
summary ("ran on `2.41.7` while changing a billing workflow; rollback path not exercised"),
because the instance, data and credentials cannot be published. That is weaker than a
reproducible test — and the status says so.

## Entry types

| Type | Points at | Extra fields |
| --- | --- | --- |
| `source` | An upstream project or documentation site | `url` |
| `skill` | An external agent skill (`SKILL.md`) | `url`, optional `reviewedBlob` |
| `recipe` | A recipe in [recipes/README.md](../recipes/README.md) | `input`, `output`, `sources` |
| `doc` | A document in this repository | `path` |
| `learning-path` | A curriculum or learning path in this repository | `path`, `lessons` |

Every entry has exactly one location: `url` (external, `https://` only) or `path` (relative to
the repository root). Both is an error, neither is an error.

## Validate

```bash
python3 scripts/validate_catalog.py                 # schema + referential integrity
python3 scripts/validate_catalog.py --links         # additionally check external URLs (network)
python3 scripts/validate_catalog.py --json          # machine-readable result
python3 scripts/test_validate_catalog.py            # test the validator itself
```

The script exits `0` when the catalog is valid, `1` when a rule is violated, `2` on a usage or
parse error. It needs Python 3.9+ and the standard library only — no `pip install`, so it can
run in any CI without a dependency step.

Checks, in order:

| Rule | What it enforces |
| --- | --- |
| schema | Types, required fields, enums, patterns, `additionalProperties: false` (see `catalog/schema.json`) |
| `id` uniqueness | Two entries with one id make references ambiguous |
| exactly one of `url`/`path` | See above |
| path exists | A `path` must resolve to a file inside the repository |
| sources resolve | Each id in `sources` must exist and be one of `source`, `skill`, `doc`, `learning-path`; self-reference is rejected |
| status coupling | `field-tested`/`verified` require `verifiedOn` + `evidence`; `draft` must not claim `verifiedOn` |
| type coupling | `recipe` needs `input`/`output`; `learning-path` needs `lessons`; `source`/`skill` need `url` |
| date sanity | `verifiedOn` must not be later than the catalog's `reviewed` date |
| tags | Lowercase kebab-case, unique per entry |

`--links` adds a reachability check. It reports `403`/`429` as warnings, not failures: bot
walls and rate limits say nothing about whether a source is real.

## Add an entry

1. Write the thing first (a doc, a recipe row) — the catalog describes what exists.
2. Add the entry to `catalog/catalog.json` with a new kebab-case id.
3. Set the status to what you can defend. New entries are `draft` unless someone executed
   them.
4. Point `sources` at the entries the work is based on. A recipe with no source is an
   opinion.
5. Run `python3 scripts/validate_catalog.py` and commit only when it exits `0`.
6. If the entry changes a count or a table in the README, update the README in **all three
   languages**.

## Versioning

`catalogVersion` follows the repository's own pace, not semver of a product: bump the minor
number when entries are added or a status changes, the major number when the schema breaks.
The schema is additive where possible; a new field is optional and gets a default in the
validator, so old catalogs keep validating.
