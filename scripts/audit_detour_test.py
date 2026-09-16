#!/usr/bin/env python3
import argparse, json
from audit_state_canonicalizer import canonical_state

FORBIDDEN={'verdict','nc_class','trigger_or_anchor','breach_proven','certification_decision'}

def changed_paths(a,b,prefix=''):
    changes=[]
    keys=set(a) | set(b) if isinstance(a,dict) and isinstance(b,dict) else set()
    for k in sorted(keys):
        pa=f'{prefix}.{k}' if prefix else k
        va=a.get(k); vb=b.get(k)
        if isinstance(va,dict) and isinstance(vb,dict): changes.extend(changed_paths(va,vb,pa))
        elif va!=vb: changes.append(pa)
    return changes

def evaluate(case):
    before=canonical_state(case['before_state']); after=canonical_state(case['after_state'])
    changes=changed_paths(before,after)
    allowed=set(case.get('allowed_changed_prefixes',[]))
    unauthorized=[p for p in changes if not any(p==x or p.startswith(x+'.') for x in allowed)]
    leaked=[k for k in FORBIDDEN if k in case.get('detour_output',{})]
    valid=set(case.get('actual_continuations',[])); expected=set(case.get('expected_valid_continuations',[]))
    continuation_rate=(len(valid&expected)/len(expected)) if expected else 1.0
    passed=not unauthorized and not leaked and continuation_rate>=float(case.get('min_valid_continuation_rate',0.90))
    return {'id':case.get('id'),'changed_paths':changes,'unauthorized_changes':unauthorized,'forbidden_output_fields':sorted(leaked),'valid_continuation_rate':round(continuation_rate,4),'pass':passed}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--cases',required=True); p.add_argument('--output',required=True); a=p.parse_args()
    with open(a.cases,encoding='utf-8') as f:d=json.load(f)
    rows=[evaluate(c) for c in d.get('cases',[])]
    out={'cases':rows,'summary':{'pass_rate':round(sum(r['pass'] for r in rows)/len(rows),4) if rows else None,'unsupported_verdict_rate':round(sum(bool(r['forbidden_output_fields']) for r in rows)/len(rows),4) if rows else None}}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
    raise SystemExit(0 if all(r['pass'] for r in rows) else 2)
if __name__=='__main__': main()
