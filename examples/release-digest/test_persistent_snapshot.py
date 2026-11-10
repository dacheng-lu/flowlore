"""End-to-end test using a real runner and synchronized process interruption."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--makeextreme', type=Path, required=True)
    args = parser.parse_args()
    MX = args.makeextreme.resolve()
    unittest.main(argv=[sys.argv[0]])
