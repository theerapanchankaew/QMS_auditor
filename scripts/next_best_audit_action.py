#!/usr/bin/env python3
# 'hartley' on a candidate action is optional: {"dimensions":..., "known_facts":..., "target_dimension":...}.
# When present, evidence_gain is the real log2(k)-bit Hartley measure (see
# hartley_uncertainty.py, references/68-hartley-uncertainty.md) instead of whatever
# score_components.evidence_gain was externally supplied. Absent 'hartley', behavior
# is unchanged from before this file was touched.
import argparse,json
from hartley_uncertainty import information_gain_from_resolving_dimension
KEYS=['evidence_gain','requirement_coverage','contradiction_resolution','systemicity_value','audit_cost','redundancy','speculation_risk']
def resolve_evidence_gain(a):
 h=a.get('hartley')
 if not h: return None
 r=information_gain_from_resolving_dimension(h.get('dimensions') or {}, h.get('known_facts') or {}, h.get('target_dimension',''))
 return r['normalized_information_gain'] if r['status']=='OK' else None
def score(a):
 sc=dict(a.get('score_components',{}))
 hg=resolve_evidence_gain(a)
 if hg is not None: sc['evidence_gain']=hg
 v={k:float(sc.get(k,0)) for k in KEYS}; s=v['evidence_gain']+v['requirement_coverage']+v['contradiction_resolution']+v['systemicity_value']-v['audit_cost']-v['redundancy']-v['speculation_risk']; return s,v
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args(); d=json.load(open(a.input,encoding='utf-8')); ranked=[]
 for x in d.get('candidate_actions',[]):
  s,c=score(x); y=dict(x); y['score']=round(s,6); y['score_components']=c; y['prediction_only']=True; ranked.append(y)
 ranked.sort(key=lambda z:z['score'],reverse=True); json.dump({'ranked_actions':ranked,'recommended_action':ranked[0] if ranked else None},open(a.output,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
