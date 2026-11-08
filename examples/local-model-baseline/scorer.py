#!/usr/bin/env python3
"""Deterministic scorer for the local-model baseline.

The expected answer is never a model opinion. For a digest case it is what
``examples/release-digest/digest.py`` does with the same input (render, then
compare bytes); for a gate case it is what Longhaul's ``scripts/checkpoint.py
gate`` says about the same record, together with the case's authored list of
open criteria. Both oracles are executed, not reimplemented.

Scoring is deliberately lenient about packaging (a fenced block or a sentence
around the JSON is accepted when exactly one JSON value can be recovered) and
strict about content: fields, values, order-insensitivity only where the
project's checker is order-insensitive, and refusal where the checker refuses.

This module makes no network or model calls.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLOWLORE = HERE.parents[1]


class ScorerError(Exception):
    """The fixture and the independent checker disagree: no score can be trusted."""


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60, **kw)


def _write_fixture(files, directory):
    for name, text in files.items():
        path = Path(directory, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _digest(files, output, work, digest_script):
    _write_fixture(files, work)
    source = Path(work, "release.json")
    valid = _run([sys.executable, str(digest_script), "validate", str(source)])
    expected_file = Path(work, "expected.md")
    if valid.returncode == 0:
        rendered = _run([sys.executable, str(digest_script), "render", str(source),
                         "--output", str(expected_file)])
        if rendered.returncode != 0:
            raise ScorerError(f"digest render failed on a valid fixture: {rendered.stderr.strip()}")
        expected = {"verdict": "artifact", "sha256": _sha(expected_file)}
    else:
        expected = {"verdict": "refuse", "reason": valid.stderr.strip()}

    if isinstance(output, dict) and "refuse" in output:
        got = {"verdict": "refuse", "reason": str(output["refuse"])}
        if expected["verdict"] == "refuse":
            return 1, expected, got, "refused exactly where the checker refuses"
        return 0, expected, got, "refused a valid input the checker accepts"
    if isinstance(output, dict) and set(output) == {"records"} and isinstance(output["records"], list):
        output = output["records"]  # the documented envelope; contents are still checked below
    if not isinstance(output, list):
        return 0, expected, {"verdict": "unparseable"}, "no record list or refusal object"
    candidate = Path(work, "candidate.json")
    out_md = Path(work, "candidate.md")
    candidate.write_text(json.dumps(output), encoding="utf-8")
    rendered = _run([sys.executable, str(digest_script), "render", str(candidate),
                     "--output", str(out_md)])
    if rendered.returncode != 0:
        return 0, expected, {"verdict": "checker_refused_output"}, rendered.stderr.strip()[:200]
    got = {"verdict": "artifact", "sha256": _sha(out_md)}
    if expected["verdict"] == "refuse":
        return 0, expected, got, "emitted an artifact where the checker refuses the input"
    if got["sha256"] == expected["sha256"]:
        return 1, expected, got, "rendered bytes equal the independent expected digest"
    return 0, expected, got, "rendered digest differs from the expected bytes"


def _gate(files, output, work, checkpoint_script, meta):
    _write_fixture(files, work)
    state = Path(work, "state.json")
    result = _run([sys.executable, str(checkpoint_script), "gate", str(state)])
    if result.returncode not in (0, 1):
        raise ScorerError(f"gate did not answer (rc={result.returncode}): {result.stderr.strip()}")
    expected_pass = result.returncode == 0
    if expected_pass != bool(meta.get("expect_pass")):
        raise ScorerError("the authored expectation disagrees with the gate verdict")
    expected = {"verdict": "pass" if expected_pass else "blocked",
                "open": [] if expected_pass else list(meta["open"])}
    if not isinstance(output, dict):
        return 0, expected, {"verdict": "unparseable"}, "no JSON object"
    verdict = output.get("verdict")
    open_ids = output.get("open")
    if verdict not in ("pass", "blocked") or not isinstance(open_ids, list) \
            or any(not isinstance(x, str) for x in open_ids):
        return 0, expected, output, "verdict/open have the wrong shape"
    got = {"verdict": verdict, "open": sorted(open_ids)}
    if got["verdict"] == expected["verdict"] and got["open"] == sorted(expected["open"]):
        return 1, expected, got, "verdict and open criteria match the gate"
    return 0, expected, got, "verdict or open criteria differ from the gate"


def _sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recover_json(text):
    """Recover exactly one JSON value from a reply, tolerating fences and prose.

    Returns the value, or raises ValueError. Two values in one reply are ambiguous
    and therefore refused instead of guessing which one the model meant.
    """
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty reply")
    fenced = stripped.split("```")
    candidates = [stripped] + [part.split("\n", 1)[-1] if part.split("\n", 1)[0].strip().lower()
                               in ("json", "javascript", "js") else part
                               for part in (fenced[1::2] if len(fenced) > 2 else [])]
    decoders = [json.JSONDecoder()]
    for candidate in candidates:
        for start in [i for i, ch in enumerate(candidate) if ch in "[{"]:
            try:
                value, end = decoders[0].raw_decode(candidate, start)
            except ValueError:
                continue
            if candidate[end:].strip(" \t\r\n.") == "":
                return value
    raise ValueError("no single JSON value in the reply")


def evaluate(case, output_text, *, longhaul=None, makeextreme=None):
    """Score one reply. `longhaul` is the checkout that owns the gate checker.

    ``makeextreme`` is accepted for symmetry with the runner and recorded by the
    caller, but scoring does not need it: the digest checker is in this repository.
    """
    if longhaul is None:
        raise ScorerError("--longhaul is required for the gate oracle")
    digest_script = FLOWLORE / "examples" / "release-digest" / "digest.py"
    checkpoint_script = Path(longhaul, "scripts", "checkpoint.py")
    try:
        output = recover_json(output_text)
    except ValueError as exc:
        return {"score": 0, "detail": f"unparseable: {exc}", "expected": None, "got": None,
                "failure": "unparseable"}
    with tempfile.TemporaryDirectory(prefix="lmb-score-") as work:
        if case["scenario"] == "digest":
            score, expected, got, detail = _digest(case["files"], output, work, digest_script)
        elif case["scenario"] == "gate":
            score, expected, got, detail = _gate(case["files"], output, work, checkpoint_script,
                                                 case["meta"])
        else:
            raise ScorerError(f"unknown scenario {case['scenario']!r}")
    return {"score": score, "expected": expected, "got": got, "detail": detail,
            "failure": None if score else "wrong_answer"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Score one recorded reply against a case")
    parser.add_argument("case_id")
    parser.add_argument("reply", type=Path)
    parser.add_argument("--longhaul", type=Path, required=True)
    args = parser.parse_args()
    import scenarios
    cases = scenarios.build()
    print(json.dumps(evaluate(cases[args.case_id], args.reply.read_text(), longhaul=args.longhaul),
                     indent=1))
