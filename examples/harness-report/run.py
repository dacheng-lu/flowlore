#!/usr/bin/env python3
"""Exercise an independently checked producer fix and evidence handoff."""
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'release-digest'))
import integration
import tenon


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--makeextreme', type=Path, required=True)
    parser.add_argument('--longhaul', type=Path, required=True)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    args = parser.parse_args()
    mx, lh = args.makeextreme.resolve(), args.longhaul.resolve()
    out = args.evidence_dir.resolve()
    out.mkdir(parents=False, exist_ok=False)
    for name in ('summary.json', 'expected.md', 'render.py'):
        shutil.copyfile(HERE / name, out / name)
    producer = out / 'render.py'
    correct = producer.read_text()
    faulty = correct.replace("solo = source['C_pi_alone']\ncluster = source['H8_hermes_8pi']", "solo = source['H8_hermes_8pi']\ncluster = source['C_pi_alone']")
    if faulty == correct:
        raise RuntimeError('fault injection failed')
    producer.write_text(faulty)
    py = shlex.quote(sys.executable)
    stage = {'id': 'render', 'run': f'{py} render.py',
             'check': f'{py} -c "import sys; sys.exit(open(\'report.md\',\'rb\').read() != open(\'expected.md\',\'rb\').read())"',
             'deps': ['summary.json', 'render.py', 'expected.md'], 'outputs': ['report.md']}
    (out / 'stages.json').write_text(json.dumps([stage]))
    command = [sys.executable, '-m', 'makeextreme', 'run', str(out)]
    def run():
        return subprocess.run(command, cwd=mx, capture_output=True, text=True, timeout=90)
    failed = run()
    if failed.returncode == 0 or (out / 'report.md').read_bytes() == (out / 'expected.md').read_bytes():
        raise AssertionError('fault not detected')
    (out / 'first-attempt.json').write_text(json.dumps({'returncode': failed.returncode, 'stdout': failed.stdout, 'stderr': failed.stderr, 'report_sha256': hashlib.sha256((out / 'report.md').read_bytes()).hexdigest()}, indent=2) + '\n')
    shutil.copyfile(out / 'report.md', out / 'failed-report.md')
    producer.write_text(correct)
    fixed = run()
    if fixed.returncode or (out / 'report.md').read_bytes() != (out / 'expected.md').read_bytes():
        raise AssertionError(f'fixed run failed: {fixed.stdout} {fixed.stderr}')
    checkpoint = lh / 'scripts' / 'checkpoint.py'
    state = out / 'longhaul.json'
    def check(*values):
        return integration.call([sys.executable, checkpoint, *values])
    check('init', state, '--task-id', 'harness-report', '--goal', 'Verify budget comparison')
    check('artifact', state, '--id', 'A1', '--locator', 'report.md')
    check('evidence', state, '--id', 'E1', '--artifact', 'A1', '--result', 'pass')
    record = json.loads(state.read_text())
    record['acceptance'] = [{'id': 'C1', 'criterion': 'Matches independently transcribed expected.md', 'status': 'verified', 'evidence_ids': ['E1']}]
    state.write_text(json.dumps(record, indent=2) + '\n')
    check('gate', state)
    repos = {'flowlore': HERE.parent.parent, 'makeextreme': mx, 'longhaul': lh}
    status = {name: integration.repository_revision(path) for name, path in repos.items()}
    card = {'schema': 'tenon/0', 'task': 'harness-report', 'run': str(uuid.uuid4()),
            'stage': 'render', 'recipe': 'harness-budget-report', 'result': 'pass',
            'revisions': {name: value['commit'] for name, value in status.items()},
            'tracked_dirty': {name: value['trackedDirty'] for name, value in status.items()},
            'artifact': 'report.md', 'sha256': hashlib.sha256((out / 'report.md').read_bytes()).hexdigest(),
            'check': 'exact-match expected.md', 'limitations': ['captured aggregate; not a benchmark rerun', 'unauthenticated card']}
    if tenon.inspect(card, (out / 'report.md').read_bytes())[0] != 'match':
        raise AssertionError('card validation failed')
    (out / 'card.json').write_text(json.dumps(card, indent=2) + '\n')
    print('PASS: swapped producer failed; repaired producer passed; Longhaul gate accepted')
    print(f'Records: {out}')


if __name__ == '__main__':
    main()
