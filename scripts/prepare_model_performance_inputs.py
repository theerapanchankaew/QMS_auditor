#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
LEAK_KEYS={"expected_verdict","expected_nc_class","finding_expected_verdict","finding_expected_nc_class","answer_rationale","finding_basis","trigger_or_anchor","gold_verdict","gold_nc_class","verdict","nc_class","expected_clause","expected_trigger_or_anchor"}

def load_jsonl(path):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip(): yield json.loads(line)

def main():
    p=argparse.ArgumentParser(description="Prepare sanitized QMS model performance inputs and prediction template.")
    p.add_argument("--source", required=True)
    p.add_argument("--outdir", required=True)
    args=p.parse_args(); out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    sanitized=[]; template=[]; removed={}
    for r in load_jsonl(args.source):
        cid=r.get("case_id")
        clean={k:v for k,v in r.items() if k not in LEAK_KEYS}
        removed[cid]=[k for k in r if k in LEAK_KEYS]
        sanitized.append(clean)
        template.append({"case_id":cid,"predicted_verdict":"ReviewRequired","predicted_nc_class":"None","predicted_clause":None,"predicted_trigger_or_anchor":None,"rationale":""})
    (out/"qms_test_inputs_sanitized_no_labels.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in sanitized)+"\n", encoding="utf-8")
    (out/"model_predictions_template.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in template)+"\n", encoding="utf-8")
    (out/"sanitization_report.json").write_text(json.dumps({"records":len(sanitized),"removed_fields_by_case_id":removed}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status":"passed","records":len(sanitized),"outdir":str(out)}, indent=2))
if __name__ == "__main__": main()
