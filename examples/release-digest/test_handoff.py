"""Exercise the narrow handoff against actual runner/checkpoint artifacts."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import verify_handoff

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'evidence/cli-snapshot'

class Handoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.original=cls.root/'original'
        cmd=[sys.executable,str(HERE/'integration.py'),'--makeextreme',str(MX),'--longhaul',str(LH),
             '--live-snapshot',str(SOURCE/'snapshot.json'),'--expected',str(SOURCE/'expected.md'),
             '--evidence-dir',str(cls.original)]
        subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=90)
        cls.revisions=json.loads((cls.original/'card.json').read_text())['revisions']
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.bundle=Path(self.tmp.name)/'bundle';shutil.copytree(self.original,self.bundle)
        self.source=Path(self.tmp.name)/'source';shutil.copytree(SOURCE,self.source)
    def check(self,revisions=None):
        r=revisions or self.revisions
        return verify_handoff.verify(self.bundle,self.source,LH,r['flowlore'],r['longhaul'],r['makeextreme'])
    def test_real_handoff(self): self.assertEqual(self.check()['result'],'consistent')
    def test_changed_report_refused(self):
        (self.bundle/'digest.md').write_text('altered')
        with self.assertRaises(ValueError):self.check()
    def test_changed_input_refused(self):
        (self.bundle/'sanitized-input.json').write_text('[]')
        with self.assertRaises(ValueError):self.check()
    def test_wrong_peer_revision_refused(self):
        r=dict(self.revisions,makeextreme='a'*40)
        with self.assertRaises(ValueError):self.check(r)
    def test_changed_source_refused(self):
        (self.source/'expected.md').write_text('wrong')
        with self.assertRaises(ValueError):self.check()
    def test_missing_journal_refused(self):
        (self.bundle/'journal.jsonl').unlink()
        with self.assertRaises(OSError):self.check()
    def test_unsupported_card_refused(self):
        p=self.bundle/'card.json';c=json.loads(p.read_text());c['schema']='tenon/999';p.write_text(json.dumps(c))
        with self.assertRaises(ValueError):self.check()
    def test_checkpoint_must_pass(self):
        p=self.bundle/'longhaul.json';s=json.loads(p.read_text());s['acceptance'][0]['status']='pending';p.write_text(json.dumps(s))
        with self.assertRaises(ValueError):self.check()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--makeextreme',required=True,type=Path);p.add_argument('--longhaul',required=True,type=Path)
    args=p.parse_args();MX=args.makeextreme.resolve();LH=args.longhaul.resolve();unittest.main(argv=[sys.argv[0]])
