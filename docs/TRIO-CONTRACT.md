# Candidate three-project evidence card

Status: **proposed, not a cross-project standard or automatic adapter**. The offline
[release digest example](../examples/release-digest/README.md) emits a small local card
labelled `trio-evidence-example/0.1`. Its fields are intended for discussion and inspection;
no project should consume it as authoritative evidence without its own validation.

| Field | Meaning and limitation |
| --- | --- |
| `schema` | Identifies this illustrative example; incompatible or missing versions are unknown. |
| `task`, `recipe` | Human-readable identifiers. A production contract must bind them to exact revisions. |
| `revisions` | Git commit and tracked-file dirty state when available; not proof of execution identity. |
| `result` | The example's own check outcome, not a claim about external systems. |
| `artifact`, `sha256` | Artifact location and full content hash. A hash binds bytes, not correctness. |
| `check` | Precisely which assertion was run; a stronger requirement may need separate evidence. |
| `limitations` | Unchecked live API, credentials, side effects, identity and other constraints. |

A production handoff would additionally need authenticated producer/observer provenance,
run and stage identifiers, revision-pinned recipes, checker version, observation time,
explicit fail/unknown/uncertain states, platform and environment, and versioned path/hash
semantics. Durable storage and trusted identity come from the host. Distinguish claimed
observations from independently verified facts. Missing, stale, malformed, unsupported or
untrusted entries cannot be silently promoted to `pass`.

No automatic knowledge promotion: a human should examine the evidence, version, scope,
replication and counterexamples before updating a reusable FlowLore recipe or Longhaul rule.
Do not execute commands from a card or catalog entry without an authorized host decision.
