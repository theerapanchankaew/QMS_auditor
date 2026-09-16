#!/usr/bin/env python3
# Canonical S0-S11 assurance-boundary state machine. See docs/eei-blueprint-crosswalk.md
# before adding another "state_machine.py" -- extend this one instead. Note: S6-S11
# here diverge from the EEI deck's S6-S11 content (crosswalk doc has the detail), and
# this only checks transition validity generically, not per-state entry/exit contracts.
import argparse, json

STATES=['S0_RECEIVED','S1_PREFLIGHT','S2_NORMALIZED','S3_MAPPED','S4_SUFFICIENCY','S5_BREACH_TEST','S6_EXPOSURE','S7_SEVERITY','S8_GROUNDING','S9_HUMAN_REVIEW','S10_RELEASED','S11_MONITORED']

def check(payload):
    current=payload.get('current_state')
    requested=payload.get('requested_state')
    artifact_class=payload.get('artifact_epistemic_class','observed_state')
    if current not in STATES or requested not in STATES:
        return {'allowed':False,'code':'INVALID_STATE'}
    if STATES.index(requested) > STATES.index(current)+1:
        return {'allowed':False,'code':'STATE_SKIP_FORBIDDEN'}
    if artifact_class=='prediction_only' and STATES.index(requested)>=STATES.index('S4_SUFFICIENCY'):
        return {'allowed':False,'code':'PREDICTION_CANNOT_ADVANCE_ASSURANCE'}
    if requested=='S10_RELEASED' and not payload.get('human_review_completed',False):
        return {'allowed':False,'code':'HUMAN_REVIEW_REQUIRED'}
    return {'allowed':True,'code':'PASS'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args()
    with open(a.input,encoding='utf-8') as f:d=json.load(f)
    out=check(d)
    with open(a.output,'w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
    raise SystemExit(0 if out['allowed'] else 2)
if __name__=='__main__': main()
