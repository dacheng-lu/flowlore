#!/usr/bin/env python3
"""Exercise pinned projects with fixed local fixtures; no network or credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--makeextreme', type=Path, required=True)
    p.add_argument('--longhaul', type=Path, required=True)
    a = p.parse_args()
    mx = a.makeextreme.resolve()
    lh = a.longhaul.resolve() / 'scripts' / 'checkpoint.py'
    if not (mx / 'makeextreme/__main__.py').is_file() or not lh.is_file():
        p.error('both checked-out repositories are required')
    py = shlex.quote(sys.executable)
    with tempfile.TemporaryDirectory(prefix='trio-digest-') as tmp:
        d = Path(tmp)
        for name in ('digest.py', 'releases.json', 'expected.md'):
            shutil.copyfile(HERE / name, d / name)
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
        check('init', state, '--task-id', 'offline-release-digest', '--goal', 'Verify fixed release digest')
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
        card = {'schema': 'trio-evidence-example/0.1', 'task': 'offline-release-digest',
                'recipe': 'github-release-digest', 'result': 'pass',
                'revisions': {'flowlore': repository_revision(HERE.parent.parent),
                              'makeextreme': repository_revision(mx),
                              'longhaul': repository_revision(lh.parent.parent)},
                'artifact': 'digest.md', 'sha256': hashlib.sha256(digest.read_bytes()).hexdigest(),
                'check': 'exact-match expected.md; stage starts validate=1, render=2',
                'limitations': ['synthetic data', 'not authenticated', 'no live API or external side effects']}
        print('Evidence card (example, not a signed receipt):')
        print(json.dumps(card, indent=2))
        print('PASS: stale evidence rejected and modified output restored')
    # An existing upstream demo independently exercises a real process interruption.
    call([sys.executable, mx / 'examples/longhaul_recovery/demo.py', '--longhaul', lh.parent.parent], cwd=mx)
    print('PASS: upstream interruption/recovery demonstration')


if __name__ == '__main__':
    main()
