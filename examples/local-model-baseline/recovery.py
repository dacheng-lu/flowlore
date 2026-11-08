#!/usr/bin/env python3
"""Interruption and recovery with a real model call inside a real Makeextreme stage.

The task has three stages: `generate` calls the local model through Makeextreme's
adapter, `verify` renders and checks the digest with FlowLore's deterministic
checker, and `accept` compares the rendered bytes. The runner is killed with SIGKILL
while the model call is in flight, then restarted.

What the record has to prove, and how:
  1. incomplete work is never reported successful - task.json says `running` at the
     kill and only `complete` after the restarted run passes every check;
  2. old artifacts are not taken for current results - after completion the digest
     is edited and a rerun invalidates `verify` instead of skipping it;
  3. a completed stage is not re-executed without basis - after the crash `generate`
     runs a second time, while `verify` and `accept` run once; on a completed task a
     further run starts nothing;
  4. the model's process does not survive as an orphan - no process carrying the
     killed run's MAKEEXTREME_RUN_ID is left after recovery;
  5. final acceptance still runs - `accept` executes and its check passes.

This is a single local observation. It does not prove the same for every runner,
host or filesystem, and a hash proves content, not authorship.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scenarios  # noqa: E402

CASE = "d-valid-3"


def journal(task):
    path = Path(task, "journal.jsonl")
    if not path.exists():
        return []
    out = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def state(task):
    return json.loads(Path(task, "task.json").read_text())


def starts(task, stage=None):
    return [e for e in journal(task) if e.get("ev") == "start"
            and (stage is None or e.get("stage") == stage)]


def pids_with_run_id(run_id):
    needle = f"MAKEEXTREME_RUN_ID={run_id}".encode()
    found = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/environ", "rb") as f:
                if needle in f.read().split(b"\0"):
                    found.append(int(name))
        except OSError:
            continue
    return found


def wait_for(predicate, secs=20, step=0.05):
    end = time.time() + secs
    while time.time() < end:
        if predicate():
            return True
        time.sleep(step)
    return False


def build_task(root, args):
    task = Path(root, "task")
    task.mkdir(parents=True)
    case = scenarios.build()[CASE]
    prompt = scenarios.digest_prompt(case["files"]["release.json"].encode())
    (task / "prompt.txt").write_text(prompt)
    expected = Path(root, "expected.md")
    source = Path(root, "release.json")
    source.write_text(case["files"]["release.json"])
    digest = Path(args.flowlore, "examples", "release-digest", "digest.py")
    subprocess.run([sys.executable, str(digest), "render", str(source), "--output", str(expected)],
                   check=True, capture_output=True, text=True)
    shutil.copy(expected, task / "expected.md")
    (task / "normalize.py").write_text(
        "import json, sys\n"
        "rec = json.load(open('candidate.json'))\n"
        "if rec.get('status') != 'ok':\n"
        "    sys.exit('the model call did not succeed')\n"
        "payload = json.loads(rec['response'])\n"
        "rows = payload.get('records') if isinstance(payload, dict) else None\n"
        "if not isinstance(rows, list):\n"
        "    sys.exit('the model refused or returned no record list')\n"
        "json.dump(rows, open('releases.json', 'w'))\n")
    adapter = Path(args.makeextreme, "makeextreme", "model_runner.py")
    stages = [
        {"id": "generate", "timeout": 120,
         "run": (f"{sys.executable} {adapter} --model {args.model} "
                 f"--prompt-file prompt.txt --out candidate.json --format json "
                 f"--num-predict 384 --num-ctx 8192 --think off --timeout 90"),
         "check": ("python3 -c \"import json;d=json.load(open('candidate.json'));"
                   "assert d.get('status')=='ok' and d.get('response','').strip()\""),
         "outputs": ["candidate.json"]},
        {"id": "verify", "timeout": 60,
         "run": (f"{sys.executable} normalize.py && {sys.executable} {digest} render releases.json "
                 f"--output digest.md && {sys.executable} {digest} check releases.json "
                 f"--output digest.md --expected expected.md"),
         "check": "test -s digest.md",
         "deps": ["candidate.json", "normalize.py", "expected.md"],
         "outputs": ["releases.json", "digest.md"]},
        {"id": "accept", "timeout": 30,
         "run": "cmp digest.md expected.md && echo accepted > accepted.txt",
         "check": "test -s accepted.txt",
         "deps": ["digest.md", "expected.md"],
         "outputs": ["accepted.txt"]},
    ]
    (task / "stages.json").write_text(json.dumps(stages))
    return task


def start_run(args, task):
    return subprocess.Popen([sys.executable, "-m", "makeextreme", "run", str(task)],
                            cwd=args.makeextreme, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--makeextreme", type=Path, required=True)
    parser.add_argument("--flowlore", type=Path, required=True)
    parser.add_argument("--model", default="lfm3:1.7b")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)
    task = build_task(args.out, args)
    evidence = {"version": 1, "case": CASE, "model": args.model,
                "limitations": ["one local observation, one runner and one filesystem",
                                "a content hash proves bytes, not authorship or truth",
                                "the kill window is timed, not synchronised with a stage boundary"],
                "steps": []}

    first = start_run(args, task)
    started_at = time.time()
    ok = wait_for(lambda: starts(task, "generate"), 20)
    if not ok:
        raise SystemExit("the first run never started its model stage")
    time.sleep(0.6)
    run_id = state(task)["stages"].get("generate", {}).get("run_id")
    before = state(task)
    os.killpg(first.pid, signal.SIGKILL)
    first.wait()
    killed_after = round(time.time() - started_at, 3)
    orphans = pids_with_run_id(run_id) if run_id else []
    evidence["steps"].append({
        "step": "kill_during_model_call",
        "killed_after_seconds": killed_after,
        "task_status_at_kill": before["status"],
        "stage_status_at_kill": before["stages"]["generate"]["status"],
        "run_id": run_id,
        "surviving_pids_carrying_the_run_id_at_kill": orphans,
        "false_success": before["status"] == "complete",
    })

    second = start_run(args, task)
    stdout, stderr = second.communicate(timeout=180)
    after = state(task)
    events = [e.get("ev") for e in journal(task)]
    recovered = [e for e in journal(task) if e.get("ev") == "recovered_from_crash"]
    survivors = pids_with_run_id(run_id) if run_id else []
    rendered, expected_text = Path(task, "digest.md"), Path(task, "expected.md").read_text()
    digest_ok = rendered.exists() and rendered.read_text() == expected_text
    evidence["steps"].append({
        "step": "restart_and_recover",
        "exit_code": second.returncode,
        "task_status": after["status"],
        "recovered_from_crash_events": len(recovered),
        "generate_attempts": after["stages"]["generate"]["attempts"],
        "verify_attempts": after["stages"]["verify"]["attempts"],
        "accept_attempts": after["stages"]["accept"]["attempts"],
        "generate_starts": len(starts(task, "generate")),
        "verify_starts": len(starts(task, "verify")),
        "accept_starts": len(starts(task, "accept")),
        "surviving_pids_carrying_the_old_run_id": survivors,
        "digest_equals_expected": digest_ok,
        "stderr_tail": stderr.strip()[-300:],
    })

    total_before = len(starts(task))
    third = start_run(args, task)
    third.communicate(timeout=60)
    total_after = len(starts(task))
    evidence["steps"].append({
        "step": "rerun_a_completed_task",
        "exit_code": third.returncode,
        "new_stage_starts": total_after - total_before,
        "total_start_events": total_after,
    })

    # Drift: the rendered artifact is replaced, so `verify` must not be skipped.
    (Path(task) / "digest.md").write_text("# Release digest\n\n- forged line\n")
    fourth = start_run(args, task)
    fourth.communicate(timeout=180)
    final = state(task)
    evidence["steps"].append({
        "step": "artifact_drift_after_completion",
        "exit_code": fourth.returncode,
        "task_status": final["status"],
        "generate_attempts": final["stages"]["generate"]["attempts"],
        "verify_attempts": final["stages"]["verify"]["attempts"],
        "verify_repeated": final["stages"]["verify"]["attempts"] == 2,
        "digest_restored": ((Path(task) / "digest.md").exists()
                                   and (Path(task) / "digest.md").read_text()
                                   == (Path(task) / "expected.md").read_text()),
    })

    evidence["checks"] = {
        "no_false_success_at_kill": not evidence["steps"][0]["false_success"],
        "recovered_and_completed": evidence["steps"][1]["exit_code"] == 0
                                   and evidence["steps"][1]["task_status"] == "complete",
        "completed_generate_not_restarted": evidence["steps"][1]["generate_attempts"] == 2,
        "no_stage_repeated_after_recovery": evidence["steps"][1]["verify_attempts"] == 1
                                            and evidence["steps"][1]["accept_attempts"] == 1,
        "no_orphan_after_recovery": evidence["steps"][1]["surviving_pids_carrying_the_old_run_id"] == [],
        "final_acceptance_ran": evidence["steps"][1]["accept_attempts"] == 1,
        "stale_artifact_invalidated": evidence["steps"][3]["verify_repeated"]
                                      and evidence["steps"][3]["digest_restored"],
    }
    (args.out / "recovery.json").write_text(json.dumps(evidence, indent=1))
    print(json.dumps({k: v for k, v in evidence["checks"].items()}, indent=1))
    return 0 if all(evidence["checks"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
