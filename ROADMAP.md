# FlowLore roadmap / 流谱路线图

Status: proposed direction, not a release commitment. / 状态：待实施方向，不是发布承诺。 / Stand: vorgeschlagene Richtung, keine Release-Zusage.

Reviewed: 2026-11-08, against `main`. Catalog version **0.4**.

This page is in English, like the operating documents; the README is trilingual. Nothing here has a date, and a "Candidate" item is not decided.

The roadmap answers one question: what turns this catalog from a reading list into something a reader can trust and reuse? The order below is the proposal.

## Released

- **0.4** (2026-11-08): Kelly theory reference and recovery-budget experiment draft; 44 entries, **0 of 17 recipes verified**.
- **0.3** (2026-11-08): six pinned agent-ecosystem sources, three draft design references, one joint-audit draft and three [design recipes](recipes/design-workflows.md); 42 entries, **0 of 16 recipes verified**. The offline cross-project fixture does not establish real audit effectiveness.

- **0.2** (2026-11-03): the catalog became machine-readable and partly checkable: [`catalog/catalog.json`](catalog/catalog.json) with a schema, a validator and its tests (29 entries), the [n8n operations chapter](docs/n8n/OPERATIONS.md) (API surface, publishing model, safe changes, execution diagnosis), [failure modes](docs/n8n/FAILURE-MODES.md) and a [version matrix](docs/n8n/VERSION-MATRIX.md), a [30-lesson learning path](docs/learning-paths/ihk-ki-automatisierung.md), a [three-project release-digest example](examples/release-digest/README.md), a [value-experiment template](docs/VALUE-EXPERIMENT.md) and clarified entry points. `catalogVersion` is 0.2. **0 of 12 recipes are verified.**
- **0.1** (2026-11-02): first catalog draft — five automation sources, five web/HTML skill references, the first recipe designs, the boundaries between FlowLore, Longhaul and Makeextreme, a trilingual README and the logo.

No tags and no GitHub Releases exist.

## Owed

### P0 — the next three steps, in this order

- [ ] **Verify the first recipe end to end.** The GitHub release digest needs no private infrastructure. Pin the engine version, write the test input and the expected output, run it in an isolated environment, publish the artifact (export and command output) under `examples/release-digest/evidence/`, then change its status from `draft` to `verified` in [recipes/README.md](recipes/README.md). Acceptance: a fresh clone reproduces the published output with one documented command, and the README's "0 of 17" becomes "1 of 17".
  A bounded, read-only public API experiment and the three-project snapshot demonstration are in
  [the example](examples/release-digest/README.md). A partial live sample does not satisfy the
  verified-recipe criteria. Offline CI exercises pinned and current peer revisions separately;
  the network job is non-blocking and may fail for upstream reasons.
- [ ] **Add a recipe contract and validator.** Today a recipe is prose in [recipes/README.md](recipes/README.md); nothing checks that a `verified` label has evidence behind it. Define the fields (id, intent, inputs, outputs, engines, source revisions, status, evidence path), add `scripts/validate_recipes.py` with tests, and run it in CI. Acceptance: all seventeen recipes validate, and a `verified` recipe without an existing evidence file fails with the recipe id.
- [x] **Check links and versions in CI.** Every external source is a reference, not a tested dependency, and links rot. Add a check that every URL answers (with an explicit allowlist for bot walls) and that every n8n claim carries the version it was read on. Acceptance: one deliberately broken URL fails CI and names the file and the URL.

### P1 — after the first recipe is verified

- [ ] **Search by intent, platform, dependencies and status.** Generate a static index from `catalog.json`; a query returns entries and their evidence state. No server. Acceptance: ten recorded sample queries return the expected entries.
- [ ] **Watch upstream changes.** Read releases and commits for the five sources and open a review queue when a pinned revision moves. Never edit the catalog automatically. Acceptance: one dry run against pinned revisions produces a review list, not a write.
- [ ] **Give every recipe the same page.** Input, output, dependencies, validation, evidence and failure path — the four field-tested operations recipes already show the shape; the drafts do not. Acceptance: all seventeen have every section, and an empty section says "not yet tested" instead of being omitted.

### P2 — only if the earlier steps hold

- [ ] **Evaluate a read-only agent interface.** A CLI or MCP server that can query the catalog and read recipes, with no write scope and no execution. Acceptance: an agent answers three catalog questions using only that interface, and the interface has no write path.

## Blocked

- **License.** The README says "License not yet specified". Until the owner chooses one, the terms for reuse and contribution are undefined. A [scope review and Apache-2.0 candidate](docs/proposals/license-choice.md) are ready for that decision; neither activates a license. Third-party course labels and branding need separate treatment.
- **Publishing the field-tested evidence.** Four recipes rest on private n8n instances and customer data. Their evidence can only be a dated summary; publishing more needs a redaction policy and the owner's approval.
- **Compatibility claims beyond the recorded versions.** The n8n field notes cover specific versions (`2.27.5`–`2.46.4` at review time). Testing another version needs an instance the repository does not have.

## Candidate (not decided)

- Bundle an n8n workflow JSON per recipe, exported from the pinned version.
- A generated GitHub Pages site over `catalog.json`.
- A German or English edition of the 30-lesson learning path.
- Evaluate Huginn and Activepieces as second engines, not only as references.
- A recipe for the questions that keep recurring in the value experiment.
- **A next major version: capabilities in the catalog and a read-only query surface.** Proposed, not decided, not scheduled; design only. [docs/proposals/trust-substrate-2.0.md](docs/proposals/trust-substrate-2.0.md) adds per-recipe capabilities, effect classes, an untrusted-by-default rule for fetched web content, and an MCP resource with no write path. The shared exchange format is drafted in [docs/proposals/trio-trust-contract-v0.md](docs/proposals/trio-trust-contract-v0.md) and is not frozen until one real release-digest run passes.

## Not planned

- Bundling, hosting or operating n8n, Huginn or Activepieces.
- Executing a reader's automations, storing credentials, or any autonomous write access.
- A marketplace, a star ranking or a "best tool" claim.
- Importing third-party templates without a license review.

## How this page stays true

[`scripts/test_roadmap.py`](scripts/test_roadmap.py) checks that these sections exist in order, that `catalogVersion` is the newest released version, that the README links here, and that every relative link points at a file that exists. It runs in CI.
