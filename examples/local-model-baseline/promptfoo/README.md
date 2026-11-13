# Optional Promptfoo adapter

This is an **experimental, not end-to-end verified** Promptfoo integration. The
Python callbacks and original deterministic checkers were tested directly, but
Promptfoo `eval` was not run in the development environment: automatic approval
rejected the execution. The config and JSON export validator follow the published
Python callback interface and the inspected 0.125.1 source; their actual
Promptfoo interoperability still needs an authorized run. No new model was run.

It reuses the unchanged `cases.json`, `scenarios.py` and `scorer.py`: 14 digest
and 10 gate cases, with their existing dev/heldout splits. It checks the exact
prompt and input hash, preflights the frozen files and checker, and invokes the
original scorer. Oracle errors are tagged `FLOWLORE_HARNESS_ERROR`; they are not
model failures. Promptfoo itself may count a Python assertion exception as a
failed test: **do not interpret its displayed aggregate** until
`validate_results.py` accepts the exported JSON. That validator reruns the
original scorer on every saved response and checks case count, provider, prompt,
input, one assertion, and score consistency. It cannot authenticate a producer
or prove that the prompt actually reached a model.

## Setup and direct offline checks

Node >=22.22.0, Python 3, git and a clean Longhaul checkout are required. The
optional package and lockfile pin Promptfoo 0.125.1 and its dependency tree;
installing requires access to npm. Nothing is installed for ordinary FlowLore
usage. From this directory, after the package cache is available:

```bash
npm ci --ignore-scripts --no-audit --no-fund
export FLOWLORE_LONGHAUL=/absolute/path/to/longhaul
# Default is the project's pinned CI revision. To use another clean checkout,
# set its full 40-character SHA explicitly and keep it for the entire run:
export FLOWLORE_LONGHAUL_REV=fd81df28052f1c1d0f29955a8a48170049d4cbf0
python3 adapter.py
python3 test_adapter.py
```

The Longhaul revision and tracked files are checked; an override changes the
oracle version and must be recorded with results. FlowLore baseline files are
hash-pinned, so updating them intentionally also requires updating this adapter.
The 24-case preflight runs the actual checker for every fixture, including a
known valid digest validate/render, and checks response protocols. No Promptfoo
or model is needed for these direct tests.

## Synthetic Promptfoo smoke test (not a model run)

The provided provider synthesizes the existing `test_scorer.py` golden or wrong
answers. `good` should produce 24 passes; `wrong` should produce 24 failures.
These are adapter test doubles, never historical model outputs. This command is
provided for a future authorized verification; it has not been exercised here.

```bash
export PROMPTFOO_DISABLE_TELEMETRY=1 PROMPTFOO_DISABLE_SHARING=1
export PROMPTFOO_CONFIG_DIR=/tmp/flowlore-promptfoo
export PROMPTFOO_PYTHON=python3 FLOWLORE_SPLIT=all FLOWLORE_SYNTHETIC=good
./node_modules/.bin/promptfoo eval -c promptfooconfig.yaml --no-cache -o /tmp/flowlore-good.json
python3 validate_results.py /tmp/flowlore-good.json --split all
export FLOWLORE_SYNTHETIC=wrong
./node_modules/.bin/promptfoo eval -c promptfooconfig.yaml --no-cache -o /tmp/flowlore-wrong.json
python3 validate_results.py /tmp/flowlore-wrong.json --split all
```

A failing assertion can make the second eval exit nonzero; validate the saved
file regardless. Disabling telemetry/sharing is not a network sandbox. Promptfoo
may persist local prompts, responses and configuration; use a private config/output
directory and enforce network isolation externally if required. Never send these
inputs to a remote provider without deciding to do so.

## Replay a raw run

`promptfooconfig.replay.yaml` reads **raw** `run.py` `results.json`, with an
explicit policy and attempt. It never calls a model. The checked-in compact
evidence has only selected excerpts, not all replies, and is rejected. For example:

```bash
export FLOWLORE_RESULTS=/absolute/path/to/raw/results.json
export FLOWLORE_POLICY=A FLOWLORE_ATTEMPT=2
export FLOWLORE_SPLIT=all FLOWLORE_ONLY=d-valid-3
./node_modules/.bin/promptfoo eval -c promptfooconfig.replay.yaml --no-cache -o /tmp/flowlore-replay.json
python3 validate_results.py /tmp/flowlore-replay.json --split all
```

Keep the same environment for validation. `FLOWLORE_ONLY` is a comma-separated
list of IDs; omit it only if every selected case contains that attempt. Missing,
duplicated, non-text, fault-injected, non-`ok` transport or mismatched records
are errors, not scores. Empty successful replies remain legitimate 0 scores.
The replay checks the case, policy, attempt, model, available model digest, input,
prompt and reply hashes. The original prompt/reply and case-file hashes are
truncated to 16 hex characters; they establish limited consistency, not
cryptographic provenance. A reserved verification pass changes the prompt and is
therefore rejected by this adapter. Different retries and fault injections are
not silently combined. A runtime binding in the test variables includes the raw
file hash and selectors to avoid reusing an earlier cache entry; still use
`--no-cache`.

To evaluate a model instead, replace the synthetic provider in a **separate**
local config with a Promptfoo provider you have chosen and authorized. Preserve
the prompt, generated tests and assertion, ensure the provider returns the raw
string and does not alter the prompt, then validate the JSON as above. This is a
single-attempt eval: it does not reproduce `run.py`'s A/B policies, fault
injection, runner configuration, timing or token counts. Do not compare it as the
same experiment. `dev` is the default; using heldout for prompt tuning invalidates
its original heldout interpretation.

Promptfoo interfaces: [Python assertions](https://www.promptfoo.dev/docs/configuration/expected-outputs/python/),
[Python providers](https://www.promptfoo.dev/docs/providers/python/), and
[Python-generated tests](https://www.promptfoo.dev/docs/configuration/test-cases/).
