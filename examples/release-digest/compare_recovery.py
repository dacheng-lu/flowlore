#!/usr/bin/env python3
"""Small deterministic comparison; not a model benchmark or security audit."""
import argparse
import json
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import digest


def worker(task):
    # Identical intentionally imperfect producer in every condition: it drops
    # unrecognised fields, modelling a producer that silently repairs input.
    source = json.loads((task / 'source.json').read_text())
    fields = ('repo', 'id', 'tag', 'title', 'url')
    repaired = [{k: row[k] for k in fields} for row in source]
    (task / 'repaired.json').write_text(json.dumps(repaired))
    content = digest.render(digest.entries(task / 'repaired.json'))
    (task / 'digest.md').write_text(content)
    (task / 'expected.md').write_text(content)
    with (task / 'starts').open('a') as f:
        f.write('render\n')


def command(argv, cwd=None):
    p = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True, text=True, timeout=90)
    return {'argv': [str(x) for x in argv], 'code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def trial(condition, scenario, mx, lh):
    began = time.monotonic()
    logs = []
    with tempfile.TemporaryDirectory(prefix='trio-comparison-') as tmp:
        d = Path(tmp)
        source = json.loads((HERE / 'releases.json').read_text())
        if scenario == 'invalid-source':
            source[0]['unexpected'] = 'invalid'
        (d / 'source.json').write_text(json.dumps(source))
        stage = {'id': 'render', 'run': f'{shlex.quote(sys.executable)} {shlex.quote(str(Path(__file__).resolve()))} --worker {shlex.quote(str(d))}',
                 'check': f'{shlex.quote(sys.executable)} {shlex.quote(str(HERE / "digest.py"))} check {shlex.quote(str(d / "repaired.json"))} --output {shlex.quote(str(d / "digest.md"))} --expected {shlex.quote(str(d / "expected.md"))}',
                 'deps': ['source.json'], 'outputs': ['digest.md']}
        (d / 'stages.json').write_text(json.dumps([stage]))
        def execute():
            if condition == 'plain':
                return command([sys.executable, __file__, '--worker', d])
            return command([sys.executable, '-m', 'makeextreme', 'run', d], mx)
        logs.append(execute())
        if logs[-1]['code'] != 0:
            raise RuntimeError(f'producer execution failed: {logs[-1]}')
        if scenario in ('tamper-output', 'repeat'):
            if scenario == 'tamper-output':
                (d / 'digest.md').write_text('tampered\n')
            logs.append(execute())
            if logs[-1]['code'] != 0:
                raise RuntimeError(f'recovery execution failed: {logs[-1]}')
        # Identical source-anchored acceptance for all three conditions. The
        # producer-derived comparison is reported separately as a diagnostic.
        weak = command([sys.executable, HERE / 'digest.py', 'check', d / 'repaired.json', '--output', d / 'digest.md', '--expected', d / 'expected.md'])
        logs.append(weak)
        verified = command([sys.executable, HERE / 'digest.py', 'verify', d / 'source.json', '--output', d / 'digest.md'])
        logs.append(verified)
        accepted = verified['code'] == 0
        if condition == 'anchored' and accepted:
            checkpoint = lh / 'scripts/checkpoint.py'
            state = d / 'state.json'
            for args in ([checkpoint, 'init', state, '--task-id', 'comparison', '--goal', 'Check digest'],
                         [checkpoint, 'artifact', state, '--id', 'A1', '--locator', 'digest.md'],
                         [checkpoint, 'evidence', state, '--id', 'E1', '--artifact', 'A1', '--result', 'pass']):
                result = command([sys.executable, *args]); logs.append(result)
                if result['code'] != 0: raise RuntimeError(str(result))
            record = json.loads(state.read_text())
            record['acceptance'] = [{'id': 'C1', 'criterion': 'source verification', 'status': 'verified', 'evidence_ids': ['E1']}]
            state.write_text(json.dumps(record))
            result = command([sys.executable, checkpoint, 'gate', state]); logs.append(result)
            accepted = result['code'] == 0
        truth = scenario != 'invalid-source' and (d / 'digest.md').read_text() == digest.render(digest.entries(d / 'source.json'))
        return {'condition': condition, 'scenario': scenario, 'accepted': accepted,
                'expected_acceptance': truth, 'weak_check_accepted': weak['code'] == 0, 'false_accept': accepted and not truth,
                'false_reject': not accepted and truth,
                'stage_starts': len((d / 'starts').read_text().splitlines()),
                'wall_seconds': round(time.monotonic() - began, 6), 'commands': logs}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    p.add_argument('--makeextreme', type=Path)
    p.add_argument('--longhaul', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if a.worker:
        worker(a.worker); return
    if not a.makeextreme or not a.longhaul: p.error('--makeextreme and --longhaul are required')
    mx, lh = a.makeextreme.resolve(), a.longhaul.resolve()
    revisions = {}
    for name, path in [('flowlore', HERE.parent.parent), ('makeextreme', mx), ('longhaul', lh)]:
        result = command(['git', '-C', path, 'rev-parse', 'HEAD'])
        status = command(['git', '-C', path, 'status', '--porcelain', '--untracked-files=no'])
        revisions[name] = {'commit': result['stdout'].strip() if result['code'] == 0 else 'unknown',
                           'tracked_dirty': bool(status['stdout']) if status['code'] == 0 else None}
    results = [trial(c, s, mx, lh) for s in ('valid', 'repeat', 'tamper-output', 'invalid-source') for c in ('plain', 'runner', 'anchored')]
    output = {'revisions': revisions, 'results': results,
              'limitations': ['four synthetic cases, one run each; no statistical inference',
                              'not an interruption or model experiment; tamper occurs between runs',
                              'all conditions use the same imperfect producer and source-anchored acceptance; weak check is diagnostic only',
                              'anchored verifies source before recording a local checkpoint; no authenticated provenance',
                              'wall time includes process startup and is not a cost estimate']}
    content = json.dumps(output, indent=2) + '\n'
    if a.output:
        with a.output.open('x') as f: f.write(content)
    print(content, end='')


if __name__ == '__main__': main()
