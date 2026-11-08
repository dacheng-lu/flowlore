#!/usr/bin/env python3
"""Run the frozen cases against one local model under two budget policies.

The model is called through Makeextreme's adapter (``makeextreme/model_runner.py``),
one request at a time. Every request is recorded with the prompt hash, the reply,
the counters the runner reported, and the score the deterministic scorer gave it.
Nothing here retries silently: an attempt is a recorded request with a policy
decision in front of it.

Policies, same cap of three requests per case:
  A  fixed retry cap: generation attempts only, up to three.
  B  reserve: at most two generation attempts, and one request kept for a
     verification/repair pass over the candidate the model produced.

Exit codes: 0 the run finished (whatever the scores), 2 the runner refused to
start (bad checkout, lock held, missing case), 3 no case matched the filter.
"""
import argparse
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scenarios  # noqa: E402
import scorer  # noqa: E402

CAP = 3
# Harness fault injection (class B), applied identically to both policies on the
# first attempt only. These are not model failures and are always reported apart.
FAULTS = {
    "d-valid-3": "timeout",
    "d-valid-6": "wrong_input",
    "g-pass": "wrong_input",
    "g-stale": "timeout",
    "d-empty": "timeout",
    "g-failed-evidence": "wrong_input",
}


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _wrong_input(case):
    """A valid input whose correct answer differs from this case's expectation.

    This models the harness bug that matters most here: the wrong case's bytes are
    delivered. It is a deliberate injection (class B), never counted as a model error.
    """
    if case["scenario"] == "digest":
        valid = case["id"] in ("d-valid-3", "d-valid-1", "d-valid-6", "d-duplicate-identical",
                               "d-injection-title")
        return json.dumps([]) if valid else json.dumps(scenarios.BASE)
    pass_case = scenarios.build()["g-pass"]
    if case["meta"]["expect_pass"]:
        doc = json.loads(pass_case["files"]["state.json"])
        doc["acceptance"][0]["status"] = "pending"
        return json.dumps(doc)
    return pass_case["files"]["state.json"]


def prompt_for(case, fault=None, previous=None):
    files = dict(case["files"])
    if case["scenario"] == "digest":
        data = files["release.json"]
        if fault == "wrong_input":
            data = _wrong_input(case)
        text = scenarios.digest_prompt(data.encode())
    else:
        data = files["state.json"]
        if fault == "wrong_input":
            data = _wrong_input(case)
        text = scenarios.gate_prompt(data.encode())
    if previous is not None:
        text += ("\nA previous answer was:\n" + previous +
                 "\nRe-check it against the input and output the corrected final answer, "
                 "following the same rules. Output only the JSON value.\n")
    return text


def call_model(args, prompt, tag, timeout):
    """One bounded request through Makeextreme's adapter; a timeout is data, not an exception."""
    work = Path(args.out, "requests")
    work.mkdir(parents=True, exist_ok=True)
    prompt_file = work / f"{tag}.prompt.txt"
    reply_file = work / f"{tag}.reply.json"
    prompt_file.write_text(prompt, encoding="utf-8")
    cmd = [sys.executable, str(Path(args.makeextreme, "makeextreme", "model_runner.py")),
           "--model", args.model, "--prompt-file", str(prompt_file), "--out", str(reply_file),
           "--timeout", str(timeout), "--num-predict", str(args.num_predict),
           "--num-ctx", str(args.num_ctx), "--think", args.think, "--format", "json"]
    started = time.monotonic()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=timeout + 20)
    except subprocess.TimeoutExpired:
        # The adapter overran its own bound: stop the whole group, then record the fact.
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
        return {"status": "killed_by_harness", "exit": None, "wall_seconds": round(time.monotonic() - started, 3),
                "tokens": {"prompt": None, "eval": None}, "record": None,
                "stdout": stdout[-200:], "stderr": stderr[-200:]}
    record = json.loads(reply_file.read_text()) if reply_file.exists() else None
    return {"status": (record or {}).get("status", "no_record"), "exit": proc.returncode,
            "wall_seconds": round(time.monotonic() - started, 3),
            "tokens": (record or {}).get("tokens", {"prompt": None, "eval": None}),
            "record": record, "stdout": stdout[-200:], "stderr": stderr[-200:]}


