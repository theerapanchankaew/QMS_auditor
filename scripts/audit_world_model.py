#!/usr/bin/env python3
import argparse, copy, hashlib, json

ALLOWED = {
    'ask_question','request_document_or_record','sample_record','interview_role',
    'observe_activity','trace_process','cross_check','expand_sample'
}
FORBIDDEN_FIELDS = {'verdict','nc_class','trigger_or_anchor','breach_proven'}

def stable_hash(obj):
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def validate_state(state):
    required = ['case_id','requirement_world','evidence_world','process_world','assurance_state']
    missing = [k for k in required if k not in state]
    if missing:
        raise ValueError('missing AuditState fields: ' + ','.join(missing))
    if state.get('epistemic_class') not in (None, 'prediction_only', 'observed_state'):
        raise ValueError('invalid epistemic_class')

def step(state, action, predicted_delta=None):
    validate_state(state)
    action_type = action.get('action_type')
    if action_type not in ALLOWED:
        raise ValueError('forbidden action_type')
    nxt = copy.deepcopy(state)
    for key in FORBIDDEN_FIELDS:
        nxt.pop(key, None)
    nxt['simulation'] = True
    nxt['epistemic_class'] = 'prediction_only'
    nxt['evidence_status'] = 'not_audit_evidence'
    nxt['release_authority'] = 'none'
    nxt['start_state_hash'] = stable_hash(state)
    nxt['last_simulated_action'] = action
    if predicted_delta:
        nxt['predicted_delta'] = predicted_delta
    # Never mutate authoritative assurance state from simulation.
    nxt['assurance_state'] = copy.deepcopy(state['assurance_state'])
    return nxt

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--state', required=True)
    p.add_argument('--action', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--predicted-delta')
    a=p.parse_args()
    with open(a.state, encoding='utf-8') as f: s=json.load(f)
    with open(a.action, encoding='utf-8') as f: ac=json.load(f)
    delta=None
    if a.predicted_delta:
        with open(a.predicted_delta, encoding='utf-8') as f: delta=json.load(f)
    with open(a.output,'w',encoding='utf-8') as f:
        json.dump(step(s,ac,delta),f,ensure_ascii=False,indent=2)

if __name__=='__main__': main()
