#!/usr/bin/env python3
"""Deterministic offline release digest; all input is untrusted data."""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
SAFE = re.compile(r'^[A-Za-z0-9 ._-]{1,80}$')


def entries(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, list) or not data:
        raise ValueError('expected a non-empty release list')
    unique = {}
    for row in data:
        if not isinstance(row, dict) or set(row) != {'repo', 'id', 'tag', 'title', 'url'}:
            raise ValueError('release fields are invalid')
        repo, rid, tag, title, url = (row[k] for k in ('repo', 'id', 'tag', 'title', 'url'))
        if not isinstance(repo, str) or not REPO.fullmatch(repo) or type(rid) is not int or rid <= 0:
            raise ValueError('invalid repository or release id')
        if not all(isinstance(s, str) and SAFE.fullmatch(s) for s in (tag, title)):
            raise ValueError('invalid tag or title')
        if not isinstance(url, str):
            raise ValueError('missing URL')
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or parsed.netloc != 'github.com' or parsed.query or parsed.fragment
                or parsed.path != f'/{repo}/releases/tag/{tag}'):
            raise ValueError('release URL does not match the repository and tag')
        key = (repo, rid)
        if key in unique and unique[key] != row:
            raise ValueError('conflicting records for the same release')
        unique[key] = row
    return [unique[k] for k in sorted(unique)]


def render(rows):
    lines = ['# Release digest', '']
    lines.extend(f"- {r['repo']} — [{r['tag']}: {r['title']}]({r['url']})" for r in rows)
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['validate', 'render', 'check'])
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--expected', type=Path)
    args = parser.parse_args()
    try:
        rows = entries(args.input)
        if args.mode == 'render':
            if args.output is None:
                parser.error('render requires --output')
            args.output.write_text(render(rows), encoding='utf-8')
        if args.mode == 'check':
            if args.output is None or args.expected is None:
                parser.error('check requires --output and --expected')
            if args.output.read_text(encoding='utf-8') != args.expected.read_text(encoding='utf-8'):
                raise ValueError('digest differs from expected fixture')
        print(f'{args.mode}: {len(rows)} unique releases')
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'refused: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
