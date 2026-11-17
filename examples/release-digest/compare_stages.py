#!/usr/bin/env python3
"""Compare two offline digest pipelines. Run from any directory:

  python3 /path/to/flowlore/examples/release-digest/compare_stages.py \
    --makeextreme /path/to/makeextreme

Requires Python 3 and a supported Linux environment for Makeextreme. Uses local
synthetic fixtures and temporary task directories; never sends network requests.
Both pipelines check the same independent expected file. The shorter pipeline
relies on render's existing input validation. It loses the separate input.ok
artifact and validation-stage journal/checkpoint: the audit trail is different.
Five fixed-order timings are illustrative only, not a general performance claim.
This experiment does not exercise Longhaul or automatic cross-project routing.
"""
import argparse
import json
from pathlib import Path
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent


def trial(mx, short, invalid=False):
    with tempfile.TemporaryDirectory(prefix='digest-comparison-') as tmp:
        task = Path(tmp)
        for name in ('digest.py', 'releases.json', 'expected.md'):
            shutil.copyfile(HERE / name, task / name)
        if invalid:
            (task / 'releases.json').write_text('[]', encoding='utf-8')
        py = shlex.quote(sys.executable)
        validate = {'id': 'validate', 'run': f'{py} digest.py validate releases.json && printf valid > input.ok',
                    'check': 'test -s input.ok', 'deps': ['releases.json', 'digest.py'], 'outputs': ['input.ok']}
        render = {'id': 'render', 'run': f'{py} digest.py render releases.json --output digest.md',
                  'check': f'{py} digest.py check releases.json --output digest.md --expected expected.md',
                  'deps': ['releases.json', 'digest.py', 'expected.md'], 'outputs': ['digest.md']}
        if not short:
            render['deps'].append('input.ok')
        stages = [render] if short else [validate, render]
        (task / 'stages.json').write_text(json.dumps(stages), encoding='utf-8')

        def launch():
            start = time.monotonic()
            proc = subprocess.run([sys.executable, '-m', 'makeextreme', 'run', str(task)],
                                  cwd=mx, capture_output=True, text=True, timeout=90)
            return proc, time.monotonic() - start

        first, elapsed = launch()
        journal = lambda: [json.loads(line) for line in (task / 'journal.jsonl').read_text().splitlines()]
        if invalid:
            stage = 'render' if short else 'validate'
            ends = [e for e in journal() if e.get('ev') == 'end' and e.get('stage') == stage]
            assert first.returncode != 0 and not (task / 'digest.md').exists(), 'invalid input was accepted'
            assert 'refused: expected a non-empty release list' in first.stderr, first.stderr
            assert len(ends) == 1 and ends[0].get('rc') == 1 and ends[0].get('ok') is False, ends
            return {'refused_empty_list': True, 'output_absent': True}
        assert first.returncode == 0, (first.stdout, first.stderr)
        digest = task / 'digest.md'
        expected = (task / 'expected.md').read_bytes()
        assert digest.read_bytes() == expected, 'digest differs from expected fixture'
        digest.write_text('changed\n', encoding='utf-8')
        second, _ = launch()
        assert second.returncode == 0 and digest.read_bytes() == expected, 'modified output not restored'
        events = journal()
        starts = {stage['id']: sum(e.get('ev') == 'start' and e.get('stage') == stage['id']
                                  for e in events) for stage in stages}
        assert starts == ({'render': 2} if short else {'validate': 1, 'render': 2}), starts
        return {'initial_seconds': round(elapsed, 4), 'exact_match': True,
                'modified_output_restored': True, 'stage_starts': starts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--makeextreme', required=True, type=Path, help='path to Makeextreme checkout')
    parser.add_argument('--repeats', type=int, default=5, help='number of valid runs per path')
    args = parser.parse_args()
    mx = args.makeextreme.resolve()
    if not (mx / 'makeextreme' / '__main__.py').is_file() or args.repeats < 1:
        parser.error('provide a Makeextreme checkout and a positive repeat count')
    for name, short in (('baseline', False), ('short', True)):
        valid = [trial(mx, short) for _ in range(args.repeats)]
        result = {'valid': valid, 'invalid': trial(mx, short, invalid=True),
                  'median_initial_seconds': statistics.median(x['initial_seconds'] for x in valid)}
        print(name, json.dumps(result, sort_keys=True))
    print('Audit difference: short path has no separate input.ok or validate-stage journal/checkpoint.')
    print('Fixed-order synthetic timings are illustrative; they do not establish general speedup.')


if __name__ == '__main__':
    main()
