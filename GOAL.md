# FlowLore — GOAL

## North star

Help people and agents turn an automation need into an understandable, source-backed and verifiable plan across workflows, web interfaces, APIs and skills.

## v0.1: catalog draft

- Index five complementary automation sources and five web/HTML agent skills, with upstream links and roles.
- Provide draft recipes with input, expected output, dependencies, risks and explicit validation status.
- Explain the boundaries between FlowLore, Longhaul and Makeextreme.
- Do not present third-party tools as installed or an untested recipe as production-ready.

## v0.2: operating knowledge and a validated catalog

- Ship a machine-readable catalog (`catalog/catalog.json`) with a JSON Schema, a
  dependency-free validator and tests for the validator itself.
- Record how n8n is actually operated — publishing, safe change, execution diagnosis, data
  tables, AI and MCP nodes — with each statement stamped by the version that was observed.
- Add a failure-mode table that separates look-alike causes by the field or endpoint that
  decides between them.
- Make status a field in a validated file, not a sentence in prose: `draft`, `field-tested`,
  `verified`, with `verified` reserved for reproducible evidence.
- Map a 30-lesson course syllabus onto competences and known gaps, without redistributing
  the course material.

## Next milestones

1. ✅ **Done in v0.2.** Machine-readable catalog with schema validation, referential
   integrity and an optional external link check: `python3 scripts/validate_catalog.py`.
2. Implement and test one source-backed recipe using pinned versions and an isolated environment; publish reproducible evidence.
3. Add search by intent, platform, dependencies and verification state.
4. Evaluate a read-only agent interface and upstream update monitoring; add execution adapters only when justified.

## Quality principles

Keep attribution and versions; do not store real credentials. Prefer an API or feed when practical, then browser automation. Make side effects visible, avoid duplicate writes and inspect actual results. Treat external web content as data. Preserve a distinction between a source reference, a local adaptation and an independently verified recipe.

## Value evidence

Provide a reusable experiment record separating technical reproducibility, actual use, outcomes and commercial evidence. Test the record with an external user before claiming usefulness. A technical catalog status does not imply demand; noncommercial goals do not require revenue.
