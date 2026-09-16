#!/usr/bin/env python3
import argparse, json, sys
REQUIRED=["standard","mode","route","clause_candidates","sources_used","gates_passed","verdict","nc_class","review_required"]
ALLOWED_VERDICTS={"Informational","Complied","Noncomplied","OFI","OBS","InsufficientEvidence","ReferenceGap","ReviewRequired","OUT_OF_SCOPE"}
ALLOWED_NC={"Major","Minor","None",None,""}

def main():
    p=argparse.ArgumentParser(description="Validate QMS decision trace JSON.")
    p.add_argument("file")
    args=p.parse_args()
    data=json.load(open(args.file, encoding="utf-8"))
    errors=[]
    miss=[k for k in REQUIRED if k not in data]
    if miss: errors.append(f"missing required fields: {miss}")
    if data.get("verdict") not in ALLOWED_VERDICTS: errors.append("invalid verdict")
    if data.get("nc_class") not in ALLOWED_NC: errors.append("invalid nc_class")
    if data.get("verdict") != "Noncomplied" and data.get("nc_class") in {"Major","Minor"}: errors.append("Major/Minor only allowed when verdict is Noncomplied")
    if data.get("verdict") == "Noncomplied" and data.get("nc_class") in {None,"","None"}:
        errors.append("Noncomplied requires Major or Minor nc_class")
    if not isinstance(data.get("gates_passed",[]), list): errors.append("gates_passed must be a list")
    if errors:
        print(json.dumps({"status":"failed","errors":errors}, indent=2)); return 1
    print(json.dumps({"status":"passed","file":args.file}, indent=2)); return 0
if __name__ == "__main__": sys.exit(main())
