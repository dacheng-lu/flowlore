#!/usr/bin/env python3
"""Read bounded, public GitHub release metadata; never send credentials or write remotely."""
import argparse
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPO = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$')
LIMIT = 2_000_000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(repo, *, per_page=30, max_pages=3, allow_partial=False, open_url=None):
    if not isinstance(repo, str) or not REPO.fullmatch(repo) or '..' in repo:
        raise ValueError('invalid owner/repository')
    if not 1 <= per_page <= 100 or not 1 <= max_pages <= 10:
        raise ValueError('invalid pagination limit')
    open_url = open_url or build_opener(NoRedirect()).open
    seen = {}
    for page in range(1, max_pages + 1):
        url = f'https://api.github.com/repos/{repo}/releases?per_page={per_page}&page={page}'
        req = Request(url, headers={'Accept': 'application/vnd.github+json',
                                    'User-Agent': 'FlowLore-release-digest',
                                    'X-GitHub-Api-Version': '2022-11-28'})
        with open_url(req, timeout=15) as response:
            body = response.read(LIMIT + 1)
        if len(body) > LIMIT:
            raise ValueError('response exceeds size limit')
        releases = json.loads(body)
        if not isinstance(releases, list) or len(releases) > per_page:
            raise ValueError('unexpected API response')
        for row in releases:
            if not isinstance(row, dict) or type(row.get('id')) is not int or row['id'] <= 0:
                raise ValueError('invalid release id')
            if type(row.get('draft')) is not bool or type(row.get('prerelease')) is not bool:
                raise ValueError('invalid release flags')
            if row['draft']:
                continue
            tag, link, name = row.get('tag_name'), row.get('html_url'), row.get('name')
            if not isinstance(tag, str) or not tag or len(tag) > 256 or any(ord(c) < 32 for c in tag):
                raise ValueError('invalid release tag')
            if not isinstance(link, str) or not isinstance(name, (str, type(None))):
                raise ValueError('invalid release metadata')
            parsed = urlsplit(link)
            expected_path = f'/{repo}/releases/tag/{tag}'
            if (parsed.scheme != 'https' or parsed.netloc != 'github.com' or parsed.query or parsed.fragment
                    or unquote(parsed.path) != expected_path):
                raise ValueError('release link does not match repository and tag')
            published = row.get('published_at')
            if not isinstance(published, str) or len(published) > 40:
                raise ValueError('invalid publication time')
            item = {'repo': repo, 'id': row['id'], 'tag': tag, 'title': (name or tag)[:256],
                    'url': link, 'published_at': published, 'prerelease': row['prerelease']}
            if row['id'] in seen and seen[row['id']] != item:
                raise ValueError('conflicting duplicate release id')
            seen[row['id']] = item
        if len(releases) < per_page:
            return sorted(seen.values(), key=lambda x: x['id']), True
    if allow_partial:
        return sorted(seen.values(), key=lambda x: x['id']), False
    raise ValueError('pagination limit reached; refusing an incomplete digest')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('repository', help='public owner/repository')
    ap.add_argument('--per-page', type=int, default=30)
    ap.add_argument('--max-pages', type=int, default=3)
    ap.add_argument('--allow-partial', action='store_true', help='return a labelled partial result at the page limit')
    args = ap.parse_args()
    try:
        data, complete = fetch(args.repository, per_page=args.per_page, max_pages=args.max_pages,
                               allow_partial=args.allow_partial)
        print(json.dumps({'repository': args.repository, 'complete': complete, 'releases': data}, ensure_ascii=True))
    except (ValueError, OSError, HTTPError, URLError, json.JSONDecodeError) as exc:
        print(f'refused: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
