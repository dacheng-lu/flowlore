# Candidate three-project evidence card

Status: **proposed, not a cross-project standard or automatic adapter**. The offline
[release digest example](../examples/release-digest/README.md) emits a small local card
labelled `tenon/0`, a narrow implementation experiment of the broader
[`trio-trust/0` proposal](proposals/trio-trust-contract-v0.md). Its fields are intended for discussion and inspection;
no project should consume it as authoritative evidence without its own validation.

| Field | Meaning and limitation |
| --- | --- |
| `schema` | Identifies this illustrative example; incompatible or missing versions are unknown. |
| `task`, `run`, `stage`, `recipe` | Identifiers for the claimed execution. They are unauthenticated; the recipe still needs a version binding. |
| `revisions` | Git commit and tracked-file dirty state when available; not proof of execution identity. |
| `result` | The example's own check outcome, not a claim about external systems. |
| `artifact`, `sha256` | Artifact location and full content hash. A hash binds bytes, not correctness. |
| `check` | Precisely which assertion was run; a stronger requirement may need separate evidence. |
| `limitations` | Unchecked live API, credentials, side effects, identity and other constraints. |

A production handoff would additionally need authenticated producer/observer provenance,
revision-pinned recipes, checker version, observation time,
explicit fail/unknown/uncertain states, platform and environment, and versioned path/hash
semantics. Durable storage and trusted identity come from the host. Distinguish claimed
observations from independently verified facts. Missing, stale, malformed, unsupported or
untrusted entries cannot be silently promoted to `pass`.

No automatic knowledge promotion: a human should examine the evidence, version, scope,
replication and counterexamples before updating a reusable FlowLore recipe or Longhaul rule.
Do not execute commands from a card or catalog entry without an authorized host decision.

`examples/release-digest/tenon.py` checks required fields and compares a separately supplied
local artifact's bytes to the claimed hash. Its `match` means only byte equality, not that
the claimed check ran or passed. Unsupported cards, absent fields and absent revisions are
unknown; changed bytes are a mismatch. The view can summarize manually selected journal and
checkpoint files, but cannot authenticate that they belong to the same run and does not run
Longhaul's gate. It never executes commands from the card and does not follow artifact paths
from it. `tenon/0` is not frozen, a security boundary, or an automatic handoff.
