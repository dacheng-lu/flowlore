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


class VerifyTests(unittest.TestCase):
    """`verify` anchors acceptance to the trusted source, not to a second file.

    The failure it closes: a producer silently repairs an invalid source (drops an
    extra field, invents a title) and renders a digest that is internally valid.
    `check` against a fixture derived from the repaired bytes would pass; `verify`
    refuses because the source itself is invalid.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.rows = json.loads((HERE / 'releases.json').read_text())
        self.source = self.dir / 'source.json'
        self.output = self.dir / 'digest.md'

    def run_cli(self, *args):
        import subprocess
        import sys
        return subprocess.run([sys.executable, str(HERE / 'digest.py'), *map(str, args)],
                               capture_output=True, text=True)

    def render_source(self):
        self.source.write_text(json.dumps(self.rows))
        rendered = self.run_cli('render', self.source, '--output', self.output)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)

    def test_a_digest_rendered_from_its_own_source_verifies(self):
        self.render_source()
        result = self.run_cli('verify', self.source, '--output', self.output)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_digest_from_repaired_bytes_does_not_verify(self):
        repaired = copy.deepcopy(self.rows)
        repaired[0]['draft'] = False           # extra field the renderer rejects
        self.source.write_text(json.dumps(repaired))
        clean = copy.deepcopy(self.rows)
        clean[0].pop('draft', None)
        scratch = self.dir / 'clean.json'
        scratch.write_text(json.dumps(clean))
        self.assertEqual(self.run_cli('render', scratch, '--output', self.output).returncode, 0)
        result = self.run_cli('verify', self.source, '--output', self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn('refused', result.stderr)

    def test_a_digest_of_other_content_does_not_verify(self):
        self.render_source()
        self.output.write_text('# Release digest\n\n- forged line\n')
        result = self.run_cli('verify', self.source, '--output', self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn('not the rendering of this source', result.stderr)


if __name__ == '__main__':
    unittest.main()
