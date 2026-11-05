# Trio trust contract — v0 (draft for discussion)

Status: **proposed, not authoritative, not frozen.** Nothing may consume this as evidence
without its own validation. It exists so the three projects can argue about fields before any
code depends on them.

## Purpose

Carry one task's evidence from a recipe (FlowLore) through execution (Makeextreme) to a
verdict (Longhaul) without any project having to trust another's prose.

## Fields

| Field | Meaning | Not a proof of |
|---|---|---|
| `schema` | `trio-trust/0` while draft | compatibility |
| `task`, `stage` | stable identifiers; a stage belongs to exactly one task | identity |
| `mandate` | id, policy version, scope, strength, requester *as reported by the host*, approver | authenticated identity |
| `capability` | readable/writable paths, reachable hosts, credential *names* | actual containment |
| `effect` | `pure`/`reversible`/`irreversible`/`unknown` | real-world reversibility |
| `artifact`, `sha256` | path and content hash at the time of the claim | correctness |
| `evidence` | which check ran, its version, its result, and whether it was deterministic or a second identity | that the check is sufficient |
| `approval` | who, when, and the hash the approval was bound to | that the approver understood the action |
| `verifier` | `deterministic` or an identity that did not produce the artifact | independence in the strong sense |
| `time`, `environment` | observation time, host and runtime versions | freshness after the fact |

## Rules

1. Missing, stale, malformed or untrusted fields are `unknown`, never `pass`.
2. A policy change invalidates verdicts computed under the old policy; they are not silently
   recomputed.
3. A producer cannot be the sole verifier. "Same agent, second look" is not independent.
4. A hash binds bytes, not correctness, and not the absence of other effects.
5. Durable storage, credentials and identity come from the host.
6. Each project remains independently usable when a field or a peer is absent.

## Freeze condition

One real task end to end (release-digest): FlowLore recipe → Makeextreme stages → Longhaul
verdict, including one negative control (edited artifact or stale evidence) that fails with
the rule named. Only then may this become `trio-trust/1`.
