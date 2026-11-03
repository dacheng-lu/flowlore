import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('digest', HERE / 'digest.py')
digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(digest)


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'input.json'
        self.rows = json.loads((HERE / 'releases.json').read_text())

    def load(self, data):
        self.path.write_text(json.dumps(data))
        return digest.entries(self.path)

    def test_duplicate_removed_and_expected_output_matches(self):
        result = self.load(self.rows)
        self.assertEqual(len(result), 2)
        self.assertEqual(digest.render(result), (HERE / 'expected.md').read_text())

    def test_missing_url_and_conflicting_duplicate_are_rejected(self):
        for mutate in ('missing', 'conflict'):
            rows = copy.deepcopy(self.rows)
            if mutate == 'missing':
                del rows[0]['url']
            else:
                rows[1]['title'] = 'Different title'
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.load(rows)

    def test_rejects_link_injection_and_unrelated_urls(self):
        for url in ('https://evil.example/release', 'https://github.com/sample/other/releases/tag/v1.0',
                    'javascript:alert(1)', 'https://github.com/sample/alpha/releases/tag/v1.0?x=1'):
            rows = copy.deepcopy(self.rows)
            rows[0]['url'] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.load(rows)

    def test_empty_and_missing_input_are_not_success(self):
        with self.assertRaises(ValueError):
            self.load([])
        with self.assertRaises(FileNotFoundError):
            digest.entries(self.path.parent / 'missing.json')


if __name__ == '__main__':
    unittest.main()
