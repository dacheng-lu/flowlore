#!/usr/bin/env python3
"""Offline direct tests; does not run Promptfoo or call a model."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import adapter
import synthetic_provider
import replay_provider
import validate_results


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get("FLOWLORE_LONGHAUL"):
            raise RuntimeError("set FLOWLORE_LONGHAUL to the pinned checkout")
        cls.cases = adapter.integrity()
        with patch.dict(os.environ, {"FLOWLORE_SPLIT": "all"}):
            cls.rows = adapter.generate_tests()

    def context(self, row):
        return {"vars": row["vars"], "prompt": row["vars"]["case_prompt"]}

    def test_all_fixtures_against_real_oracles(self):
        self.assertEqual(len(self.rows), 24)
        for row in self.rows:
            context = self.context(row)
            with self.subTest(case=row["vars"]["case_id"]):
                for mode, expected in (("good", True), ("wrong", False)):
                    with patch.dict(os.environ, {"FLOWLORE_SYNTHETIC": mode}):
                        context["vars"]["runtime_binding"] = adapter.runtime_binding()
                        output = synthetic_provider.call_api(context["prompt"], {}, context)["output"]
                        result = adapter.get_assert(output, context)
                        self.assertEqual(result["pass"], expected, result)
                        self.assertTrue(result["reason"].startswith("MODEL_RESULT: "), result)
                context["vars"]["runtime_binding"] = adapter.runtime_binding()

    def test_bindings_empty_and_errors(self):
        row = self.rows[0]
        context = self.context(row)
        self.assertEqual(adapter.get_assert("", context)["reason"], "MODEL_FAILURE: empty_answer")
        with patch.dict(os.environ, {"FLOWLORE_LONGHAUL": "/missing/checkout"}):
            self.assertTrue(adapter.get_assert("not json", context)["reason"].startswith(adapter.ERROR))
        changed = dict(context, prompt=context["prompt"] + " ")
        self.assertTrue(adapter.get_assert("{}", changed)["reason"].startswith(adapter.ERROR))
        self.assertTrue(adapter.get_assert(None, context)["reason"].startswith(adapter.ERROR))
        with patch.object(adapter, "probe", side_effect=adapter.AdapterError("checker crashed")):
            self.assertTrue(adapter.get_assert('{"refuse":"x"}', context)["reason"].startswith(adapter.ERROR))

    def test_checker_crashes_not_refusals(self):
        class P:
            returncode, stdout, stderr = 1, "", "Traceback: crash"
        with self.assertRaises(adapter.AdapterError):
            adapter.protocol([sys.executable, "/x/digest.py", "validate", "/tmp/input"], P())
        with self.assertRaises(adapter.AdapterError):
            adapter.protocol([sys.executable, "/x/checkpoint.py", "gate", "/tmp/state"], P())

    def test_explicit_raw_replay(self):
        case = self.cases["d-valid-3"]
        row = next(r for r in self.rows if r["vars"]["case_id"] == case["id"])
        context = self.context(row)
        reply = synthetic_provider.call_api(context["prompt"], {}, context)["output"]
        attempt = {"case": case["id"], "policy": "A", "index": 1, "fault": None, "transport": "ok", "reply": reply,
                   "reply_sha256": adapter.sha(reply)[:16], "model_digest": "synthetic-digest",
                   "prompt_sha256": adapter.sha(context["prompt"])[:16],
                   "run": {"case_id": case["id"], "model": "fixture-not-model",
                           "input_sha256": adapter.sha(adapter.input_text(case))}}
        record = {"scenario_set": {},
                  "model": {"name": "fixture-not-model", "digest": "synthetic-digest"},
                  "cases": [{"case": case["id"], "policy": "A", "scenario": case["scenario"], "split": case["split"], "attempts": [attempt]}]}
        record["scenario_set"] = {"cases_json_sha256": adapter.sha((adapter.BASE / "cases.json").read_text())[:16],
                                  "scenarios_sha256": adapter.sha((adapter.BASE / "scenarios.py").read_text())[:16]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "results.json")
            def save():
                path.write_text(json.dumps(record))
            save()
            env = {"FLOWLORE_RESULTS": str(path), "FLOWLORE_POLICY": "A", "FLOWLORE_ATTEMPT": "1"}
            with patch.dict(os.environ, env):
                self.assertEqual(replay_provider.call_api(context["prompt"], {}, context)["output"], reply)
                attempt["reply"] = ""
                attempt["reply_sha256"] = adapter.sha("")[:16]
                save()
                self.assertEqual(replay_provider.call_api(context["prompt"], {}, context)["output"], "")
                attempt["reply"] = "tampered"
                save()
                with self.assertRaisesRegex(ValueError, "reply hash mismatch"):
                    replay_provider.call_api(context["prompt"], {}, context)
                attempt["reply"] = ""
                attempt["case"] = "d-valid-1"
                save()
                with self.assertRaisesRegex(ValueError, "case or policy mismatch"):
                    replay_provider.call_api(context["prompt"], {}, context)
                attempt["case"] = case["id"]
                attempt["model_digest"] = "other-digest"
                save()
                with self.assertRaisesRegex(ValueError, "model digest mismatch"):
                    replay_provider.call_api(context["prompt"], {}, context)
                attempt["model_digest"] = "synthetic-digest"
                attempt["fault"] = "wrong_input"
                save()
                with self.assertRaisesRegex(ValueError, "faulted"):
                    replay_provider.call_api(context["prompt"], {}, context)
                attempt["fault"] = None
                attempt["prompt_sha256"] = "tampered"
                save()
                with self.assertRaisesRegex(ValueError, "binding mismatch"):
                    replay_provider.call_api(context["prompt"], {}, context)
                with patch.dict(os.environ, {"FLOWLORE_ATTEMPT": "2"}):
                    with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                        replay_provider.call_api(context["prompt"], {}, context)
                evidence = adapter.BASE / "evidence" / "local-model-baseline-2026-11-08.json"
                with patch.dict(os.environ, {"FLOWLORE_RESULTS": str(evidence)}):
                    with self.assertRaisesRegex(ValueError, "FLOWLORE_REPLAY_ERROR"):
                        replay_provider.call_api(context["prompt"], {}, context)

    def test_result_validator_fails_closed(self):
        rows = []
        for row in self.rows:
            context = self.context(row)
            with patch.dict(os.environ, {"FLOWLORE_SYNTHETIC": "good"}):
                output = synthetic_provider.call_api(context["prompt"], {}, context)["output"]
            grade = adapter.get_assert(output, context)
            component = dict(grade, assertion={"type": "python", "value": "file://adapter.py:get_assert"})
            rows.append({"vars": row["vars"], "provider": {"id": "synthetic", "config": {}}, "prompt": {"raw": context["prompt"]},
                         "response": {"output": output}, "failureReason": 0,
                         "success": grade["pass"], "score": grade["score"],
                         "gradingResult": {"pass": grade["pass"], "score": grade["score"],
                                           "componentResults": [component]}})
        record = {"evalId": "synthetic-test", "metadata": {"promptfooVersion": "0.125.1"}, "results": {"results": rows}}
        self.assertEqual(validate_results.validate(record, "all"), (24, 24, "synthetic"))
        # Promptfoo also sets row.error for ordinary failed assertions.
        wrong_row = rows[0]
        wrong_context = self.context(self.rows[0])
        wrong = adapter.get_assert("", wrong_context)
        wrong_row["response"]["output"] = ""
        wrong_row.update(failureReason=1, success=False, score=0, error=wrong["reason"])
        wrong_row["gradingResult"] = {"pass": False, "score": 0, "reason": wrong["reason"],
            "componentResults": [dict(wrong, assertion={"type": "python", "value": "file://adapter.py:get_assert"})]}
        self.assertEqual(validate_results.validate(record, "all"), (23, 24, "synthetic"))
        good_output = synthetic_provider.call_api(wrong_context["prompt"], {}, wrong_context)["output"]
        good = adapter.get_assert(good_output, wrong_context)
        wrong_row["response"]["output"] = good_output
        wrong_row.update(failureReason=0, success=True, score=1)
        wrong_row.pop("error")
        wrong_row["gradingResult"] = {"pass": True, "score": 1, "reason": "All assertions passed",
            "componentResults": [dict(good, assertion={"type": "python", "value": "file://adapter.py:get_assert"})]}
        first = rows[0]
        original = first["response"]["output"]
        first["response"]["output"] = "not valid JSON"
        with self.assertRaisesRegex(ValueError, "inconsistent assertion failure state|differs from the original scorer"):
            validate_results.validate(record, "all")
        first["response"]["output"] = original
        original_reason = first["gradingResult"]["componentResults"][0]["reason"]
        first["gradingResult"]["componentResults"][0]["reason"] = adapter.ERROR + "crash"
        with self.assertRaisesRegex(ValueError, "adapter or checker error"):
            validate_results.validate(record, "all")
        first["gradingResult"]["componentResults"][0]["reason"] = original_reason
        first["gradingResult"]["componentResults"].append({})
        with self.assertRaisesRegex(ValueError, "extra"):
            validate_results.validate(record, "all")
        first["gradingResult"]["componentResults"].pop()
        rows[1]["provider"] = {"id": "another-model", "config": {}}
        with self.assertRaisesRegex(ValueError, "multiple providers"):
            validate_results.validate(record, "all")
        rows[1]["provider"] = {"id": "synthetic", "config": {}}
        rows.pop()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            validate_results.validate(record, "all")



if __name__ == "__main__":
    unittest.main(verbosity=2)
