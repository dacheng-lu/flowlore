#!/usr/bin/env python3
"""Run a saved public snapshot as a persistent, resumable local task.

The source is a partial historical capture, not a live or authenticated feed.
The task directory contains executable code and must be kept trusted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import digest
import reproduce_snapshot

HERE = Path(__file__).resolve().parent


def revision(path):
    """Best-effort source claims, not provenance or authentication."""
    try:
        head = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        status = subprocess.run(['git', '-C', str(path), 'status', '--porcelain', '--untracked-files=no'],
                                capture_output=True, text=True, check=True, timeout=10).stdout
        return {'commit': head, 'tracked_dirty': bool(status)}
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return {'commit': 'unknown', 'tracked_dirty': None}


def normalized(source):
    snapshot = reproduce_snapshot.validate(source)
    if snapshot['complete'] is not False:
        raise ValueError('capture must remain labelled partial')
    return [{'repo': r['repo'], 'id': r['id'], 'tag': r['tag'],
             'title': 'Release', 'url': r['url']} for r in snapshot['releases']]


def verify(task):
    rows = normalized(task / 'source')
    if json.loads((task / 'input.json').read_text()) != rows:
        raise ValueError('normalized input does not match the captured source')
    rendered = digest.render(digest.entries(task / 'input.json'))
    if (task / 'digest.md').read_text() != rendered:
        raise ValueError('digest does not match the validated source')
    if rendered != (task / 'source/expected.md').read_text():
        raise ValueError('digest differs from the independent expected file')


def initialize(task, source):
    normalized(source)  # Refuse a damaged capture before creating anything.
    task.mkdir()  # Never overwrite an existing task.
    (task / 'source').mkdir()
    for name in ('raw.json.gz', 'capture.json', 'snapshot.json', 'expected.md'):
        shutil.copyfile(source / name, task / 'source' / name)
    for name in ('persistent_snapshot.py', 'reproduce_snapshot.py', 'live_releases.py', 'digest.py'):
        shutil.copyfile(HERE / name, task / name)
    names = ('raw.json.gz', 'capture.json', 'snapshot.json', 'expected.md')
    manifest = {'scope': 'partial historical snapshot; hashes and revisions are unauthenticated claims',
                'flowlore': revision(HERE.parent.parent), 'makeextreme_latest_run': None,
                'source_sha256': {n: hashlib.sha256((task / 'source' / n).read_bytes()).hexdigest()
                                  for n in names},
                'task_code_requirement': 'task code and stage definitions must be trusted by the operator'}
    (task / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    py = shlex.quote(sys.executable)
    stages = [
        {'id': 'validate', 'run': f'{py} persistent_snapshot.py stage validate',
         'check': f'{py} persistent_snapshot.py stage check-input',
         'deps': ['source', 'persistent_snapshot.py', 'reproduce_snapshot.py', 'live_releases.py'],
         'outputs': ['input.json']},
        {'id': 'render', 'run': f'{py} persistent_snapshot.py stage render',
         'check': f'{py} persistent_snapshot.py stage check-output',
         'deps': ['source', 'input.json', 'persistent_snapshot.py', 'digest.py', 'reproduce_snapshot.py', 'live_releases.py'],
         'outputs': ['digest.md']},
    ]
    (task / 'stages.json').write_text(json.dumps(stages, indent=2) + '\n')


def stage(action):
    task = Path.cwd()
    if action == 'validate':
        (task / 'input.json').write_text(json.dumps(normalized(task / 'source'), indent=2) + '\n')
    elif action == 'check-input':
        if json.loads((task / 'input.json').read_text()) != normalized(task / 'source'):
            raise ValueError('normalized input differs from source')
    elif action == 'render':
        (task / 'digest.md').write_text(digest.render(digest.entries(task / 'input.json')))
    else:
        verify(task)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('init', help='create a new task directory from the saved capture')
    p.add_argument('task', type=Path)
    p.add_argument('--source', type=Path, default=reproduce_snapshot.EVIDENCE)
    p = sub.add_parser('run', help='start or resume an existing task')
    p.add_argument('task', type=Path)
    p.add_argument('--makeextreme', type=Path, required=True)
    p.add_argument('--longhaul', type=Path, help='optionally record a run-bound checkpoint after verification')
    p = sub.add_parser('stage', help=argparse.SUPPRESS)
    p.add_argument('stage', choices=['validate', 'check-input', 'render', 'check-output'])
    args = parser.parse_args()
    try:
        if args.action == 'init':
            initialize(args.task, args.source)
            print(f'Created {args.task}; run it with the run command.')
        elif args.action == 'run':
            task, mx = args.task.resolve(), args.makeextreme.resolve()
            if not (mx / 'makeextreme/__main__.py').is_file():
                raise ValueError('Makeextreme checkout not found')
            if not (task / 'stages.json').is_file():
                raise ValueError('task not initialized')
            manifest_path = task / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['makeextreme_latest_run'] = revision(mx)
            # This is a record of the latest attempt, not proof that it completed.
            tmp_manifest = task / 'manifest.json.tmp'
            tmp_manifest.write_text(json.dumps(manifest, indent=2) + '\n')
            tmp_manifest.replace(manifest_path)
            proc = subprocess.run([sys.executable, '-m', 'makeextreme', 'run', str(task)], cwd=mx)
            if proc.returncode:
                print(f'runner stopped with exit {proc.returncode}; inspect task state before retrying', file=sys.stderr)
                return proc.returncode
            verify(task)  # Recheck on every invocation, including after skipped stages.
            if args.longhaul:
                import persistent_evidence
                checkpoint = persistent_evidence.record(task, args.longhaul.resolve())
                print(f'Run-bound checkpoint: {checkpoint}')
            print(f'PASS: partial offline snapshot verified; digest: {task / "digest.md"}')
        else:
            stage(args.stage)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f'refused: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
