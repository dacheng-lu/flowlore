#!/usr/bin/env python3
"""Reject incomplete/errored Promptfoo JSON before interpreting any model score.

Uses the 0.125.1 export schema (source-inspected; end-to-end run not verified).
"""
import argparse
import json
import sys
from pathlib import Path

import adapter

REDACTED = "[REDACTED]"
REDACTED_FIELDS = set()


def reasons(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "reason" and isinstance(item, str):
                yield item
            elif isinstance(item, (dict, list)):
                yield from reasons(item)
    elif isinstance(value, list):
        for item in value:
            yield from reasons(item)


def validate(doc, split):
    if not isinstance(doc, dict) or doc.get("metadata", {}).get("promptfooVersion") != "0.125.1":
        raise ValueError("missing or unexpected Promptfoo version")
    if not isinstance(doc.get("evalId"), str) or not doc["evalId"]:
        raise ValueError("missing evaluation ID")
    rows = doc.get("results", {}).get("results")
    if not isinstance(rows, list):
        raise ValueError("missing Promptfoo results array")
    cases = adapter.integrity()
    expected = {case["id"] for case in adapter.selected_cases(cases, split)}
    seen = set()
    passed = 0
    provider = None
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("vars"), dict):
            raise ValueError("malformed result row")
        this_provider = row.get("provider")
        if not isinstance(this_provider, dict) or not isinstance(this_provider.get("id"), str) or not this_provider["id"]:
            raise ValueError("missing provider identity")
        if provider is None:
            provider = this_provider
        elif provider != this_provider:
            raise ValueError("multiple providers in one evaluation")
        variables = row["vars"]
        cid = variables.get("case_id")
        if cid not in expected or cid in seen:
            raise ValueError("unexpected or duplicated case id")
        seen.add(cid)
        case = cases[cid]
        # promptfoo's export sanitizer redacts values that look like credentials,
        # which catches 64-char/40-char hex: input_sha256, runtime_binding and the
        # Longhaul revision arrive as "[REDACTED]". They are re-derived from the
        # frozen cases and the checkout below, so the prompt check stays the
        # authoritative binding; redactions are counted and reported.
        def exported(name, expected_value):
            actual = variables.get(name)
            if actual == REDACTED:
                REDACTED_FIELDS.add(name)
                return True
            return actual == expected_value

        if (not adapter.prompt_matches(variables.get("case_prompt"), adapter.prompt_for(case))
                or not exported("input_sha256", adapter.sha(adapter.input_text(case)))
                or not exported("longhaul_rev", adapter.requested_revision())
                or not exported("runtime_binding", adapter.runtime_binding())
                or not isinstance(row.get("prompt"), dict)
                or not adapter.prompt_matches(row["prompt"].get("raw"), adapter.prompt_for(case))):
            raise ValueError("prompt or input binding mismatch: " + cid)
        if (row.get("failureReason") not in (0, 1)
                or not isinstance(row.get("response"), dict)
                or not isinstance(row["response"].get("output"), str)):
            raise ValueError("provider or transport error: " + cid)
        if "replay_provider.py" in provider["id"]:
            import replay_provider
            replay = replay_provider.call_api(row["prompt"]["raw"], {}, {"vars": variables})
            if (replay["output"] != row["response"]["output"]
                    or replay["metadata"]["flowlore_replay"] != row["response"].get("metadata", {}).get("flowlore_replay")):
                raise ValueError("raw replay binding mismatch: " + cid)
        grade = row.get("gradingResult")
        components = grade.get("componentResults") if isinstance(grade, dict) else None
        if not isinstance(components, list) or len(components) != 1 or not isinstance(components[0], dict):
            raise ValueError("missing or extra FlowLore assertion: " + cid)
        component = components[0]
        if (component.get("assertion", {}).get("type") != "python"
                or component.get("assertion", {}).get("value") != "file://adapter.py:get_assert"):
            raise ValueError("unexpected assertion type: " + cid)
        found = list(reasons(grade))
        if any("empty_answer" in reason for reason in found):
            raise ValueError("provider returned an empty answer (facility error): " + cid)
        if any(adapter.ERROR in reason for reason in found):
            raise ValueError("adapter or checker error: " + cid)
        # Do not trust a saved score or a marker alone: re-run the frozen scorer
        # over the exact saved output and compare the complete assertion result.
        # The export may have redacted binding vars (see above); recheck against the
        # frozen values. The delivered prompt itself was verified against the case.
        recheck_vars = dict(variables, case_prompt=adapter.prompt_for(case),
                            input_sha256=adapter.sha(adapter.input_text(case)),
                            longhaul_rev=adapter.requested_revision(),
                            runtime_binding=adapter.runtime_binding())
        fresh = adapter.get_assert(row["response"]["output"], {"vars": recheck_vars, "prompt": row["prompt"]["raw"]})
        if fresh["reason"].startswith(adapter.ERROR):
            raise ValueError("adapter or checker error during recheck: " + cid)
        if ((fresh["pass"] and (row.get("failureReason") != 0 or row.get("error")))
                or (not fresh["pass"] and (row.get("failureReason") != 1
                                            or row.get("error") != grade.get("reason")))):
            raise ValueError("inconsistent assertion failure state: " + cid)
        if (component.get("reason") != fresh["reason"] or component.get("pass") != fresh["pass"]
                or component.get("score") != fresh["score"] or grade.get("pass") != fresh["pass"]
                or grade.get("score") != fresh["score"] or row.get("success") != fresh["pass"]
                or row.get("score") != fresh["score"]):
            raise ValueError("saved score or assertion differs from the original scorer: " + cid)
        passed += row["success"]
    if seen != expected:
        raise ValueError(f"incomplete result: expected {len(expected)} distinct cases, got {len(seen)}")
    return passed, len(seen), provider["id"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--split", choices=("dev", "heldout", "all"), required=True)
    args = parser.parse_args()
    try:
        passed, count, provider = validate(json.loads(args.json_file.read_text(encoding="utf-8")), args.split)
    except (OSError, ValueError, TypeError, KeyError, adapter.AdapterError) as exc:
        print("INVALID EVALUATION: " + str(exc), file=sys.stderr)
        return 2
    print(f"COMPLETE: {passed}/{count} passed; provider={provider}; split={args.split}; Longhaul={adapter.requested_revision()}")
    if REDACTED_FIELDS:
        print(f"NOTE: export redacted {len(REDACTED_FIELDS)} binding field(s) "
              f"({', '.join(sorted(REDACTED_FIELDS))}); re-derived from frozen cases + checkout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
