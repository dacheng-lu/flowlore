# Proposal — FlowLore next major: capabilities in the catalog, read-only by construction

Status: **proposed, not decided, not scheduled.** The catalog schema is at `0.1`; nothing
here is implemented and no recipe gains a status from this page.

## Why

A recipe currently says what it does, for which engine and with which evidence. It does not
say what it needs: which paths it writes, which hosts it calls, which credentials it names,
and whether its effect can be undone. Without those fields a higher layer cannot decide
whether a recipe is safe at a given autonomy level — it has to read prose and guess.

North star, shared with Longhaul and Makeextreme: the least human attention for the most
value. A field that no consumer can act on is not added; a field that cannot be validated is
not trusted.

## What would change

1. **Capabilities in the schema.** Each recipe declares: readable paths, writable paths,
   reachable hosts, credentials *by name* (never a value), effect class (`pure`, `reversible`,
   `irreversible`, `unknown`), and the highest autonomy level at which it has actually been
   tested. `unknown` is treated as irreversible. A missing effect, or `verified` without an
   existing evidence file, fails validation.
2. **Untrusted content by default.** Text fetched from a web page is `untrusted` in the
   catalog and in the trio contract. A recipe that consumes it must say how it is sanitised;
   an instruction inside fetched content is data, not authority.
3. **A read-only query surface.** An MCP resource (and the same data as plain JSON) to search
   recipes by intent, platform, dependency, verification status and autonomy level. The
   interface has no write path, no execution and no credential access. A query cannot promote
   a recipe's status.
4. **End-to-end proof.** One `release-digest` run: FlowLore recipe → Makeextreme execution →
   Longhaul verdict, with the v0 contract and the hashes. This is the test that decides
   whether the contract is real; until it passes, the contract stays `v0`.
5. **Evidence stays dated and scoped.** `verified` continues to mean: pinned engine version,
   pinned source revision, a recorded command, a result, and an evidence file that exists.
   A directory existing is not evidence.

## Autonomy ladder (shared)

L0 shadow → L1 reversible inside the task directory → L2 whitelisted egress + credential
broker → L3 irreversible with a human approval bound to the content hash. FlowLore only
*describes* what a recipe needs; it never grants a level and never executes anything.

## Acceptance

- A recipe with an effect class missing, or `verified` without an evidence file, fails the
  validator and names the recipe id.
- A recipe claiming L2 without a declared host list fails validation.
- A credential field containing a value instead of a name fails validation.
- Fetched web content is marked `untrusted` in the catalog and in the exported digest.
- The query surface returns only read-only results; a request that tries to write is refused
  by the interface, not by convention.
- The release-digest end-to-end run produces the contract card with real hashes, and a
  negative control (a stale or edited artifact) fails the Longhaul gate.

## Non-goals

- FlowLore does not execute recipes, store credentials or hold write permissions.
- It does not become an engine, a marketplace or a ranking.
- It does not import third-party templates without a licence review.
- No recipe is promoted automatically; a watcher only produces items for review.

## Order

M0 the existing P0 (the first reproducible recipe evidence) → M1 schema capabilities + validator
+ tests → M2 the read-only query surface → M3 release-digest end to end with Makeextreme and
Longhaul → M4 untrusted-content rules and the contract `v1` freeze. Each step is a PR with
evidence and limits, never a direct push to `main`.
