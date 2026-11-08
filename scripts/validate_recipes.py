#!/usr/bin/env python3
"""Validate catalog recipe contracts and evidence manifests for verified recipes."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]


def validate(catalog, root=ROOT):
    errors=[]
    entries=catalog.get('entries', [])
    ids={e.get('id') for e in entries if isinstance(e,dict)}
    recipes=[e for e in entries if isinstance(e,dict) and e.get('type')=='recipe']
    if not recipes: return ['catalog: no recipes']
    for e in recipes:
        rid=e.get('id','<missing>')
        for key in ('id','title','summary','path','input','output','status'):
            if not isinstance(e.get(key),str) or not e[key].strip(): errors.append(f'{rid}: missing {key}')
        if not isinstance(e.get('sources'),list) or not e['sources'] or any(x not in ids for x in e['sources']):
            errors.append(f'{rid}: missing or unknown sources')
        if not isinstance(rid,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',rid):
            errors.append(f'{rid}: invalid recipe id'); continue
        if e.get('status') not in ('draft','field-tested','verified'):
            errors.append(f'{rid}: invalid status'); continue
        if e.get('status')!='verified': continue
        manifest=root/'evidence'/'recipes'/f'{rid}.json'
        try:
            data=json.loads(manifest.read_text())
            if set(data)!={'schema','recipe','revision','components','command','artifacts'} or type(data['schema']) is not int or data['schema']!=1 or data['recipe']!=rid:
                raise ValueError('invalid manifest fields or recipe binding')
            if not isinstance(data['revision'],str) or not re.fullmatch(r'[0-9a-f]{40}',data['revision']):
                raise ValueError('revision must be a full git commit')
            if not isinstance(data['components'],dict) or not data['components'] or any(not isinstance(k,str) or not k.strip() or not isinstance(v,str) or not re.fullmatch(r'[0-9a-f]{40}',v) for k,v in data['components'].items()):
                raise ValueError('components need full commit pins')
            if not isinstance(data['command'],str) or not data['command'].strip(): raise ValueError('missing reproduction command')
            if not isinstance(data['artifacts'],list) or not data['artifacts']: raise ValueError('missing artifacts')
            for item in data['artifacts']:
                if not isinstance(item,dict) or set(item)!={'path','sha256'}: raise ValueError('invalid artifact record')
                name=item['path']
                if not isinstance(name,str) or Path(name).is_absolute() or '..' in Path(name).parts: raise ValueError('invalid artifact path')
                path=(root/name).resolve()
                if not path.is_relative_to(root.resolve()) or not path.is_file(): raise ValueError('missing or escaped artifact')
                if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']: raise ValueError('artifact hash mismatch')
        except (OSError,ValueError,TypeError,KeyError) as ex:
            errors.append(f'{rid}: evidence invalid: {ex}')
    return errors


def main():
    try: data=json.loads((ROOT/'catalog/catalog.json').read_text())
    except (OSError,ValueError) as ex:
        print(f'catalog: {ex}',file=sys.stderr);return 2
    errors=validate(data)
    for error in errors: print(error,file=sys.stderr)
    if errors: return 1
    print(f"OK — {sum(e.get('type')=='recipe' for e in data['entries'])} recipe contracts valid; verified manifests checked")
    return 0

if __name__=='__main__': raise SystemExit(main())
