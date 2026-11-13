"""Synthetic test doubles only: these are never model outputs or historical data."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import scenarios
import test_scorer


def call_api(prompt, options, context):
    mode = os.environ.get("FLOWLORE_SYNTHETIC", "good")
    if mode not in ("good", "wrong"):
        raise ValueError("FLOWLORE_SYNTHETIC must be good or wrong")
    case = scenarios.build()[context["vars"]["case_id"]]
    response = test_scorer.golden(case) if mode == "good" else test_scorer.wrong(case)
    return {"output": response}
