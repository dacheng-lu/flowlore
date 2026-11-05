import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('tenon', Path(__file__).with_name('tenon.py'))
tenon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tenon)


def card(data=b'known'):
    return {'schema': 'tenon/0', 'task': 'task', 'run': 'run-1', 'stage': 'render',
            'recipe': 'digest', 'result': 'pass', 'check': 'exact fixture match',
            'sha256': hashlib.sha256(data).hexdigest(),
            'revisions': {k: 'a' * 40 for k in ('flowlore', 'longhaul', 'makeextreme')}}


class TenonTests(unittest.TestCase):
    def test_match_never_asserts_identity_or_check_truth(self):
        status, reason = tenon.inspect(card(), b'known')
        self.assertEqual(status, 'match')
        self.assertIn('unverified', reason)
        self.assertEqual(tenon.inspect(card(), b'changed')[0], 'mismatch')

    def test_missing_or_unsupported_fields_are_unknown(self):
        for mutate in ('schema', 'check', 'run', 'revisions', 'result', 'sha256'):
            value = card()
            del value[mutate]
            with self.subTest(mutate=mutate):
                self.assertEqual(tenon.inspect(value, b'known')[0], 'unknown')
        bad = card()
        bad['schema'] = 'tenon/2'
        self.assertEqual(tenon.inspect(bad, b'known')[0], 'unknown')

    def test_read_only_view_reports_unverified_manual_linkage(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'card.json').write_text(json.dumps(card()))
            (p / 'artifact').write_bytes(b'known')
            (p / 'journal').write_text('{"ev":"start"}\n{"ev":"end"}\n')
            (p / 'checkpoint').write_text('{"evidence":[{}]}')
            before = {x.name: x.read_bytes() for x in p.iterdir()}
            result = tenon.summary(p / 'card.json', p / 'artifact', p / 'journal', p / 'checkpoint')
            self.assertEqual(result['artifact'], 'match')
            self.assertEqual(result['journal_event_counts'], {'start': 1, 'end': 1})
            self.assertEqual(result['checkpoint_evidence_count'], 1)
            self.assertIn('not authenticated', result['linkage'])
            self.assertEqual(before, {x.name: x.read_bytes() for x in p.iterdir()})


if __name__ == '__main__':
    unittest.main()
