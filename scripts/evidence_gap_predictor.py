#!/usr/bin/env python3
import argparse,json

def gaps(obj):
 observed=set(obj.get('observed_states',[])); out=[]
 for x in obj.get('expected_states',[]):
  if x not in observed:
   out.append({'expected_state':x,'gap_type':'missing','investigation_priority':0.5,'candidate_audit_actions':['request_corresponding_objective_evidence'],'epistemic_class':'prediction_only','breach_proven':False})
 return {'case_id':obj.get('case_id',''),'gap_candidates':out,'invariant':'MissingEvidence != ProvenBreach'}
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args(); d=json.load(open(a.input,encoding='utf-8')); json.dump(gaps(d),open(a.output,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
