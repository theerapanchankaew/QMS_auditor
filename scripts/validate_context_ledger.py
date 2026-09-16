#!/usr/bin/env python3
import argparse, json, sys
REQUIRED = ["task_mode", "route", "loaded_sources", "excluded_sources", "evidence_inventory", "open_questions", "decision_state"]

def main():
    p=argparse.ArgumentParser(description="Validate QMS context ledger JSON.")
    p.add_argument("file")
    args=p.parse_args()
    data=json.load(open(args.file, encoding="utf-8"))
    missing=[k for k in REQUIRED if k not in data]
    errors=[]
    if missing: errors.append(f"missing required fields: {missing}")
    for k in ["loaded_sources","excluded_sources","evidence_inventory","open_questions"]:
        if k in data and not isinstance(data[k], list): errors.append(f"{k} must be a list")
    if "web" not in [str(x).lower() for x in data.get("excluded_sources",[])]: errors.append("excluded_sources should include web")
    if errors:
        print(json.dumps({"status":"failed","errors":errors}, indent=2)); return 1
    print(json.dumps({"status":"passed","file":args.file}, indent=2)); return 0
if __name__ == "__main__": sys.exit(main())
