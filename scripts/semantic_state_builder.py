#!/usr/bin/env python3
import argparse,json

def build(obj):
    return {"case_id":obj.get("case_id",""),"clause":obj.get("clause",""),"atomic_requirement_ids":obj.get("atomic_requirement_ids",[]),"process":obj.get("process",""),"observed_states":obj.get("observed_states",[]),"expected_states":obj.get("expected_states",[]),"evidence_classes":obj.get("evidence_classes",[]),"support_relations":obj.get("support_relations",[]),"contradiction_relations":obj.get("contradiction_relations",[]),"missing_state_candidates":obj.get("missing_state_candidates",[]),"confidence":float(obj.get("confidence",0.0)),"epistemic_class":"prediction_only","evidence_status":"not_audit_evidence"}
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args()
 data=json.load(open(a.input,encoding='utf-8')); json.dump(build(data),open(a.output,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
