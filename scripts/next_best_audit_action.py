#!/usr/bin/env python3
import argparse,json
KEYS=['evidence_gain','requirement_coverage','contradiction_resolution','systemicity_value','audit_cost','redundancy','speculation_risk']
def score(a):
 v={k:float(a.get('score_components',{}).get(k,0)) for k in KEYS}; s=v['evidence_gain']+v['requirement_coverage']+v['contradiction_resolution']+v['systemicity_value']-v['audit_cost']-v['redundancy']-v['speculation_risk']; return s,v
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args(); d=json.load(open(a.input,encoding='utf-8')); ranked=[]
 for x in d.get('candidate_actions',[]):
  s,c=score(x); y=dict(x); y['score']=round(s,6); y['score_components']=c; y['prediction_only']=True; ranked.append(y)
 ranked.sort(key=lambda z:z['score'],reverse=True); json.dump({'ranked_actions':ranked,'recommended_action':ranked[0] if ranked else None},open(a.output,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
