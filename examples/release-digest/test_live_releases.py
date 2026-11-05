import copy
import importlib.util
import json
from pathlib import Path
import unittest
from urllib.error import HTTPError
import tempfile
import integration

spec = importlib.util.spec_from_file_location('live', Path(__file__).with_name('live_releases.py'))
live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)


def release(n=1):
    return {'id': n, 'draft': False, 'prerelease': False, 'tag_name': f'v{n}',
            'name': f'Release {n}', 'html_url': f'https://github.com/test/repo/releases/tag/v{n}',
            'published_at': '2026-11-01T00:00:00Z'}


class Response:
    def __init__(self, value):
        self.value = json.dumps(value).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, limit):
        return self.value[:limit]


class FetchTests(unittest.TestCase):
    def opener(self, pages):
        self.urls = []
        def open_url(req, timeout):
            self.urls.append(req.full_url)
            self.assertIsNone(req.get_header('Authorization'))
            return Response(pages[len(self.urls) - 1])
        return open_url

    def test_pagination_and_duplicate(self):
        data, complete = live.fetch('test/repo', per_page=2, max_pages=3,
                                    open_url=self.opener([[release(), release(2)], [release()]]))
        self.assertTrue(complete)
        self.assertEqual([r['id'] for r in data], [1, 2])
        self.assertTrue(self.urls[1].endswith('page=2'))

    def test_partial_must_be_explicit_and_labelled(self):
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            live.fetch('test/repo', per_page=1, max_pages=1, open_url=self.opener([[release()]]))
        data, complete = live.fetch('test/repo', per_page=1, max_pages=1, allow_partial=True,
                                    open_url=self.opener([[release()]]))
        self.assertEqual(len(data), 1)
        self.assertFalse(complete)

    def test_invalid_host_conflicts_and_api_errors_refuse(self):
        bad = release()
        bad['html_url'] = 'https://attacker.invalid/test/repo/releases/tag/v1'
        conflicting = copy.deepcopy(release())
        conflicting['name'] = 'different'
        for pages in ([[bad]], [[release(), conflicting]]):
            with self.subTest(pages=pages), self.assertRaises(ValueError):
                live.fetch('test/repo', per_page=2, open_url=self.opener(pages))
        def rate_limited(req, timeout):
            raise HTTPError(req.full_url, 403, 'rate limited', {}, None)
        with self.assertRaises(HTTPError):
            live.fetch('test/repo', open_url=rate_limited)

    def test_empty_and_invalid_repository(self):
        data, complete = live.fetch('test/repo', open_url=self.opener([[]]))
        self.assertEqual((data, complete), ([], True))
        for repo in ('../repo', 'x/y/z', 'x/repo?token=secret'):
            with self.subTest(repo=repo), self.assertRaises(ValueError):
                live.fetch(repo, open_url=self.opener([]))

    def test_snapshot_rejects_forged_urls_and_treats_titles_as_data(self):
        sample = release()
        sample['repo'] = 'test/repo'
        sample['tag'] = sample.pop('tag_name')
        sample['url'] = sample.pop('html_url')
        sample['title'] = '](https://attacker.invalid)'
        snapshot = {'repository': 'test/repo', 'complete': False, 'releases': [sample]}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'fixture.json'
            rows = integration.snapshot_fixture(snapshot, target)
            self.assertEqual(rows[0]['title'], 'Release')
            snapshot['releases'][0]['url'] = 'https://attacker.invalid/evil'
            with self.assertRaises(ValueError):
                integration.snapshot_fixture(snapshot, target)


if __name__ == '__main__':
    unittest.main()