def case_input_sha(case):
    name = "release.json" if case["scenario"] == "digest" else "state.json"
    return hashlib.sha256(case["files"][name].encode()).hexdigest()


def attempt(args, case, index, policy, fault=None, previous=None):
    prompt = prompt_for(case, fault=fault, previous=previous)
    tag = f"{case['id']}.{policy}.{index}"
    reply = call_model(args, prompt, tag, 0.4 if fault == "timeout" else args.timeout)
    text = (reply["record"] or {}).get("response") or ""
    result = {"case": case["id"], "policy": policy, "index": index, "fault": fault,
              "prompt_sha256": sha(prompt), "reply_sha256": sha(text), "reply": text,
              "transport": reply["status"], "exit": reply["exit"],
              "model_digest": (reply["record"] or {}).get("model_digest"),
              "run": {"case_id": case["id"], "model": args.model,
                      "input_sha256": case_input_sha(case)},
              "wall_seconds": reply["wall_seconds"], "tokens": reply["tokens"],
              "done_reason": (reply["record"] or {}).get("done_reason"),
              "score": None, "detail": None, "expected": None, "got": None}
    if reply["status"] == "ok" and text.strip():
        verdict = scorer.evaluate(case, text, longhaul=args.longhaul)
        result.update(score=verdict["score"], detail=verdict["detail"],
                      expected=verdict["expected"], got=verdict["got"])
        if case["scenario"] == "gate" and verdict["got"] and verdict["expected"]:
            result["verdict_correct"] = (verdict["got"].get("verdict")
                                        == verdict["expected"].get("verdict"))
    elif reply["status"] == "ok":
        result.update(score=0, detail="empty reply", failure="empty_answer")
    else:
        result.update(score=0, detail=reply["status"], failure=reply["status"])
    if fault:
        result["failure"] = "injected_" + fault
    elif result.get("score") == 0:
        result["failure"] = result.get("failure") or "wrong_answer"
    return result


def run_case(args, case, policy):
    attempts = []
    if policy == "A":
        for i in range(1, CAP + 1):
            a = attempt(args, case, i, policy, fault=FAULTS.get(case["id"]) if i == 1 else None)
            attempts.append(a)
            if a["score"] == 1:
                break
    else:
        for i in range(1, CAP):
            a = attempt(args, case, i, policy, fault=FAULTS.get(case["id"]) if i == 1 else None)
            attempts.append(a)
            if a["score"] == 1:
                break
        last = attempts[-1]
        if last["reply"].strip():
            # The reserved request is only useful when there is a candidate to re-check.
            attempts.append(attempt(args, case, CAP, policy, previous=last["reply"][:4000]))
    final = attempts[-1]["score"] == 1
    return {"case": case["id"], "scenario": case["scenario"], "split": case["split"],
            "category": case["category"], "policy": policy, "final_verified": final,
            "requests": len(attempts), "attempts": attempts,
            "faults": [a["fault"] for a in attempts if a["fault"]],
            "budget_exhausted": (not final and len(attempts) == CAP)}


