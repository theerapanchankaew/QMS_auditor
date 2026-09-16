#!/usr/bin/env python3
import argparse, copy, hashlib, json

DROP = {'trajectory_id','timestamp','created_at','updated_at','start_state_hash','simulation','last_simulated_action','predicted_delta'}
PREDICTION_FIELDS = {'prediction','predictions','candidate_trajectories','imagined_trajectory'}

def normalize(x):
    if isinstance(x, dict):
        out = {}
        for k in sorted(x):
            if k in DROP or k in PREDICTION_FIELDS:
                continue
            out[k] = normalize(x[k])
        return out
    if isinstance(x, list):
        vals = [normalize(v) for v in x]
        try:
            return sorted(vals, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))
        except TypeError:
            return vals
    return x

def canonical_state(state):
    s = copy.deepcopy(state)
    # Preserve only world-model semantics and assurance position.
    allowed = ['criterion','clause','atomic_requirement_ids','requirement_world','evidence_world','process_world','sampling_state','assurance_state']
    core = {k:s[k] for k in allowed if k in s}
    return normalize(core)

def state_hash(state):
    raw=json.dumps(canonical_state(state),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def equivalent(a,b):
    return canonical_state(a)==canonical_state(b)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--compare'); p.add_argument('--output',required=True); a=p.parse_args()
    with open(a.input,encoding='utf-8') as f:s1=json.load(f)
    out={'canonical_state':canonical_state(s1),'state_hash':state_hash(s1)}
    if a.compare:
        with open(a.compare,encoding='utf-8') as f:s2=json.load(f)
        out['equivalent']=equivalent(s1,s2); out['compare_hash']=state_hash(s2)
    with open(a.output,'w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
if __name__=='__main__': main()
