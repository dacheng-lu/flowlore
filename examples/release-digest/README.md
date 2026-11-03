# Offline release digest: three-project example

FlowLore supplies the source-backed [release digest recipe](../../recipes/README.md); the fixed
fixtures here describe two **fictional** releases. Makeextreme runs a two-stage pipeline and
checks the generated report. Longhaul records an observation after the example independently
compares that report to `expected.md`. The script then alters the report, verifies old evidence
is stale, asks Makeextreme to restore the declared output, rechecks and records a new observation.
The separate upstream Makeextreme demo also exercises an actual interruption and recovery.

This is a manually scripted integration demonstration, not an automatic adapter, authenticated
receipt, or a verified live GitHub API recipe. It sends no requests, needs no keys, performs no
external publishing, and uses a temporary task directory. A passing gate does not establish truth
beyond the stated checks. The evidence card is a proposed local interchange example, not a standard.

Requirements: Linux, `/proc` in the current PID namespace, Python 3.11+ and three checked-out
repositories. The checked-in workflow pins Longhaul and Makeextreme commits for reproducibility;
the FlowLore revision is the workflow commit. From the parent directory of the three checkouts:

```bash
cd flowlore
python3 examples/release-digest/test_digest.py
python3 examples/release-digest/integration.py --makeextreme ../makeextreme --longhaul ../longhaul
```

Expected: two unique records (one duplicate removed), an exact match with `expected.md`, stale
Longhaul evidence rejected after a change, a restored digest, stage starts 1/2, and the existing
crash/recovery example passes. Invalid, empty or missing records and conflicting duplicates are
covered by `test_digest.py`. Failures stop the script; they do not produce a success card.

Live GitHub API pagination, rate limits, changing upstream data, event delivery and exactly-once
external publishing remain untested. The broader Release Digest recipe remains `draft` until
those requirements and the repository's verification criteria are met. Use host permissions,
separate authentication and a durable store for any real deployment.
