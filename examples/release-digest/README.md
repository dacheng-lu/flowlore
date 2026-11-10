# Offline release digest: three-project example

FlowLore supplies the source-backed [release digest recipe](../../recipes/README.md); the fixed
fixtures here describe two **fictional** releases. Makeextreme runs a two-stage pipeline and
checks the generated report. Longhaul records an observation after the example independently
compares that report to `expected.md`. The script then alters the report, verifies old evidence
is stale, asks Makeextreme to restore the declared output, rechecks and records a new observation.
The separate upstream Makeextreme demo also exercises an actual interruption and recovery.
The emitted candidate card is now `tenon/0`; it is an unauthenticated claim, not a receipt.

This is a manually scripted integration demonstration, not an automatic adapter, authenticated
receipt, or a verified live GitHub API recipe. It sends no requests, needs no keys, performs no
external publishing, and uses a temporary task directory. A passing gate does not establish truth
beyond the stated checks. The evidence card is a proposed local interchange example, not a standard.

Requirements: Linux, `/proc` in the current PID namespace, Python 3.11+ and three checked-out
repositories. The checked-in workflow pins Longhaul and Makeextreme commits for reproducibility;
the FlowLore revision is the workflow commit. A second CI combination checks both peers'
current `main` branches; its precise revisions are recorded in each run. From the parent directory of the three checkouts:

```bash
cd flowlore
python3 examples/release-digest/test_digest.py
python3 examples/release-digest/integration.py --makeextreme ../makeextreme --longhaul ../longhaul
```

Expected: two unique records (one duplicate removed), an exact match with `expected.md`, stale
Longhaul evidence rejected after a change, a restored digest, stage starts 1/2, and the existing
crash/recovery example passes. Invalid, empty or missing records and conflicting duplicates are
covered by `test_digest.py`. Failures stop the script; they do not produce a success card.

Use `digest.py verify SOURCE --output DIGEST.md` when the digest came from an untrusted step
(a model, a generator, a downloaded file). `check` compares two files, so a producer that
silently repairs an invalid source — dropping an extra field, inventing a missing title —
can still hand you a digest that passes against a fixture derived from its own repaired
bytes. `verify` validates the trusted source itself and requires the delivered bytes to be
exactly its rendering. The local-model baseline measured this failure: see
[`examples/local-model-baseline`](../local-model-baseline/README.md).

Live GitHub API pagination, rate limits, changing upstream data, event delivery and exactly-once
external publishing remain untested. The broader Release Digest recipe remains `draft` until
those requirements and the repository's verification criteria are met. Use host permissions,
separate authentication and a durable store for any real deployment.

## Bounded public API experiment

`live_releases.py` performs only public GitHub API reads, with a fixed API host, no credentials,
timeouts and bounded pages. It returns JSON as untrusted data. The default refuses when the
page limit may truncate results. To deliberately inspect just a small sample:

```bash
python3 examples/release-digest/live_releases.py cli/cli --per-page 3 --max-pages 1 --allow-partial > /tmp/releases.json
python3 examples/release-digest/integration.py --makeextreme ../makeextreme --longhaul ../longhaul --live-snapshot /tmp/releases.json
```

The output explicitly reports `complete: false` for a page-limited sample. The integration
uses validated repository, release id, tag and URL fields; it replaces untrusted release titles
with a fixed label. Its structural comparison is derived from that captured input and is not
an independent semantic review. It does not establish freshness after capture or exactly-once
delivery. A separate non-blocking PR and manually dispatched CI job exercises this read-only
path; its failure can reflect external rate limits or upstream changes. Required regression
checks use offline fixtures and do not depend on this network job.
[One observed public sample and its limits](evidence/public-sample-2026-11-05.md).

## Inspect a local run

To retain the non-sensitive example records, pass `--evidence-dir /tmp/trio-evidence-new` to
`integration.py`; the destination must not exist. Then run:

```bash
python3 examples/release-digest/tenon.py --card /tmp/trio-evidence-new/card.json --artifact /tmp/trio-evidence-new/digest.md --journal /tmp/trio-evidence-new/journal.jsonl --checkpoint /tmp/trio-evidence-new/longhaul.json
```

The view compares bytes and summarizes events and evidence counts without modifying files.
It does not authenticate their relationship, validate semantic correctness, or replace the
Longhaul gate. Its default output does not print the report, prompts or checkpoint content.

## Reproduce a captured public sample

A captured GitHub API response is stored at [cli-snapshot](evidence/cli-snapshot/).
`raw.json.gz` contains the exact response body; `capture.json` records its SHA-256
(over decompressed bytes), URL, time and scope. It contains one full requested
page of three releases and is deliberately marked **partial**: it does not claim
to cover all releases. The independently prepared `expected.md` lists these
three tags and links, not their release notes. The sample is not a live refresh.

From this repository, with sibling Longhaul and Makeextreme checkouts:

```bash
python3 examples/release-digest/test_snapshot.py
python3 examples/release-digest/reproduce_snapshot.py --makeextreme ../makeextreme --longhaul ../longhaul
```

