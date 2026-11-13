#!/usr/bin/env python3
"""A request that never answered is not a wrong answer."""
import unittest

import run


def row(transport, score):
    return {"case": "c", "scenario": "gate", "split": "dev", "category": "x", "policy": "A",
            "final_verified": False, "requests": 1, "faults": [], "budget_exhausted": False,
            "attempts": [{"transport": transport, "score": score, "fault": None,
                          "got": None, "expected": None, "failure": None,
                          "verdict_correct": None,
                          "tokens": {"eval": None, "prompt": None}, "wall_seconds": 0.0}]}


class Summary(unittest.TestCase):
    def test_transport_errors_are_not_counted_as_wrong_answers(self):
        out = run.summarize([row("transport_error", 0), row("timeout", 0),
                             row("killed_by_harness", 0), row("ok", 0), row("ok", 1)], {})
        bucket = out["all"]
        self.assertEqual(bucket["wrong_answers"], 1)
        self.assertEqual(bucket["answered"], 2)
        self.assertEqual(bucket["transport_errors"], 1)
        self.assertEqual(bucket["timeouts"], 1)
        self.assertEqual(bucket["harness_kills"], 1)

    def test_a_dead_endpoint_reports_no_model_errors(self):
        out = run.summarize([row("transport_error", 0) for _ in range(4)], {})
        self.assertEqual(out["all"]["wrong_answers"], 0)
        self.assertEqual(out["all"]["answered"], 0)


if __name__ == "__main__":
    unittest.main()
