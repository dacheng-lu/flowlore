"""Replay one explicitly selected, unfaulted reply from run.py's raw results.json.

This is not a model provider. The compact historical evidence is not a raw run.
"""
import json
import os
from pathlib import Path

import adapter


def call_api(prompt, options, context):
    try:
        path = os.environ["FLOWLORE_RESULTS"]
        policy = os.environ["FLOWLORE_POLICY"]
        raw_attempt = os.environ["FLOWLORE_ATTEMPT"]
        if policy not in ("A", "B") or not raw_attempt.isdigit() or int(raw_attempt) < 1:
            raise ValueError("set policy A/B and a positive attempt index")
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        case = adapter.integrity()[context["vars"]["case_id"]]
        if prompt != adapter.prompt_for(case):
            raise ValueError("delivered prompt differs from the frozen prompt")
        scenario_set = record["scenario_set"]
        for name, key in (("cases.json", "cases_json_sha256"), ("scenarios.py", "scenarios_sha256")):
            if scenario_set[key] != adapter.sha((adapter.BASE / name).read_text(encoding="utf-8"))[:16]:
                raise ValueError("case-set hash mismatch: " + name)
        rows = [r for r in record["cases"] if r["case"] == case["id"] and r["policy"] == policy]
        if len(rows) != 1:
            raise ValueError("expected exactly one matching case and policy")
        if rows[0]["scenario"] != case["scenario"] or rows[0]["split"] != case["split"]:
            raise ValueError("case scenario or split mismatch")
        attempts = [a for a in rows[0]["attempts"] if a["index"] == int(raw_attempt)]
        if len(attempts) != 1:
            raise ValueError("selected attempt is missing or duplicated")
        attempt = attempts[0]
        if attempt["case"] != case["id"] or attempt["policy"] != policy:
            raise ValueError("attempt case or policy mismatch")
        if "fault" not in attempt or attempt["fault"] is not None:
            raise ValueError("faulted or unlabelled attempts cannot be replayed")
        if str(attempt.get("failure", "")).startswith("injected_"):
            raise ValueError("fault-labelled attempt cannot be replayed")
        if attempt["transport"] != "ok":
            raise ValueError("transport was not ok")
        reply = attempt["reply"]
        if not isinstance(reply, str):
            raise ValueError("reply is missing or not text")
        if attempt["reply_sha256"] != adapter.sha(reply)[:16]:
            raise ValueError("reply hash mismatch")
        run = attempt["run"]
        attempt_digest = attempt.get("model_digest")
        if attempt_digest is not None and attempt_digest != record["model"].get("digest"):
            raise ValueError("model digest mismatch")
        if (run["case_id"] != case["id"] or run["model"] != record["model"]["name"]
                or run["input_sha256"] != adapter.sha(adapter.input_text(case))
                or attempt["prompt_sha256"] != adapter.sha(prompt)[:16]):
            raise ValueError("attempt input, model, or prompt binding mismatch")
        return {"output": reply, "metadata": {"flowlore_replay": {
            "policy": policy, "attempt": int(raw_attempt), "model": run["model"],
            "model_digest": attempt_digest}}}
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise ValueError("FLOWLORE_REPLAY_ERROR: " + str(exc)) from exc
