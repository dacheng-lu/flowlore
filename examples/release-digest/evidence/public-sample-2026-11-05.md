# Public release sample — observed run

On 2026-11-05 at 09:59 UTC, the [GitHub Actions job](https://github.com/dacheng-lu/flowlore/actions/runs/42006911504/job/127175893302)
read three public `cli/cli` release records via the GitHub API and explicitly marked the
one-page sample incomplete. It then ran the snapshot through the three-project example.
The job's API-read step and three-project step both reported success.

The log records FlowLore's GitHub-generated PR merge commit
`15b865a5fe929e1de672e9a85c533a22c417687e`, Longhaul
`788ec8992c9b344035e03016b54df01a79cebda0`, and Makeextreme
`cec41676d91ec9e7954252c55190c8d67f001910`. It reports a stale-evidence rejection,
restoration of changed output, and the separate interruption/recovery demonstration.
The digest hash was `1efade348a36dc2f34ed2a6aa47f6fe26d42ae655474863281858e6c23f0cde7`.

The report and captured source data were temporary and not archived; the log and hash
alone do not make this exact output independently reproducible. A subsequent public API
run may return different releases. The expected output was derived from the same input;
there was no independent semantic review. No external publishing was performed. This
is evidence of one bounded experiment, **not** a verified live recipe or an authenticated
receipt.
