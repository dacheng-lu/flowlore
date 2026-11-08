import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import validate_recipes as validator

class RecipeContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.recipe={'id':'sample','title':'Sample','type':'recipe','summary':'Summary','path':'recipes/a.md','input':'Input','output':'Output','status':'draft','sources':['source']}
        self.catalog={'entries':[{'id':'source','type':'source'},self.recipe]}
    def test_draft_passes(self): self.assertEqual(validator.validate(self.catalog,self.root),[])
    def test_missing_source_fails(self):
        self.recipe['sources']=['unknown'];self.assertIn('sample:',validator.validate(self.catalog,self.root)[0])
    def test_verified_without_evidence_fails(self):
        self.recipe['status']='verified';self.assertIn('sample:',validator.validate(self.catalog,self.root)[0])
    def test_artifact_must_exist_and_match(self):
        self.recipe['status']='verified';(self.root/'evidence/recipes').mkdir(parents=True)
        p=self.root/'artifact.txt';p.write_text('result')
        manifest={'schema':1,'recipe':'sample','revision':'a'*40,'components':{'runner':'b'*40},'command':'python replay.py','artifacts':[{'path':'artifact.txt','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}
        (self.root/'evidence/recipes/sample.json').write_text(json.dumps(manifest))
        self.assertEqual(validator.validate(self.catalog,self.root),[])
        p.write_text('changed');self.assertIn('hash mismatch',validator.validate(self.catalog,self.root)[0])
        manifest['artifacts'][0]['path']='../escape';(self.root/'evidence/recipes/sample.json').write_text(json.dumps(manifest))
        self.assertIn('path',validator.validate(self.catalog,self.root)[0])

if __name__=='__main__':unittest.main()
