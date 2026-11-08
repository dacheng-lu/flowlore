#!/usr/bin/env python3
"""Check one local snapshot handoff against trusted inputs; never grant acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tenon
import reproduce_snapshot


def verify(bundle, source, longhaul, flowlore_rev, longhaul_rev, makeextreme_rev):
    card=tenon.strict_json(tenon.read_file(bundle/'card.json',1_000_000))
    artifact=tenon.read_file(bundle/'digest.md',50_000_000)
    result,reason=tenon.inspect(card,artifact)
    if result!='match' or card.get('result')!='pass': raise ValueError('unusable card: '+reason)
    expected={'flowlore':flowlore_rev,'longhaul':longhaul_rev,'makeextreme':makeextreme_rev}
    if card.get('revisions')!=expected: raise ValueError('component revision mismatch')
    if card.get('task')!='public-release-digest' or card.get('recipe')!='github-release-digest' or card.get('stage')!='render':
        raise ValueError('unexpected task scope')
    if card.get('source_complete') is not False: raise ValueError('partial source not declared')
    snapshot=reproduce_snapshot.validate(source)
    rows=[{'repo':r['repo'],'id':r['id'],'tag':r['tag'],'title':'Release','url':r['url']} for r in snapshot['releases']]
    actual=tenon.strict_json(tenon.read_file(bundle/'sanitized-input.json',1_000_000))
    if actual!=rows: raise ValueError('sanitized input differs from captured source')
    if artifact!=tenon.read_file(source/'expected.md',1_000_000): raise ValueError('report differs from trusted expected digest')
    events=[tenon.strict_json(line) for line in tenon.read_file(bundle/'journal.jsonl',5_000_000).splitlines()]
    ends=[e for e in events if isinstance(e,dict) and e.get('ev')=='end' and e.get('stage')=='render']
    if not ends or ends[-1].get('ok') is not True: raise ValueError('no successful render event')
    checkpoint=bundle/'longhaul.json'
    proc=subprocess.run([sys.executable,str(longhaul/'scripts/checkpoint.py'),'gate',str(checkpoint)],capture_output=True,text=True,timeout=30)
    if proc.returncode!=0: raise ValueError('Longhaul gate refused the checkpoint')
    state=tenon.strict_json(tenon.read_file(checkpoint,5_000_000))
    if state.get('task_id')!='public-release-digest': raise ValueError('checkpoint task mismatch')
    artifacts=state.get('artifacts',[])
    digest=hashlib.sha256(artifact).hexdigest()
    if not any(a.get('id')=='A1' and a.get('locator')=='digest.md' and a.get('sha256')==digest for a in artifacts if isinstance(a,dict)):
        raise ValueError('checkpoint is not bound to supplied digest')
    evidence=state.get('evidence',[])
    if not any(e.get('id')=='E1' and e.get('result')=='pass' and 'A1' in e.get('artifact_ids',[]) for e in evidence if isinstance(e,dict)):
        raise ValueError('missing bound evidence')
    acceptance=state.get('acceptance',[])
    if not any(a.get('criterion')=='Matches expected release fixture' and a.get('status')=='verified' and 'E1' in a.get('evidence_ids',[]) for a in acceptance if isinstance(a,dict)):
        raise ValueError('required bounded criterion absent')
    return {'result':'consistent','scope':'fixed partial snapshot; does not authenticate producer or establish source completeness'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--longhaul',type=Path,required=True)
    for name in ('flowlore','longhaul','makeextreme'):p.add_argument('--'+name+'-rev',required=True)
    a=p.parse_args()
    try: print(json.dumps(verify(a.bundle,a.source,a.longhaul,a.flowlore_rev,a.longhaul_rev,a.makeextreme_rev)))
    except (OSError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired) as exc:
        print(f'handoff refused: {exc}',file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
