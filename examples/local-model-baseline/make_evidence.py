#!/usr/bin/env python3
"""Turn a run directory into a compact, reviewable evidence file.

The raw run directory stays outside the repository: it holds every prompt and reply
and the local paths of the checkouts. This script keeps the pinned conditions, the
per-case outcomes, the denominators and the counts, and drops reply bodies except
for a few failing examples. It never writes a path from the machine it ran on.
"""
import argparse
import json
import platform
import sys
from pathlib import Path


def sha(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="directory holding results.json")
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--model-digest", required=True)
    parser.add_argument("--ollama", default="0.40.13")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--examples", type=int, default=3)
    args = parser.parse_args()

    raw = json.loads((args.run / "results.json").read_text())
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import scenarios
    frozen = scenarios.build()

    def input_sha(case_id):
        case = frozen[case_id]
        name = "release.json" if case["scenario"] == "digest" else "state.json"
        return sha(case["files"][name])

    cases = raw["cases"]
    rows = []
    examples = []
    for row in cases:
        rows.append({
            "case": row["case"], "scenario": row["scenario"], "split": row["split"],
            "category": row["category"], "policy": row["policy"],
            "final_verified": row["final_verified"], "requests": row["requests"],
            "budget_exhausted": row["budget_exhausted"],
            "faults_injected": row["faults"],
            "attempt_scores": [a["score"] for a in row["attempts"]],
            "transport": [a["transport"] for a in row["attempts"]],
            "final_expected": row["attempts"][-1].get("expected"),
            "final_got": row["attempts"][-1].get("got"),
            "run": {"case_id": row["case"], "model": raw["model"]["name"],
                    "input_sha256": input_sha(row["case"])},
        })
        if not row["final_verified"] and len(examples) < args.examples:
            last = row["attempts"][-1]
            examples.append({
                "case": row["case"], "policy": row["policy"],
                "expected": last.get("expected"), "got": last.get("got"),
                "detail": last.get("detail"), "reply_excerpt": (last.get("reply") or "")[:400],
            })

    evidence = {
        "version": 1,
        "generated_at": "2026-11-08",
        "scope": ("One model, one runner, one machine. The case set and this file describe "
                  "behaviour here; they do not establish behaviour for other models, runners "
                  "or live APIs."),
        "model": {**raw["model"], "digest": args.model_digest,
                  "digest_source": ("/api/tags via the Makeextreme adapter; the digest was "
                                    "resolved after this run, whose per-request records were "
                                    "written before the adapter's tags call was fixed to use GET")},
        "runner": {"name": "makeextreme.model_runner.py", "ollama": args.ollama,
                   "transport": "HTTP to a loopback Ollama server, one request at a time",
                   "concurrency": 1},
        "environment": {"platform": platform.system(), "machine": platform.machine(),
                        "python": platform.python_version()},
        "case_set": raw["scenario_set"],
        "budget": raw["budget"],
        "summary": raw["summary"],
        "cases": rows,
        "failing_examples": examples,
        "counts": {
            "case_policy_rows": len(rows),
            "verified_rows": sum(r["final_verified"] for r in rows),
            "denominator": len(rows),
        },
    }
    if args.recovery:
        evidence["recovery"] = json.loads(args.recovery.read_text())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=1) + "\n")
    print(f"wrote {args.out} ({len(rows)} case-policy rows, "
          f"{evidence['counts']['verified_rows']}/{evidence['counts']['denominator']} verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
