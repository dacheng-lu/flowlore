#!/usr/bin/env python3
"""Inspect a draft local evidence card; no commands, trust grants, or writes."""
import argparse
import hashlib
import json
import os
import re
import stat
import sys
from collections import Counter
from pathlib import Path

HASH = re.compile(r'^[0-9a-f]{64}$')
IDENT = re.compile(r'^[A-Za-z0-9_.-]{1,100}$')


def inspect(card, artifact):
    """A matching hash validates bytes only; it cannot authenticate a producer or a check."""
    if not isinstance(card, dict) or card.get('schema') != 'tenon/0':
        return 'unknown', 'unsupported card'
    for key in ('task', 'run', 'stage', 'recipe'):
        if not isinstance(card.get(key), str) or not IDENT.fullmatch(card[key]):
            return 'unknown', 'missing or invalid ' + key
    if card.get('result') not in ('pass', 'fail', 'unknown', 'uncertain'):
        return 'unknown', 'missing or invalid result'
    if not isinstance(card.get('check'), str) or not card['check'].strip():
        return 'unknown', 'missing check description'
    revisions = card.get('revisions')
    if not isinstance(revisions, dict) or any(
            not isinstance(revisions.get(k), str) or not re.fullmatch(r'[0-9a-f]{40}', revisions[k])
            for k in ('flowlore', 'longhaul', 'makeextreme')):
        return 'unknown', 'missing pinned repository revisions'
    expected = card.get('sha256')
    if not isinstance(expected, str) or not HASH.fullmatch(expected) or artifact is None:
        return 'unknown', 'missing artifact or content hash'
    if hashlib.sha256(artifact).hexdigest() != expected:
        return 'mismatch', 'artifact hash differs from the card'
    return 'match', 'bytes match the claim; identity, check and semantic correctness remain unverified'


def read_file(path, maximum):
    flags = os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise ValueError('input must be a regular file')
        data = f.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('input exceeds size limit')
    return data


def strict_json(data):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError('duplicate JSON key')
            obj[key] = value
        return obj
    def constant(value):
        raise ValueError('non-finite JSON number')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def summary(card_path, artifact_path, journal_path=None, checkpoint_path=None):
    card = strict_json(read_file(card_path, 1_000_000))
    outcome, reason = inspect(card, read_file(artifact_path, 50_000_000))
    result = {'schema': 'tenon-view/0', 'artifact': outcome, 'reason': reason,
              'claimed_result': card.get('result') if isinstance(card, dict) else None,
              'identity': 'unverified', 'linkage': 'not authenticated; manually supplied files'}
    if journal_path:
        counts = Counter()
        for line in read_file(journal_path, 5_000_000).splitlines():
            event = strict_json(line)
            if not isinstance(event, dict) or not isinstance(event.get('ev'), str):
                raise ValueError('malformed journal entry')
            if event['ev'] in ('start', 'end', 'skip', 'fail', 'refused', 'interrupted'):
                counts[event['ev']] += 1
        result['journal_event_counts'] = dict(sorted(counts.items()))
    if checkpoint_path:
        checkpoint = strict_json(read_file(checkpoint_path, 5_000_000))
        if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get('evidence'), list):
            raise ValueError('malformed checkpoint')
        result['checkpoint_evidence_count'] = len(checkpoint['evidence'])
        result['checkpoint_validation'] = 'not run; use the Longhaul gate separately'
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--card', type=Path, required=True)
    ap.add_argument('--artifact', type=Path, required=True)
    ap.add_argument('--journal', type=Path)
    ap.add_argument('--checkpoint', type=Path)
    args = ap.parse_args()
    try:
        result = summary(args.card, args.artifact, args.journal, args.checkpoint)
        print(json.dumps(result, sort_keys=True))
        return 0 if result['artifact'] == 'match' and result['claimed_result'] == 'pass' else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'refused: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
