#!/usr/bin/env python3
"""Verify a saved public response, normalize it offline and exercise the trio."""
import argparse
import hashlib
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import live_releases

HERE=Path(__file__).resolve().parent
EVIDENCE=HERE/'evidence/cli-snapshot'

class Response:
    def __init__(self, body): self.body=body
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, limit): return self.body[:limit]


def validate(root):
    with gzip.open(root/'raw.json.gz', 'rb') as source:
        raw=source.read(live_releases.LIMIT + 1)
    if len(raw)>live_releases.LIMIT:
        raise ValueError('raw response exceeds limit')
    capture=json.loads((root/'capture.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=capture['raw_sha256']:
        raise ValueError('raw response hash mismatch')
    expected_url='https://api.github.com/repos/cli/cli/releases?per_page=3&page=1'
    if capture['url']!=expected_url or capture['complete'] is not False:
        raise ValueError('unexpected capture scope')
    rows,complete=live_releases.fetch('cli/cli',per_page=3,max_pages=1,allow_partial=True,
                                      open_url=lambda req,timeout: Response(raw))
    snapshot=json.loads((root/'snapshot.json').read_text())
    if snapshot!={'repository':'cli/cli','complete':complete,'releases':rows}:
        raise ValueError('normalized snapshot differs from raw response')
    return snapshot


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--makeextreme',required=True,type=Path)
    p.add_argument('--longhaul',required=True,type=Path)
    p.add_argument('--evidence',type=Path,default=EVIDENCE)
    p.add_argument('--output-dir',type=Path,help='new directory for the retained digest and verification records; parent must exist')
    a=p.parse_args()
    try:
        snapshot=validate(a.evidence)
        if snapshot['complete'] is not False: raise ValueError('sample must remain labelled partial')
        if a.output_dir and (a.output_dir.exists() or not a.output_dir.parent.is_dir()):
            raise ValueError('output directory must not exist and its parent must exist')
        cmd=[sys.executable,str(HERE/'integration.py'),'--makeextreme',str(a.makeextreme.resolve()),
                        '--longhaul',str(a.longhaul.resolve()),'--live-snapshot',str((a.evidence/'snapshot.json').resolve()),
                        '--expected',str((a.evidence/'expected.md').resolve()),
                        '--verify-handoff-source',str(a.evidence.resolve())]
        if a.output_dir:
            cmd += ['--evidence-dir',str(a.output_dir.resolve())]
        subprocess.run(cmd,check=True)
    except (ValueError,KeyError,OSError,subprocess.CalledProcessError) as exc:
        print(f'refused: {exc}',file=sys.stderr)
        return 1
    print('PASS: pinned raw public response and independent expected digest; sample is partial')
    return 0

if __name__=='__main__': raise SystemExit(main())
