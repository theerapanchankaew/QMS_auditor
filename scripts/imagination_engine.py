#!/usr/bin/env python3
import argparse, copy, hashlib, json
from audit_world_model import ALLOWED, step, stable_hash

def simulate(state, actions, horizon=3):
    if horizon < 1 or horizon > 8:
        raise ValueError('horizon must be between 1 and 8')
    trajectories=[]
    for idx, action in enumerate(actions):
        if action.get('action_type') not in ALLOWED:
            continue
        cur=copy.deepcopy(state)
        nodes=[]
        plan=action.get('plan') or [action]
        for a in plan[:horizon]:
            if a.get('action_type') not in ALLOWED:
                break
            cur=step(cur,a,a.get('predicted_delta'))
            nodes.append({'action':a,'predicted_state':cur})
        trajectories.append({
            'trajectory_id': hashlib.sha256(f"{stable_hash(state)}:{idx}".encode()).hexdigest()[:16],
            'start_state_hash': stable_hash(state),
            'nodes': nodes,
            'simulation': True,
            'epistemic_class':'prediction_only',
            'evidence_status':'not_audit_evidence',
            'release_authority':'none'
        })
    return {'trajectories':trajectories,'horizon':horizon,'prediction_only':True}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--state',required=True); p.add_argument('--actions',required=True); p.add_argument('--horizon',type=int,default=3); p.add_argument('--output',required=True); a=p.parse_args()
    with open(a.state,encoding='utf-8') as f:s=json.load(f)
    with open(a.actions,encoding='utf-8') as f:d=json.load(f)
    out=simulate(s,d.get('candidate_actions',[]),a.horizon)
    with open(a.output,'w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
if __name__=='__main__': main()
