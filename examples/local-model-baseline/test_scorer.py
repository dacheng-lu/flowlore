#!/usr/bin/env python3
"""Deterministic tests for the local-model case set and its scorer. No model needed.

Run from the FlowLore checkout with a sibling Longhaul checkout:

    python3 examples/local-model-baseline/test_scorer.py --longhaul ../longhaul

Each case's golden answer must score 1 and at least one plausible wrong answer
must score 0, so a later change cannot quietly make the scorer accept everything.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scenarios  # noqa: E402
import scorer  # noqa: E402


def golden(case):
    if case["scenario"] == "digest":
        try:
            rows = json.loads(case["files"]["release.json"])
        except ValueError:
            return '{"refuse": "malformed input"}'
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "release.json")
            p.write_text(case["files"]["release.json"])
            ok = subprocess.run([sys.executable, str(scorer.FLOWLORE / "examples" / "release-digest" / "digest.py"),
                                 "validate", str(p)], capture_output=True).returncode == 0
        return json.dumps(rows) if ok else '{"refuse": "invalid release list"}'
    return json.dumps({"verdict": "pass" if case["meta"]["expect_pass"] else "blocked",
                       "open": case["meta"]["open"]})


def wrong(case):
    if case["scenario"] == "digest":
        text = case["files"]["release.json"]
        try:
            rows = json.loads(text)
        except ValueError:
            rows = None
        if isinstance(rows, list) and rows:
            if len(rows) > 1:
                return json.dumps(rows[:1])        # silently drop records
            mut = dict(rows[0])
            mut["title"] = "a different title"    # silently rewrite a copied value
            return json.dumps([mut])
        return "[]"                                # claim a clean empty digest
    return json.dumps({"verdict": "pass" if not case["meta"]["expect_pass"] else "blocked",
                       "open": [] if not case["meta"]["expect_pass"] else ["C1"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--longhaul", type=Path, required=True)
    args = parser.parse_args()
    cases = scenarios.build()
    assert len(cases) == 24, len(cases)
    splits = {"dev": 0, "heldout": 0}
    for case in cases.values():
        splits[case["split"]] += 1
    assert splits == {"dev": 12, "heldout": 12}, splits
    for case in cases.values():
        good = scorer.evaluate(case, golden(case), longhaul=args.longhaul)
        assert good["score"] == 1, (case["id"], good)
        bad = scorer.evaluate(case, wrong(case), longhaul=args.longhaul)
        assert bad["score"] == 0, (case["id"], bad)
        assert bad["expected"] is not None, case["id"]
    # Packaging tolerance must not turn into content tolerance.
    case = cases["g-pass"]
    fenced = "Here is the audit:\n```json\n" + golden(case) + "\n```\n"
    assert scorer.evaluate(case, fenced, longhaul=args.longhaul)["score"] == 1
    two = golden(case) + "\n" + json.dumps({"verdict": "blocked", "open": ["C1"]})
    assert scorer.evaluate(case, two, longhaul=args.longhaul)["score"] == 0
    assert scorer.evaluate(case, "", longhaul=args.longhaul)["score"] == 0
    print(f"PASS: {len(cases)} cases ({splits['dev']} dev, {splits['heldout']} heldout); "
          f"golden=1 and a wrong answer=0 for every case")
    return 0


if __name__ == "__main__":
    sys.exit(main())
