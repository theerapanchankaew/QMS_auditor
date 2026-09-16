#!/usr/bin/env python3
import argparse,json,sys
BAD={'prediction_only', 'simulation'}
def check(d):
 leaks=[]
 for i,x in enumerate(d.get('decisive_support',[])):
  if x.get('epistemic_class')=='prediction_only' or x.get('simulation') is True or x.get('evidence_status')=='not_audit_evidence': leaks.append(i)
 return {'gate':'PE-1','result':'FAIL' if leaks else 'PASS','leak_indices':leaks,'rule':'Predictions may guide investigation but may not support a material audit conclusion.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output'); a=p.parse_args(); d=json.load(open(a.input,encoding='utf-8')); r=check(d); txt=json.dumps(r,ensure_ascii=False,indent=2); open(a.output,'w',encoding='utf-8').write(txt) if a.output else print(txt); sys.exit(2 if r['result']=='FAIL' else 0)
