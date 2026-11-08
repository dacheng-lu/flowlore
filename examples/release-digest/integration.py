#!/usr/bin/env python3
"""Exercise three projects with a fixed fixture or an explicitly captured public snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
import tenon
import digest as digest_lib

HERE = Path(__file__).resolve().parent


def call(args, cwd=None, expected=0):
    p = subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True, text=True, timeout=90)
    if p.returncode != expected:
        raise RuntimeError(f'{args}: expected {expected}, got {p.returncode}\n{p.stdout}\n{p.stderr}')
    return p.stdout


def repository_revision(path):
    try:
        head = call(['git', '-C', path, 'rev-parse', 'HEAD']).strip()
        dirty = bool(call(['git', '-C', path, 'status', '--porcelain', '--untracked-files=no']).strip())
        return {'commit': head, 'trackedDirty': dirty}
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return {'commit': 'unknown', 'trackedDirty': None}


def snapshot_fixture(snapshot, destination):
    if (not isinstance(snapshot, dict) or type(snapshot.get('complete')) is not bool
            or not isinstance(snapshot.get('repository'), str) or not isinstance(snapshot.get('releases'), list)
            or not snapshot['releases']):
        raise ValueError('snapshot must contain a labelled nonempty release list')
    rows = []
    for row in snapshot['releases']:
        if not isinstance(row, dict) or row.get('repo') != snapshot['repository']:
            raise ValueError('snapshot repository mismatch')
        rows.append({'repo': row.get('repo'), 'id': row.get('id'), 'tag': row.get('tag'),
                     'title': 'Release', 'url': row.get('url')})
    destination.write_text(json.dumps(rows))
    return digest_lib.entries(destination)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--makeextreme', type=Path, required=True)
    p.add_argument('--longhaul', type=Path, required=True)
    p.add_argument('--evidence-dir', type=Path, help='new local directory for the inspected example records')
    p.add_argument('--live-snapshot', type=Path, help='JSON captured by live_releases.py; never fetches here')
    p.add_argument('--expected', type=Path, help='independently prepared expected digest for a captured snapshot')
    a = p.parse_args()
    if a.expected and not a.live_snapshot:
        p.error('--expected requires --live-snapshot')
    mx = a.makeextreme.resolve()
    lh = a.longhaul.resolve() / 'scripts' / 'checkpoint.py'
    if not (mx / 'makeextreme/__main__.py').is_file() or not lh.is_file():
        p.error('both checked-out repositories are required')
    py = shlex.quote(sys.executable)
    with tempfile.TemporaryDirectory(prefix='trio-digest-') as tmp:
        d = Path(tmp)
        task_id = 'public-release-digest' if a.live_snapshot else 'offline-release-digest'
        for name in ('digest.py', 'releases.json', 'expected.md'):
            shutil.copyfile(HERE / name, d / name)
        if a.live_snapshot:
            snap = json.loads(a.live_snapshot.read_text())
            # Titles from the network are untrusted; the report uses a fixed label.
            validated = snapshot_fixture(snap, d / 'releases.json')
            expected = ['# Release digest', '']
            expected.extend(f"- {r['repo']} — [{r['tag']}: Release]({r['url']})" for r in validated)
            (d / 'expected.md').write_text('\n'.join(expected) + '\n')
            if a.expected:
                shutil.copyfile(a.expected, d / 'expected.md')
        stages = [
            {'id': 'validate', 'run': f'{py} digest.py validate releases.json && printf valid > input.ok',
             'check': 'test -s input.ok', 'deps': ['releases.json', 'digest.py'], 'outputs': ['input.ok']},
            {'id': 'render', 'run': f'{py} digest.py render releases.json --output digest.md',
             'check': f'{py} digest.py check releases.json --output digest.md --expected expected.md',
             'deps': ['releases.json', 'digest.py', 'expected.md', 'input.ok'], 'outputs': ['digest.md']},
        ]
        (d / 'stages.json').write_text(json.dumps(stages))
        run = [sys.executable, '-m', 'makeextreme', 'run', d]
        call(run, cwd=mx)
        digest = d / 'digest.md'
        if digest.read_text() != (d / 'expected.md').read_text():
            raise AssertionError('digest does not equal independent expected fixture')
        state = d / 'longhaul.json'
        def check(*args, expected=0):
            return call([sys.executable, lh, *args], expected=expected)
        check('init', state, '--task-id', task_id, '--goal', 'Verify captured release digest')
        check('artifact', state, '--id', 'A1', '--locator', 'digest.md')
        check('evidence', state, '--id', 'E1', '--artifact', 'A1', '--result', 'pass')
        record = json.loads(state.read_text())
        record['acceptance'] = [{'id': 'C1', 'criterion': 'Matches expected release fixture',
                                 'status': 'verified', 'evidence_ids': ['E1']}]
        state.write_text(json.dumps(record))
        check('gate', state)
        digest.write_text('changed\n')
        check('artifact', state, '--id', 'A1', '--locator', 'digest.md')
        rejected = json.loads(check('gate', state, expected=1))
        if not any('stale' in e for e in rejected.get('errors', [])):
            raise AssertionError('gate did not report stale evidence')
        # The runner must detect the changed declared output, rerun its stage,
        # and the new report must match the independent expected fixture.
        call(run, cwd=mx)
        if digest.read_text() != (d / 'expected.md').read_text():
            raise AssertionError('changed output was not restored')
        check('artifact', state, '--id', 'A1', '--locator', 'digest.md')
        check('evidence', state, '--id', 'E1', '--artifact', 'A1', '--result', 'pass')
        check('gate', state)
        journal = [json.loads(line) for line in (d / 'journal.jsonl').read_text().splitlines()]
        starts = {name: sum(e.get('ev') == 'start' and e.get('stage') == name for e in journal)
                  for name in ('validate', 'render')}
        if starts != {'validate': 1, 'render': 2}:
            raise AssertionError(f'unexpected stage starts: {starts}')
        repo_status = {'flowlore': repository_revision(HERE.parent.parent),
                       'makeextreme': repository_revision(mx),
                       'longhaul': repository_revision(lh.parent.parent)}
        card = {'schema': 'tenon/0', 'task': task_id,
                'run': str(uuid.uuid4()), 'stage': 'render',
                'recipe': 'github-release-digest', 'result': 'pass',
                'revisions': {name: value['commit'] for name, value in repo_status.items()},
                'tracked_dirty': {name: value['trackedDirty'] for name, value in repo_status.items()},
                'artifact': 'digest.md', 'sha256': hashlib.sha256(digest.read_bytes()).hexdigest(),
                'source_complete': snap['complete'] if a.live_snapshot else None,
                'check': 'exact-match expected.md; stage starts validate=1, render=2',
                'limitations': (['captured public data; completeness as stated in snapshot',
                                 'independent expected fixture' if a.expected else 'fixture-based structural checks; not semantic review'] if a.live_snapshot
                                else ['synthetic data', 'no live API'])
                               + ['not authenticated', 'no external writes']}
        if tenon.inspect(card, digest.read_bytes())[0] != 'match':
            raise AssertionError('candidate card does not match the output or lacks revisions')
        if tenon.inspect(card, b'tampered')[0] != 'mismatch':
            raise AssertionError('candidate card did not detect modified output')
        call([sys.executable, mx / 'examples/longhaul_recovery/demo.py', '--longhaul', lh.parent.parent], cwd=mx)
        print('PASS: upstream interruption/recovery demonstration')
        if a.evidence_dir:
            out = a.evidence_dir.resolve()
            out.mkdir(parents=False, exist_ok=False)
            for source in (digest, d / 'journal.jsonl', state):
                shutil.copyfile(source, out / source.name)
            if a.live_snapshot:
                shutil.copyfile(d / 'releases.json', out / 'sanitized-input.json')
            (out / 'card.json').write_text(json.dumps(card, indent=2) + '\n')
            print(f'Local example records: {out}')
        print('Evidence card (example, not a signed receipt):')
        print(json.dumps(card, indent=2))
        print('PASS: stale evidence rejected and modified output restored')


if __name__ == '__main__':
    main()
