#!/usr/bin/env python3
import argparse, json

FORBIDDEN={'breach_proven','verdict','nc_class','trigger_or_anchor','certification_decision','release_authority'}
ALLOWED_TOP={'evidence_world','process_world','sampling_state','uncertainty','information_gain','candidate_next_actions'}

def validate(obj):
    errors=[]
    if obj.get('epistemic_class')!='prediction_only': errors.append('EPISTEMIC_CLASS_REQUIRED')
    delta=obj.get('predicted_delta',{})
    for k in delta:
        if k in FORBIDDEN: errors.append('FORBIDDEN_AUTHORITATIVE_FIELD:'+k)
        if k not in ALLOWED_TOP: errors.append('UNAPPROVED_DELTA_FIELD:'+k)
    if any(k in obj for k in FORBIDDEN): errors.append('AUTHORITATIVE_FIELD_AT_TOP_LEVEL')
    return {'valid':not errors,'errors':errors,'planning_only':True}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args()
    with open(a.input,encoding='utf-8') as f:d=json.load(f)
    out=validate(d)
    with open(a.output,'w',encoding='utf-8') as f:json.dump(out,f,indent=2)
    raise SystemExit(0 if out['valid'] else 2)
if __name__=='__main__': main()
