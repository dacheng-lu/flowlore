#!/usr/bin/env python3
"""Compare admission policies on real digest subprocesses and injected failures."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import integration

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'evidence/cli-snapshot'
SCENARIOS={'first_success':[True], 'retry_success':[False,True],
           'consecutive_failures':[False,False,False,False],
           'late_success':[False,False,False,True]}


def run(mx, scenario, reserve):
    spec=importlib.util.spec_from_file_location('budget',mx/'makeextreme/budget.py')
    budget=importlib.util.module_from_spec(spec);spec.loader.exec_module(budget)
    remaining,attempts,verified,unverified=9,0,False,False
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='digest-budget-') as tmp:
        d=Path(tmp);good=d/'good.json';bad=d/'bad.json';out=d/'out.md'
        snapshot=json.loads((SOURCE/'snapshot.json').read_text())
        integration.snapshot_fixture(snapshot,good);bad.write_text('{invalid')
        for succeeds in scenario:
            if reserve:
                plan={'version':1,'attempts_used':attempts,'max_attempts':4,'retry_reserve':0,
                      'resources':{'units':{'remaining':remaining,'attempt':2,'recovery':0,'verification':3}}}
                if not budget.assess(plan)['admit']:break
            elif remaining<2:break
            attempts+=1;remaining-=2
            inp=good if succeeds else bad
            p=subprocess.run([sys.executable,str(HERE/'digest.py'),'render',str(inp),'--output',str(out)],capture_output=True,text=True,timeout=10)
            if (p.returncode==0)!=succeeds:raise RuntimeError('injected outcome did not match subprocess result')
            if p.returncode==0:
                if remaining<3:unverified=True;break
                remaining-=3
                p=subprocess.run([sys.executable,str(HERE/'digest.py'),'check',str(good),'--output',str(out),'--expected',str(SOURCE/'expected.md')],capture_output=True,text=True,timeout=10)
                if p.returncode!=0:raise RuntimeError('verification failed unexpectedly')
                verified=True;break
    return {'verified':verified,'unverified':unverified,'attempts':attempts,'modeled_units_spent':9-remaining,'wall_seconds':round(time.monotonic()-start,6)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--makeextreme',type=Path,required=True);a=p.parse_args()
    results={name:{'baseline':run(a.makeextreme.resolve(),trace,False),'reserve':run(a.makeextreme.resolve(),trace,True)} for name,trace in SCENARIOS.items()}
    print(json.dumps({'results':results,'limitations':['modeled units are not money or wall-time limits','fixed small cases, not statistical inference','no model, external publishing or real recovery action']},indent=2))

if __name__=='__main__':main()
