# Local-model baseline: two read-only scenarios, deterministic scoring

Status: **one local observation, not a benchmark.** One model, one runner, one
machine, one prompt revision. The numbers describe this setup; they do not
establish what a larger model, another quantisation or a live API would do.

This directory answers three questions with executable evidence:

1. What does an installed local model actually do on a frozen case set whose
   answers are decided by the projects' own checkers, not by another model?
2. Does reserving part of a small request budget for verification beat spending
   it on another generation attempt?
3. Does a real interruption during a real model call recover without false
   completion, duplicated stages or an orphan process?

## What is measured

| Item | Value |
| --- | --- |
| Model | `lfm3:1.7b` (LFM3-1.7B, Q4_K_M, GGUF), digest `b36a103fe2f8fbe9df2ceec88b9cfdf842dc04aaabe2b4677d1acf8e16570b5d` |
| Runner | Ollama 0.40.13 on `127.0.0.1:11434`, one request at a time, 100% GPU (RTX 3050 Laptop, 4 GB) |
| Inference | `temperature=0`, `seed=0`, `num_predict=384`, `num_ctx=8192`, thinking off, runner-side JSON mode |
| Cases | 24 frozen cases: 12 `dev` (used for prompt work), 12 `heldout` (scored as frozen) |
| Scenarios | 14 release-digest cases, 10 checkpoint-gate cases |
| Scorer | `examples/release-digest/digest.py` and Longhaul's `scripts/checkpoint.py gate`, executed on the same bytes |

The case identities and splits are in `cases.json`; the input bytes, prompts and
expected-answer rules are in `scenarios.py`. Both files are hashed into every run
record (`case_set.cases_json_sha256`, `case_set.scenarios_sha256`).

## Scenarios

**Release digest.** The model converts a captured release list into the strict input
of the deterministic digest renderer. Acceptance is byte equality between the
rendered candidate and the rendering of the trusted source, or the refusal the
renderer itself makes. This is structured evidence extraction with a fully
mechanical answer.

**Checkpoint gate.** The model audits a Longhaul v2 record and returns
`{"verdict": ..., "open": [...]}`. Acceptance is `checkpoint.py gate`'s verdict plus
the case's authored open-criterion list; the gate independently confirms every
verdict, and the scorer refuses to run a case whose authored expectation disagrees
with the gate.

Both scenarios are read-only: no repository writes, no network, no external effect.

## Results (2026-11-08)

Full record: [evidence/local-model-baseline-2026-11-08.json](evidence/local-model-baseline-2026-11-08.json).

| Policy | Verified | Requests | Wall (s) | Budget exhausted | Accepted-error attempts | Prompt tokens | Eval tokens |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A fixed retry cap (up to 3 attempts) | **12/24** | 51 | 40.1 | 12 | 10 | 19,768 | 3,965 |
| B two attempts + one reserved verification pass | **11/24** | 63 | 51.2 | 13 | 10 | 28,312 | 5,005 |

By split and scenario:

| Slice | A | B |
| --- | --- | --- |
| `dev` (12 cases) | 9/12 | 8/12 |
| `heldout` (12 cases) | 3/12 | 3/12 |
| release digest (14) | 5/14 | 5/14 |
| checkpoint gate (10) | 7/10 | 6/10 |

All four valid-input digest cases and the prompt-injection case passed under both
policies: the model copies the five fields and does not follow the instruction in
the release title. All nine digest cases whose correct answer is **refusal** failed
under both policies: the model repairs the input instead (drops an extra field,
writes `"title": ""`, converts a string id to an integer) or emits a partial list.
Ten attempts per policy therefore produced an artifact that the renderer accepts
even though the input was invalid — the accepted-error count above.

The gate scenario fails in the other direction: `g-waived` (a recorded waiver is not
accepted) and `g-failed-evidence` (a `result: fail` observation is reported as
`pass`). The second is a false completion claim and the most serious single failure
in the set.

## Budget A/B

Same model, cases, inputs, scorer and inference configuration. Each case has a cap
of three requests under both policies; only the allocation differs. Policies run in
alternating order by case index, one request at a time.

- A: generation attempts only, stop at the first verified answer or after three.
- B: at most two generation attempts, plus one request reserved for a
  verification/repair pass over whatever candidate exists. If no candidate exists,
  the reserved request is not spent.

