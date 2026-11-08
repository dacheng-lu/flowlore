# Captured release snapshot replay

Status: **verified for this pinned offline sample only** (2026-11-08). The source
is a single public GitHub API page for `cli/cli`, three releases, explicitly
partial. The wider live release digest stays draft.

Input: saved response and capture metadata in [cli-snapshot](../examples/release-digest/evidence/cli-snapshot/).
Output: a three-link Markdown digest compared byte-for-byte with the independently
prepared `expected.md`; the sample includes no release-note summary.

Dependencies: Linux, Python 3.14.4 for the recorded run, FlowLore commit
`b81d170bac27ab700127f7bf40c11d4610d7a9a9`, Longhaul commit
`b494f078c0dfdba10469354d793d334edcbe8f60`, and Makeextreme commit
`0c4decc6dc606386c2b106011ee4f7d5f698453f`. Reproduce from the parent
of the checkouts, after checking out those exact commits:

```bash
cd flowlore
python3 examples/release-digest/reproduce_snapshot.py --makeextreme ../makeextreme --longhaul ../longhaul
```

Verification evidence: [isolated CI run](https://github.com/dacheng-lu/flowlore/actions/runs/42497752231)
and [captured run outputs](../examples/release-digest/evidence/cli-snapshot/isolated-ci-2026-11-08/).
The pinned runner created a separate network namespace and observed ENETUNREACH,
then validated the raw response hash and normalized fields, ran the two-stage
pipeline, checked the expected output, rejected stale checkpoint evidence and
restored modified output. An additional existing upstream demo exercises a killed
runner and recovery; interruption of the digest pipeline itself was not tested.

[Evidence manifest](../evidence/recipes/captured-release-snapshot.json) binds the
run output and saved inputs to hashes and component revisions. Its validator
checks bytes and structure, not authenticity, remote origin, or semantics.
The run does not demonstrate complete API pagination, current data, authenticated
provenance, external delivery, exactly-once publication, real model output, or
network isolation on every host. A changed source, code, checker or expected
output requires fresh evidence before extending this verified claim.
