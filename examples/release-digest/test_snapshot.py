import hashlib
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import reproduce_snapshot as replay

class SavedSnapshot(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'evidence'
        shutil.copytree(replay.EVIDENCE,self.root)

    def test_public_response_roundtrip(self):
        result=replay.validate(self.root)
        self.assertFalse(result['complete'])
        self.assertEqual(len(result['releases']),3)

    def test_tampering_raw_is_rejected(self):
        (self.root/'raw.json.gz').write_bytes(gzip.compress(b'[]',mtime=0))
        with self.assertRaisesRegex(ValueError,'hash mismatch'): replay.validate(self.root)

    def test_tampering_normalized_is_rejected(self):
        data=json.loads((self.root/'snapshot.json').read_text())
        data['releases'][0]['tag']='v999'
        (self.root/'snapshot.json').write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'differs'): replay.validate(self.root)

    def test_missing_page_cannot_be_claimed_complete(self):
        p=self.root/'capture.json';data=json.loads(p.read_text());data['complete']=True;p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'scope'): replay.validate(self.root)

    def test_empty_input_is_refused_even_with_updated_hash(self):
        raw=b'[]';(self.root/'raw.json.gz').write_bytes(gzip.compress(raw,mtime=0))
        p=self.root/'capture.json';d=json.loads(p.read_text());d['raw_sha256']=hashlib.sha256(raw).hexdigest();p.write_text(json.dumps(d))
        with self.assertRaises(ValueError): replay.validate(self.root)

    def test_independent_expected_detects_false_output(self):
        expected=self.root/'expected.md';expected.write_text('invented release\n')
        data=json.loads((self.root/'snapshot.json').read_text())
        rows=[dict(repo=x['repo'],id=x['id'],tag=x['tag'],title='Release',url=x['url']) for x in data['releases']]
        fixture=self.root/'input.json';fixture.write_text(json.dumps(rows))
        import digest
        output=self.root/'out.md';output.write_text(digest.render(digest.entries(fixture)))
        p=subprocess.run([sys.executable,str(HERE/'digest.py'),'check',str(fixture),'--output',str(output),'--expected',str(expected)],capture_output=True)
        self.assertNotEqual(p.returncode,0)

if __name__=='__main__': unittest.main()
