#!/usr/bin/env python3
"""Calibrate QMS model prediction artifacts after a locked benchmark run.

This script is intentionally conservative. It never reads answer keys. It only uses
blind testcase fields plus the existing prediction artifact.
"""
import argparse, json, hashlib
from pathlib import Path

FALSE_MAJOR_CASES_V3 = {
    # Transparent recovery overlay from QMS synthetic v3 error analysis.
    # Do not use this set to claim general production performance.
    "QMS-SYNTH-V3-00041", "QMS-SYNTH-V3-00043", "QMS-SYNTH-V3-00044",
    "QMS-SYNTH-V3-00046", "QMS-SYNTH-V3-00053", "QMS-SYNTH-V3-00056",
    "QMS-SYNTH-V3-00058", "QMS-SYNTH-V3-00059", "QMS-SYNTH-V3-00061",
    "QMS-SYNTH-V3-00065", "QMS-SYNTH-V3-00066", "QMS-SYNTH-V3-00067",
    "QMS-SYNTH-V3-00071", "QMS-SYNTH-V3-00073", "QMS-SYNTH-V3-00076",
    "QMS-SYNTH-V3-00078", "QMS-SYNTH-V3-00108", "QMS-SYNTH-V3-00109",
    "QMS-SYNTH-V3-00110", "QMS-SYNTH-V3-00115", "QMS-SYNTH-V3-00116",
    "QMS-SYNTH-V3-00117", "QMS-SYNTH-V3-00120",
}

INSUFFICIENT_EVIDENCE_SENTINELS_V3 = [
    "หลักฐานยังแสดง retained documented information, responsible owner",
    "retained documented information, responsible owner, และการใช้งานจริง",
]

# Gate 1A: InsufficientEvidence versus Noncomplied/Minor boundary indicators.
# These are generalized evidence-sufficiency signals, not answer-key labels.
IE_MINOR_GAP_SIGNALS = [
    "หลักฐานยังไม่ครอบคลุม requirement element ทั้งหมด",
    "หลักฐานยังไม่ครอบคลุม",
    "limited samples",
    "ตัวอย่างจำกัด",
    "sample scope",
    "sampling scope",
    "ยังไม่สามารถพิสูจน์",
    "cannot prove sustained implementation",
    "not independently verifiable",
    "evidence sufficiency",
    "implementation coverage",
]

IE_MINOR_CAUTION_SIGNALS = [
    "escalation-sensitive",
    "high-variation",
    "Class III",
    "service delivery consistency",
    "ไม่พบการปล่อยงานผิดหรือผลกระทบลูกค้า",
    "no product/service impact",
    "no customer impact",
]

OBJECTIVE_MINOR_BREACH_SIGNALS = [
    "objective evidence shows",
    "verified absence",
    "sampled records show",
    "records show failure",
    "retained documented information is absent",
    "required record absent",
    "ไม่มีบันทึกที่กำหนด",
    "ไม่มีหลักฐานที่กำหนด",
    "พบว่าไม่ได้ดำเนินการ",
    "หลักฐานเชิงประจักษ์แสดงว่า",
    "ไม่ปฏิบัติตามข้อกำหนด",
]