To retain the digest and records for inspection, pass `--output-dir /tmp/release-digest-records`
to the second command. The directory must not already exist and its parent must
exist. It contains `digest.md`, `card.json`, the sanitized input, journal and
Longhaul checkpoint. The command runs a fresh temporary task each time; the
retained records are evidence for inspection, not a resumable task directory.
Use a new output directory for another run. The card records the checked-out
component revisions and whether tracked files were dirty; a dirty checkout does
not identify all source bytes. The capture remains a partial historical sample.

For interruption and resume behavior, the command also runs the separate upstream
crash-recovery demonstration. It does not test interruption of this snapshot run.

### Run the captured snapshot as a resumable task

For a persistent Makeextreme task, initialize a new directory and run it:

```bash
python3 examples/release-digest/persistent_snapshot.py init /tmp/release-digest-task
python3 examples/release-digest/persistent_snapshot.py run /tmp/release-digest-task --makeextreme ../makeextreme
```

Run the second command again after an interruption. On success the task contains
`digest.md` and Makeextreme's state and journal. It verifies the captured source
and independent expected digest on every invocation, including skipped stages.
The task directory contains executable scripts: keep it trusted and do not run
tasks supplied by an untrusted party. It is a separate local example; it does not
fetch live releases, authenticate the source, or publish anything. The source is
a partial historical capture. Longhaul evidence is optional, as described below.

To also record a Longhaul checkpoint, add `--longhaul ../longhaul` to the run
command. Each successful invocation writes a separate `evidence/snapshot-*.json`
record, with a fresh run ID and a digest of the four captured source files. The
checkpoint binds the checked digest and each source file, so changing or
deleting one causes Longhaul's gate to refuse the old record. Verify it with:

```bash
python3 ../longhaul/scripts/checkpoint.py gate /tmp/release-digest-task/evidence/snapshot-REPLACE_WITH_PRINTED_ID.json
```

Replace the example filename with the exact printed checkpoint filename.
The gate checks the current files and the recorded run binding. An old record
describes its own past invocation, not the status of a later failed run. Keep
the task and checkpoint files trusted and unchanged while the check runs. These
records are local bookkeeping: they do not authenticate the operator or source,
and hashes do not prove the semantic truth of external data. The persistent
task remains usable without Longhaul.

Run the synchronized interruption and repair tests with:

```bash
python3 examples/release-digest/test_persistent_snapshot.py --makeextreme ../makeextreme --longhaul ../longhaul
```

Replay checks raw SHA-256 and normalization, compares the output to the independent
expected file, exercises recovery and evidence invalidation, and makes no network
requests. CI tests pinned and current peer versions. The hash records integrity,
not authorship or independent proof of origin; it is not a signed receipt.
The wider API-to-published-digest recipe stays draft: completeness, network failure
semantics, real publishing and a network-isolated run remain unverified.

## Network namespace CI trial

`.github/workflows/isolated-snapshot.yml` checks out pinned peers and executes
`isolated_ci.sh` inside an OS network namespace. The script requires an
`ENETUNREACH` network probe and writes versions, test results and replay output
as a CI artifact. It fails closed if isolation cannot be created or the probe
fails. The artifact remains a CI observation, not authentication of the API
capture; the broader release digest is still draft. A configured workflow alone
is not evidence that it passed: check the exact run and commit.

## Bounded handoff consistency

The captured-snapshot replay now checks the local card, source and sanitized input,
report bytes, expected digest, journal, and Longhaul checkpoint gate before
reporting its bounded handoff consistent. `verify_handoff.py` can also inspect a
retained `--evidence-dir` bundle when supplied trusted source and component
revisions; it does not execute a command from a card or grant task acceptance.

This is a local, single-case adapter for trusted, quiescent files, not a general
shared adapter or authentication mechanism. Supplied revisions and journal entries
are claims; hashes cannot prove who ran a check or whether it was truthful.

## Budget comparison on the digest workload

For a separate deterministic comparison of a plain script, Makeextreme, and
Makeextreme plus a Longhaul checkpoint, run:

```bash
python3 examples/release-digest/compare_recovery.py --makeextreme ../makeextreme --longhaul ../longhaul --output /tmp/digest-comparison.json
python3 examples/release-digest/test_compare_recovery.py
```

All conditions apply the same source verification for final acceptance. The
separately reported weaker check is a diagnostic and does not decide acceptance.
The output records revisions, commands, observations and local wall times. This
is one run of four synthetic scenarios; it does not measure a real process
interruption, model call, or cross-run evidence binding, and does not establish
statistical significance or real-world cost savings. Choose a new output path
for each run; the command will not overwrite an existing file.

With a Makeextreme checkout that has `makeextreme/budget.py`:

```bash
python3 examples/release-digest/budget_compare.py --makeextreme ../makeextreme
python3 examples/release-digest/test_budget_compare.py --makeextreme ../makeextreme
```

This runs actual digest render and check subprocesses on the saved sample; it
injects malformed inputs on designated attempts and measures wall-clock duration.
The same four traces feed both policies. Budget units and costs (9 total, 2 per
attempt, 3 for verification) are deliberately modeled; they are neither actual
API charges nor enforced wall-time limits. There are no model calls, real recovery
actions, external effects, or statistical claims. A conservative reserve can
leave a late success unattempted; unknown real costs still need host metering.
