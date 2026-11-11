"""End-to-end test using a real runner and synchronized process interruption."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / 'persistent_snapshot.py'


class PersistentSnapshot(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.task = Path(self.temp.name) / 'task'
        self.call('init', str(self.task))

    def call(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(SCRIPT), *args], text=True,
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def run_task(self, expected=0):
        return self.call('run', str(self.task), '--makeextreme', str(MX), expected=expected)

    def starts(self, stage):
        events = [json.loads(line) for line in (self.task / 'journal.jsonl').read_text().splitlines()]
        return sum(e.get('ev') == 'start' and e.get('stage') == stage for e in events)

    def test_resume_after_interruption_and_repair(self):
        # Test-only injection pauses inside render after creating a readiness signal.
        # Keep the identical stage code across the kill and restart.
        script = self.task / 'persistent_snapshot.py'
        contents = script.read_text()
        hook = ("    if sys.argv[1:] == ['stage', 'render'] and not Path('ready').exists():\n"
                "        import time\n        Path('ready').write_text('ready')\n"
                "        time.sleep(60)\n")
        contents = contents.replace("if __name__ == '__main__':\n", "if __name__ == '__main__':\n" + hook)
        script.write_text(contents)
        proc = subprocess.Popen([sys.executable, str(SCRIPT), 'run', str(self.task),
                                 '--makeextreme', str(MX)], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            deadline = time.monotonic() + 15
            while not (self.task / 'ready').exists() and proc.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue((self.task / 'ready').exists(), 'render never reached readiness signal')
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
        self.run_task()
        self.assertEqual((self.starts('validate'), self.starts('render')), (1, 2))
        self.assertEqual((self.task / 'digest.md').read_bytes(), (self.task / 'source/expected.md').read_bytes())
        self.run_task()
        self.assertEqual((self.starts('validate'), self.starts('render')), (1, 2))
        (self.task / 'digest.md').write_text('tampered')
        self.run_task()
        self.assertEqual((self.starts('validate'), self.starts('render')), (1, 3))
        self.assertEqual((self.task / 'digest.md').read_bytes(), (self.task / 'source/expected.md').read_bytes())

    def test_existing_task_is_not_overwritten(self):
        self.call('init', str(self.task), expected=1)
        self.assertTrue((self.task / 'stages.json').is_file())

    def test_manifest_records_source_and_component_claims(self):
        self.run_task()
        manifest = json.loads((self.task / 'manifest.json').read_text())
        self.assertEqual(manifest['source_sha256']['raw.json.gz'],
                         hashlib.sha256((self.task / 'source/raw.json.gz').read_bytes()).hexdigest())
        self.assertEqual(manifest['makeextreme_latest_run']['commit'],
                         subprocess.check_output(['git', '-C', str(MX), 'rev-parse', 'HEAD'], text=True).strip())
        self.assertIsInstance(manifest['flowlore']['tracked_dirty'], bool)

    def test_modified_capture_refused_after_completed_run(self):
        self.run_task()
        capture = self.task / 'source/capture.json'
        data = json.loads(capture.read_text())
        data['complete'] = True
        capture.write_text(json.dumps(data))
        self.run_task(expected=2)

    def test_run_bound_checkpoint_rejects_swaps_and_stale_files(self):
        for _ in range(2):
            self.call('run', str(self.task), '--makeextreme', str(MX), '--longhaul', str(LH))
        records = sorted((self.task / 'evidence').glob('snapshot-*.json'))
        self.assertEqual(len(records), 2)
        first, second = (json.loads(p.read_text()) for p in records)
        self.assertNotEqual(first['acceptance'][0]['run']['case_id'], second['acceptance'][0]['run']['case_id'])
        self.assertEqual(first['acceptance'][0]['run']['input_sha256'], second['acceptance'][0]['run']['input_sha256'])
        helper = LH / 'scripts/checkpoint.py'
        def gate(path):
            return subprocess.run([sys.executable, str(helper), 'gate', str(path)], capture_output=True, text=True)
        self.assertEqual(gate(records[0]).returncode, 0)
        first['evidence'][0]['run'] = second['evidence'][0]['run']
        records[0].write_text(json.dumps(first))
        swapped = gate(records[0])
        self.assertNotEqual(swapped.returncode, 0)
        self.assertIn('not from the criterion', swapped.stdout)
        self.assertEqual(gate(records[1]).returncode, 0)
        digest = self.task / 'digest.md'
        digest.write_text('tampered')
        self.assertNotEqual(gate(records[1]).returncode, 0)
        digest.write_bytes((self.task / 'source/expected.md').read_bytes())
        self.assertEqual(gate(records[1]).returncode, 0)
        expected = self.task / 'source/expected.md'
        expected_bytes = expected.read_bytes()
        expected.unlink()
        self.assertNotEqual(gate(records[1]).returncode, 0)
        expected.write_bytes(expected_bytes)
        self.assertEqual(gate(records[1]).returncode, 0)
        source = self.task / 'source/capture.json'
        source.write_bytes(source.read_bytes() + b' ')
        self.assertNotEqual(gate(records[1]).returncode, 0)

    def test_checkpoint_follows_copied_and_moved_task(self):
        self.call('run', str(self.task), '--makeextreme', str(MX), '--longhaul', str(LH))
        record = next((self.task / 'evidence').glob('snapshot-*.json'))
        doc = json.loads(record.read_text())
        self.assertTrue(all(not Path(a['locator']).is_absolute() for a in doc['artifacts']))
        def gate(path):
            return subprocess.run([sys.executable, str(LH / 'scripts/checkpoint.py'),
                                   'gate', str(path)], capture_output=True, text=True)
        copied = self.task.parent / 'copy'
        shutil.copytree(self.task, copied)
        copied_record = copied / 'evidence' / record.name
        self.assertEqual(gate(copied_record).returncode, 0)
        (copied / 'digest.md').write_text('wrong')
        self.assertNotEqual(gate(copied_record).returncode, 0)
        self.assertEqual(gate(record).returncode, 0)
        (copied / 'digest.md').write_bytes((self.task / 'digest.md').read_bytes())
        moved = self.task.parent / 'moved'
        shutil.move(self.task, moved)
        moved_record = moved / 'evidence' / record.name
        self.assertEqual(gate(moved_record).returncode, 0)
        self.call('run', str(moved), '--makeextreme', str(MX), '--longhaul', str(LH))
        self.assertEqual(gate(moved_record).returncode, 0)

    def test_old_absolute_checkpoint_is_not_silently_rewritten(self):
        self.call('run', str(self.task), '--makeextreme', str(MX), '--longhaul', str(LH))
        record = next((self.task / 'evidence').glob('snapshot-*.json'))
        doc = json.loads(record.read_text())
        for artifact in doc['artifacts']:
            artifact['locator'] = str((record.parent / artifact['locator']).resolve())
        for evidence in doc['evidence']:
            evidence['locator'] = str((record.parent / evidence['locator']).resolve())
        record.write_text(json.dumps(doc))
        original = record.read_bytes()
        moved = self.task.parent / 'moved'
        shutil.move(self.task, moved)
        moved_record = moved / 'evidence' / record.name
        result = subprocess.run([sys.executable, str(LH / 'scripts/checkpoint.py'),
                                 'gate', str(moved_record)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(moved_record.read_bytes(), original)
        self.call('run', str(moved), '--makeextreme', str(MX), '--longhaul', str(LH))
        new_records = set((moved / 'evidence').glob('snapshot-*.json')) - {moved_record}
        self.assertEqual(len(new_records), 1)
        result = subprocess.run([sys.executable, str(LH / 'scripts/checkpoint.py'),
                                 'gate', str(new_records.pop())], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_task_output_does_not_bind_working_directory_fallback(self):
        work = self.task.parent / 'working'
        work.mkdir()
        (self.task.parent / 'digest.md').write_text('unrelated file')
        code = ("import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
                "import persistent_evidence; persistent_evidence.record(Path(sys.argv[2]), Path(sys.argv[3]))")
        result = subprocess.run([sys.executable, '-c', code, str(HERE), str(self.task), str(LH)],
                                cwd=work, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('working-directory fallback', result.stderr)
        records = list((self.task / 'evidence').glob('snapshot-*.json'))
        self.assertEqual(len(records), 1)
        gate = subprocess.run([sys.executable, str(LH / 'scripts/checkpoint.py'), 'gate', str(records[0])],
                              capture_output=True, text=True)
        self.assertNotEqual(gate.returncode, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--makeextreme', type=Path, required=True)
    parser.add_argument('--longhaul', type=Path)
    args = parser.parse_args()
    MX = args.makeextreme.resolve()
    LH = (args.longhaul or MX.parent / 'longhaul').resolve()
    unittest.main(argv=[sys.argv[0]])