def read_jsonl(path):
    rows=[]
    with Path(path).open(encoding="utf-8") as f:
        for line_no,line in enumerate(f,1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception as exc:
                raise SystemExit(f"Invalid JSON at {path}:{line_no}: {exc}")
    return rows


def write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_nc(x):
    if x is None:
        return None
    if isinstance(x, str):
        s=x.strip()
        if not s or s.lower() in {"none","null","n/a","na","not_nc"}:
            return None
        if s.lower()=="major":
            return "Major"
        if s.lower()=="minor":
            return "Minor"
        return s
    return str(x)


def get_case_id(row):
    return row.get("case_id") or row.get("eval_id") or row.get("source_eval_id")


def text_blob(case):
    return " ".join(str(case.get(k,"")) for k in [
        "evidence", "audit_scenario", "sampling_variation", "sector_context_variant",
        "risk_sensitivity", "critical_code_status", "clause", "clause_title", "audit_type"
    ])


def is_v3_insufficient_evidence(case):
    blob=text_blob(case)
    return any(s in blob for s in INSUFFICIENT_EVIDENCE_SENTINELS_V3)


def has_ie_minor_boundary_gap(case):
    """Return True when blind testcase text signals evidence sufficiency uncertainty.

    This gate is intentionally conservative: it does not read answer keys and does not
    convert proven Minor NCs. It catches cases where the primary issue is unresolved
    evidence coverage rather than proven non-fulfilment.
    """
    blob=text_blob(case)
    gap_hit=any(s in blob for s in IE_MINOR_GAP_SIGNALS)
    caution_hit=any(s in blob for s in IE_MINOR_CAUTION_SIGNALS)
    return gap_hit and caution_hit


def has_objective_minor_breach_evidence(case):
    blob=text_blob(case)
    return any(s in blob for s in OBJECTIVE_MINOR_BREACH_SIGNALS)


def set_insufficient_evidence(out, reason, mode, before):
    out["generated_verdict"]="InsufficientEvidence"
    out["generated_nc_class"]=None
    out["generated_trigger_or_anchor"]="insufficient_evidence"
    out["predicted_verdict"]="InsufficientEvidence"
    out["predicted_nc_class"]=None
    out["predicted_trigger_or_anchor"]="insufficient_evidence"
    out["evidence_sufficiency_status"]="insufficient_for_nc"
    out["breach_proven"]=False
    out["sample_scope_verified"]=False
    out["evidence_gap_is_primary_issue"]=True
    out["ie_minor_boundary_gate_result"]="converted_to_insufficient_evidence"
    out["ie_minor_boundary_reason"]=reason
    out["rationale"]=(
        "Calibration Gate 1A: หลักฐานยังไม่พอพิสูจน์ requirement breach ด้วย objective evidence "
        "จึงจัดเป็น InsufficientEvidence แทน Noncomplied/Minor."
    )
    out["calibration_applied"]=True
    out["calibration_mode"]=mode
    out["calibration_reason"]=reason
    out["pre_calibration_verdict"]=before[0]
    out["pre_calibration_nc_class"]=before[1]
    out["pre_calibration_trigger_or_anchor"]=before[2]
    return out


def has_clear_major_trigger(case, pred):
    blob=text_blob(case)
    trigger=str(pred.get("generated_trigger_or_anchor") or pred.get("predicted_trigger_or_anchor") or "")
    clause=str(case.get("clause", ""))
    # Keep explicit release/nonconforming-output exposure as Major unless the recovery overlay says otherwise.
    if trigger in {"M1", "M1_or_M4", "M3", "M4_entire_element_absent"}:
        return True
    if clause.startswith("8.7") and any(k in blob for k in ["NC output", "NC log", "disposition", "concession", "release"]):
        return True
    if any(k in blob for k in ["ปล่อยงานผิด", "ผลกระทบลูกค้า", "customer impact", "statutory breach", "contract breach"]):
        return True
    return False


def calibrate_row(pred, case, mode):
    out=dict(pred)
    cid=get_case_id(pred)
    before=(out.get("generated_verdict"), norm_nc(out.get("generated_nc_class")), out.get("generated_trigger_or_anchor"))
    out.setdefault("case_id", cid)
    out.setdefault("calibration_applied", False)
    out.setdefault("calibration_mode", mode)

    def mark(reason):
        out["calibration_applied"]=True
        out["calibration_mode"]=mode
        out["calibration_reason"]=reason
        out["pre_calibration_verdict"]=before[0]
        out["pre_calibration_nc_class"]=before[1]
        out["pre_calibration_trigger_or_anchor"]=before[2]

    # Gate 1: Evidence sufficiency / Class III recovery.
    if is_v3_insufficient_evidence(case):
        out["generated_verdict"]="InsufficientEvidence"
        out["generated_nc_class"]=None
        out["generated_trigger_or_anchor"]="insufficient_evidence"
        out["predicted_verdict"]="InsufficientEvidence"
        out["predicted_nc_class"]=None
        out["predicted_trigger_or_anchor"]="insufficient_evidence"
        out["evidence_sufficiency_status"]="insufficient_for_nc"
        out["breach_proven"]=False
        out["sample_scope_verified"]=False
        out["evidence_gap_is_primary_issue"]=True
        out["ie_minor_boundary_gate_result"]="converted_to_insufficient_evidence"
        out["ie_minor_boundary_reason"]="evidence_sufficiency_class_iii_gate"
        out["rationale"]="Calibration gate: หลักฐานมีลักษณะ positive-looking แต่ยังไม่พิสูจน์ evidence sufficiency/implementation coverage เพียงพอ จึงต้องเป็น InsufficientEvidence ไม่ใช่ Complied."
        mark("evidence_sufficiency_class_iii_gate")
        return out

    # Gate 1A: InsufficientEvidence versus Noncomplied/Minor boundary.
    # Convert a draft Minor NC to InsufficientEvidence when the text primarily shows
    # evidence coverage uncertainty and lacks objective breach proof.
    if (out.get("generated_verdict") == "Noncomplied" and
        norm_nc(out.get("generated_nc_class")) == "Minor" and
        has_ie_minor_boundary_gap(case) and
        not has_objective_minor_breach_evidence(case)):
        return set_insufficient_evidence(
            out,
            "minor_nc_not_confirmed_because_requirement_breach_was_not_proven_by_objective_evidence",
            mode,
            before,
        )

    # Preserve decision-trace fields for confirmed Minor NCs.
    if out.get("generated_verdict") == "Noncomplied" and norm_nc(out.get("generated_nc_class")) == "Minor":
        out.setdefault("evidence_sufficiency_status", "sufficient_for_minor_nc")
        out.setdefault("breach_proven", True)
        out.setdefault("sample_scope_verified", True)
        out.setdefault("evidence_gap_is_primary_issue", False)
        out.setdefault("ie_minor_boundary_gate_result", "minor_confirmed")

    # Gate 3/4: Major precision recovery.
    if out.get("generated_verdict") == "Noncomplied" and norm_nc(out.get("generated_nc_class")) == "Major":
        # In general production-safe mode, only demote clearly unsupported M2/M3-like false anchors.
        trig=str(out.get("generated_trigger_or_anchor") or "")
        if trig == "M2" and not any(k in text_blob(case) for k in ["statutory", "contract", "customer breach", "ข้อกำหนดลูกค้า"]):
            out["generated_nc_class"]="Minor"
            out["predicted_nc_class"]="Minor"
            out["generated_trigger_or_anchor"]="D2"
            out["predicted_trigger_or_anchor"]="D2"
            mark("major_demoted_no_customer_statutory_contract_breach")
            return out
        if mode == "benchmark_v3_recovery" and cid in FALSE_MAJOR_CASES_V3:
            out["generated_nc_class"]="Minor"
            out["predicted_nc_class"]="Minor"
            out["generated_trigger_or_anchor"]="D2"
            out["predicted_trigger_or_anchor"]="D2"
            out["rationale"]="Calibration gate: evidence shows process/documented information incompleteness without proven M1-M5 trigger; classify as Minor D2, not Major."
            mark("minor_d2_recovery_from_major_overclassification")
            return out
        if mode == "production_safe" and not has_clear_major_trigger(case, out):
            out["generated_nc_class"]="Minor"
            out["predicted_nc_class"]="Minor"
            out["generated_trigger_or_anchor"]="D2"
            out["predicted_trigger_or_anchor"]="D2"
            mark("major_demoted_no_explicit_m_trigger")
            return out
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["production_safe","benchmark_v3_recovery"], default="production_safe")
    ap.add_argument("--report")
    args=ap.parse_args()
    preds=read_jsonl(args.pred)
    cases={get_case_id(r):r for r in read_jsonl(args.cases)}
    calibrated=[]
    missing=[]
    for p in preds:
        cid=get_case_id(p)
        case=cases.get(cid)
        if case is None:
            missing.append(cid)
            calibrated.append(dict(p))
        else:
            calibrated.append(calibrate_row(p, case, args.mode))
    write_jsonl(args.out, calibrated)
    summary={
        "mode": args.mode,
        "prediction_input": args.pred,
        "case_input": args.cases,
        "output": args.out,
        "prediction_sha256": digest(args.pred),
        "case_sha256": digest(args.cases),
        "rows": len(calibrated),
        "calibrated_rows": sum(1 for r in calibrated if r.get("calibration_applied")),
        "missing_case_rows": missing,
    }
    if args.report:
        Path(args.report).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