**Result: no advantage for the reserve policy on this workload.** B verified one
fewer case, used 12 more requests, 11 s more wall time and 44% more prompt tokens.
The loss is traceable: on `g-pass`, A's second attempt returned `{"verdict":"pass"}`
and verified; B's reserved third request re-read the same record and returned
`{"verdict":"blocked","open":["C1"]}`. A model self-check is another model call, not
a stronger verifier, and it can overturn a correct answer.

These are raw counts on 24 paired cases per policy, one repeat. There is no
statistical-significance claim, and the confidence interval around 12/24 vs 11/24
is wide. The effect direction is consistent with the mechanism (an extra call on an
unreliable verifier), and the cost direction is not ambiguous: B always spends the
reserved request when a candidate exists.

## Interruption and recovery

`recovery.py` builds a three-stage Makeextreme task: `generate` calls the local model,
`verify` renders and checks the digest, `accept` compares bytes. It kills the runner's
process group with SIGKILL 0.65 s into the first model call, then restarts.

Recorded in the same evidence file (`recovery`):

| Check | Observation |
| --- | --- |
| No false success at the kill | task and stage were `running`; no `complete` |
| Recovery completed | restart exit 0, status `complete`, one `recovered_from_crash` |
| Completed stage not re-executed | `generate` attempts 2 (was killed), `verify` 1, `accept` 1 |
| No orphan | one pid carried the killed run id at the kill; none after recovery (reaped) |
| Final acceptance ran | `accept` executed once and its check passed |
| Stale artifact not reused | editing `digest.md` re-ran `verify` (attempts 2) and restored the bytes; `generate` stayed at 2 |
| Rerun of a complete task | exit 0, zero new stage starts |

The kill window is timed, not synchronised with a stage boundary, and one run is one
observation. A content hash proves bytes, not authorship.

## Fault injection

Harness faults are separate from model failures and are labelled in every attempt:

- **forced timeout** — the adapter's own bound is set to 0.4 s. It fired on 2 of 6
  designated attempts; in the other four the model answered faster than the bound,
  so the injection did not bite.
- **wrong input delivered** — the attempt receives a valid input whose correct answer
  differs from the case's expectation (an empty list, or a record with a pending
  criterion). All six designated attempts scored 0, as intended; the retry received
  the true input.

No attempt is both faulted and counted as a natural model failure.

## Commands

```bash
# Deterministic: the case set, the scorer and every golden/wrong answer. No model.
python3 examples/local-model-baseline/test_scorer.py --longhaul ../longhaul

# The frozen case set against one local model, both policies, one request at a time.
python3 examples/local-model-baseline/run.py \
  --makeextreme ../makeextreme --longhaul ../longhaul \
  --model lfm3:1.7b --split all --policy both \
  --out /tmp/local-model-run

# Interruption with a real model call inside a real pipeline stage.
python3 examples/local-model-baseline/recovery.py \
  --makeextreme ../makeextreme --flowlore . --out /tmp/local-model-recovery

# Compact evidence from a run directory (no prompts, no local paths).
python3 examples/local-model-baseline/make_evidence.py /tmp/local-model-run \
  --recovery /tmp/local-model-recovery/recovery.json \
  --model-digest <digest> --out evidence/local-model-baseline-<date>.json
```

`run.py` refuses to start without `makeextreme/model_runner.py`,
`makeextreme/budget.py` and Longhaul's gate, and holds an exclusive lock on its
output directory so two runs cannot share one local model at the same time.

## What this does not show

- One model and quantisation. A different model or a larger one can behave
  differently; nothing here ranks models.
- One prompt revision, tuned on `dev` only. `heldout` was frozen before the
  comparison and was not used to change the prompt. If the prompt changes, the
  held-out scores stop being comparable and a new held-out set is required.
- The digest scenario has a mechanical answer, which is why it can be scored this
  way. Most real work does not, and a deterministic scorer is not a substitute for
  domain review.
- Latency and tokens are local wall-clock and runner counters, not prices. The
  accepted-error count measures artifacts that the renderer accepts; it does not
  measure whether a human would have caught them.
- A SHA-256 binding proves content consistency, not who produced it, whether the
  producer was authorised, or whether the content is true.
