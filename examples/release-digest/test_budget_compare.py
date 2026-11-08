import argparse
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE=Path(__file__).resolve().parent
class BudgetWorkload(unittest.TestCase):
    def test_paired_real_subprocesses(self):
        p=subprocess.run([sys.executable,str(HERE/'budget_compare.py'),'--makeextreme',str(MX)],capture_output=True,text=True,check=True,timeout=30)
        data=json.loads(p.stdout)['results']
        self.assertTrue(data['first_success']['baseline']['verified'])
        self.assertTrue(data['first_success']['reserve']['verified'])
        self.assertTrue(data['retry_success']['reserve']['verified'])
        self.assertEqual(data['consecutive_failures']['baseline']['attempts'],4)
        self.assertEqual(data['consecutive_failures']['reserve']['attempts'],3)
        self.assertTrue(data['late_success']['baseline']['unverified'])
        self.assertFalse(data['late_success']['reserve']['unverified'])
        self.assertFalse(data['late_success']['reserve']['verified'])
        for pair in data.values():
            for row in pair.values(): self.assertGreaterEqual(row['wall_seconds'],0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--makeextreme',required=True,type=Path);args=p.parse_args();MX=args.makeextreme.resolve();unittest.main(argv=[sys.argv[0]])
