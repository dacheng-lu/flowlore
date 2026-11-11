#!/usr/bin/env python3
"""Record a bounded local observation; the checkpoint is not authentication.

The task, checkpoint helper and files must be trusted and quiescent during this
operation. No commands are read from task records. Each invocation receives a
new identity, even if the source and output bytes are unchanged.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

SOURCE_NAMES = ('raw.json.gz', 'capture.json', 'snapshot.json', 'expected.md')


def source_digest(task):
    digest = hashlib.sha256(b'flowlore-snapshot-input-v1\0')
    for name in SOURCE_NAMES:
        data = (task / 'source' / name).read_bytes()
        digest.update(name.encode() + b'\0' + len(data).to_bytes(8, 'big') + data)
    return digest.hexdigest()


def record(task, longhaul):
    helper = longhaul / 'scripts' / 'checkpoint.py'
    if not helper.is_file():
        raise ValueError('Longhaul checkpoint helper not found')
    run_id = 'snapshot-' + uuid.uuid4().hex
    run = {'case_id': run_id, 'model': 'deterministic-snapshot',
           'input_sha256': source_digest(task)}
    directory = task / 'evidence'
    directory.mkdir(exist_ok=True)
    state = directory / (run_id + '.json')

    def checkpoint(*args):
        proc = subprocess.run([sys.executable, str(helper), *map(str, args)],
                              capture_output=True, text=True, timeout=30)
        if proc.returncode:
            raise ValueError('checkpoint refused: ' + (proc.stderr or proc.stdout).strip())
        return proc.stdout

    checkpoint('init', state, '--task-id', run_id, '--goal', 'Verify partial snapshot digest')
    # Locators are relative to the checkpoint inside evidence/, so a trusted
    # task can be moved or copied without referring back to the old directory.
    paths = [Path('../digest.md')] + [Path('../source') / n for n in SOURCE_NAMES]
    for index, path in enumerate(paths):
        result = json.loads(checkpoint('artifact', state, '--id', 'A' + str(index), '--locator', path))
        # The helper may fall back to its working directory if the state-relative
        # file is missing. Do not let that bind a similarly named unrelated file.
        if result['artifact']['locator'] != str(path):
            raise ValueError('checkpoint used a working-directory fallback: ' + str(path))
    args = ['evidence', state, '--id', 'E1']
    for index in range(len(paths)):
        args += ['--artifact', 'A' + str(index)]
    args += ['--result', 'pass', '--run-case', run_id, '--run-model', run['model'],
             '--run-input', run['input_sha256'], '--summary', 'Validated source and compared independent expected digest']
    checkpoint(*args)
    data = json.loads(state.read_text())
    data['acceptance'] = [{'id': 'C1', 'criterion': 'Partial snapshot digest matches source and expected',
                           'status': 'verified', 'evidence_ids': ['E1'], 'run': run}]
    # This example assumes a trusted, quiescent task directory; the helper's
    # gate will check every registered file after this write.
    state.write_text(json.dumps(data, indent=2) + '\n')
    if source_digest(task) != run['input_sha256']:
        raise ValueError('source changed while recording evidence')
    checkpoint('gate', state)
    return state
