# Budget comparison report handoff

This offline recipe renders the budget-matched aggregate from agent-harness-lab,
checks it against an independently transcribed reference, and records the result
with Makeextreme and Longhaul. The captured `summary.json` is from
[agent-harness-lab commit f708c634](https://github.com/dacheng-lu/agent-harness-lab/blob/f708c634ad7b3872810cff1c096e5175926483a4/results/summary.json).
The reference values were transcribed from the separately maintained
[budget report](https://github.com/dacheng-lu/agent-harness-lab/blob/f708c634ad7b3872810cff1c096e5175926483a4/reports/REPORT_BUDGET.md).
Both files describe the same experiment; they are not independent measurements.

On Linux with Python 3.11+ and sibling checkouts:

```sh
python3 examples/harness-report/run.py --makeextreme ../makeextreme --longhaul ../longhaul --evidence-dir /tmp/harness-report-new
```

Use a new evidence directory. The script copies the producer, swaps its solo and
cluster mappings and runs it. The Makeextreme check must reject the incorrect
report. It saves that report and the failing result, repairs the producer in the
task directory, and reruns the same stage and check. The second result is handed
to a Longhaul checkpoint and its gate. The directory retains the journal,
reports, source, reference, checkpoint and a `tenon/0` candidate card.

The card is an unauthenticated local claim. The source is a captured aggregate,
not a rerun of the benchmark. Repository revisions and tracked dirty state are
recorded; dirty and untracked content is not fully identified by the commit.
The failed producer is reconstructed by the fault injection in `run.py`.
No credentials or external writes are used.
