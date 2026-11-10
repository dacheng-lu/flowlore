#!/usr/bin/env python3
"""Acceptance regression for the bounded comparison; requires sibling checkouts."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent


class ComparisonTest(unittest.TestCase):
    def test_same_acceptance_and_recovery(self):
        result = subprocess.run(
            [sys.executable, str(HERE / 'compare_recovery.py'),
             '--makeextreme', str(ROOT / 'makeextreme'), '--longhaul', str(ROOT / 'longhaul')],
            capture_output=True, text=True, timeout=90, check=True)
        cases = {(x['scenario'], x['condition']): x for x in json.loads(result.stdout)['results']}
        self.assertEqual(len(cases), 12)
        conditions = ('plain', 'runner', 'anchored')
        self.assertEqual([cases['repeat', c]['stage_starts'] for c in conditions], [2, 1, 1])
        self.assertEqual([cases['tamper-output', c]['stage_starts'] for c in conditions], [2, 2, 2])
        for c in conditions:
            self.assertTrue(cases['invalid-source', c]['weak_check_accepted'])
            self.assertFalse(cases['invalid-source', c]['accepted'])
        self.assertFalse(any(row['false_accept'] or row['false_reject'] for row in cases.values()))


if __name__ == '__main__': unittest.main()