def summarize(rows, cases):
    def bucket(rows):
        requests = sum(r["requests"] for r in rows)
        attempts = [a for r in rows for a in r["attempts"]]
        known = [a["tokens"] for a in attempts if a["tokens"]["eval"] is not None]
        return {
            "cases": len(rows),
            "final_verified": sum(r["final_verified"] for r in rows),
            "budget_exhausted": sum(r["budget_exhausted"] for r in rows),
            "requests": requests,
            "timeouts": sum(a["transport"] == "timeout" for a in attempts),
            "harness_kills": sum(a["transport"] == "killed_by_harness" for a in attempts),
            "accepted_errors": sum(1 for a in attempts if a["got"] and a["expected"] and
                                   (a["got"].get("verdict") in ("artifact", "pass")) and
                                   a["expected"].get("verdict") in ("refuse", "blocked")),
            "wrong_answers": sum(a["score"] == 0 for a in attempts),
            "verdict_correct": sum(a.get("verdict_correct") is True for a in attempts),
            "unparseable": sum((a.get("failure") or "") == "unparseable" for a in attempts),
            "eval_tokens_known": sum(t["eval"] for t in known),
            "prompt_tokens_known": sum(t["prompt"] for t in known),
            "wall_seconds": round(sum(a["wall_seconds"] for a in attempts), 3),
        }

    out = {"all": bucket(rows)}
    for policy in ("A", "B"):
        out[policy] = bucket([r for r in rows if r["policy"] == policy])
        for split in ("dev", "heldout"):
            out[f"{policy}/{split}"] = bucket([r for r in rows if r["policy"] == policy
                                               and r["split"] == split])
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--makeextreme", type=Path, required=True)
    parser.add_argument("--longhaul", type=Path, required=True)
    parser.add_argument("--model", default="lfm3:1.7b")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--split", choices=("dev", "heldout", "all"), default="heldout")
    parser.add_argument("--policy", choices=("A", "B", "both"), default="both")
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--num-predict", type=int, default=384)
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--think", choices=("on", "off"), default="on")
    parser.add_argument("--only", action="append", default=[])
    args = parser.parse_args()

    adapter = Path(args.makeextreme, "makeextreme", "model_runner.py")
    gate = Path(args.longhaul, "scripts", "checkpoint.py")
    for needed in (adapter, gate, Path(args.makeextreme, "makeextreme", "budget.py")):
        if not needed.exists():
            print(f"refused: missing {needed.name} in the given checkouts", file=sys.stderr)
            return 2

    cases = scenarios.build()
    selected = [c for c in cases.values()
                if (args.split == "all" or c["split"] == args.split)
                and (not args.only or c["id"] in args.only)]
    if not selected:
        print("no case matched the filter", file=sys.stderr)
        return 3

    args.out.mkdir(parents=True, exist_ok=True)
    lock = open(args.out / "run.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("refused: another run holds this output directory", file=sys.stderr)
        return 2

    policies = ("A", "B") if args.policy == "both" else (args.policy,)
    rows = []
    started = time.monotonic()
    model_digest = None
    for n, case in enumerate(selected):
        order = policies if (policies == ("A",) or policies == ("B",) or n % 2 == 0) \
            else tuple(reversed(policies))
        for policy in order:
            row = run_case(args, case, policy)
            if model_digest is None:
                model_digest = next((a.get("model_digest") for a in row["attempts"]
                                     if a.get("model_digest")), None)
            rows.append(row)
            with open(args.out / "rows.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            print(f"{case['id']:24} {policy} verified={row['final_verified']} "
                  f"requests={row['requests']}", flush=True)
    wall = round(time.monotonic() - started, 3)

    case_bytes = json.dumps({c["id"]: c for c in selected}, sort_keys=True).encode()
    record = {
        "version": 1,
        "scenario_set": {"cases": len(selected), "split": args.split,
                         "cases_json_sha256": sha((HERE / "cases.json").read_text()),
                         "scenarios_sha256": sha((HERE / "scenarios.py").read_text()),
                         "rendered_cases_sha256": hashlib.sha256(case_bytes).hexdigest()},
        "model": {"name": args.model, "digest": model_digest,
                  "num_predict": args.num_predict, "num_ctx": args.num_ctx,
                  "temperature": 0.0, "seed": 0, "think": args.think},
        "budget": {"cap_per_case": CAP, "policies": {"A": "fixed retry cap",
                                                     "B": "two attempts plus one reserved verification pass"},
                   "concurrency": 1},
        "policy_order": "both policies run every case; the first policy alternates by case index",
        "wall_seconds": wall,
        "summary": summarize(rows, selected),
        "cases": rows,
    }
    (args.out / "results.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(json.dumps(record["summary"]["all"], indent=1))
    print(f"results: {args.out / 'results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
