
import { useState, useEffect, useRef } from "react";

// ── Data ───────────────────────────────────────────────────────────────────
const BENCHMARK_HISTORY = [
  {
    version:"v5.1",round:1,date:"2026-06-01",
    metrics:{composite_macro_f1:0.668,verdict_macro_f1:0.686,major_precision:0.941,major_recall:0.533,major_f1:0.690,minor_f1:0.908,ofi_f1:1.000,ie_recall:0.000,ie_f1:0.000,clause_accuracy:1.000,binary_f1:0.844,binary_precision:1.000,binary_recall:0.942},
    gates:{system_macro_f1:false,noncomplied_f1:true,major_precision:true,major_recall:false,ie_handling:false},
    gates_passed:1,upskill:"none",
    failure:"Major under-escalation: 14 Major→Minor; IE collapse 0/21",
    refs_applied:[],
  },
  {
    version:"v5.2",round:2,date:"2026-06-02",
    metrics:{composite_macro_f1:0.825,verdict_macro_f1:0.686,major_precision:0.566,major_recall:1.000,major_f1:0.723,minor_f1:0.826,ofi_f1:1.000,ie_recall:0.000,ie_f1:0.000,clause_accuracy:1.000,binary_f1:0.939,binary_precision:0.941,binary_recall:1.000},
    gates:{system_macro_f1:false,noncomplied_f1:true,major_precision:false,major_recall:true,ie_handling:false},
    gates_passed:2,upskill:"ref-36 Major escalation gate + ref-37 IE gate",
    failure:"Over-correction: 23 Minor→Major; IE still 0/21",
    refs_applied:["ref-36","ref-37"],
  },
  {
    version:"v5.3",round:3,date:"2026-06-03",
    metrics:{composite_macro_f1:0.624,verdict_macro_f1:0.686,major_precision:null,major_recall:null,major_f1:null,minor_f1:0.826,ofi_f1:1.000,ie_recall:0.000,ie_f1:0.000,clause_accuracy:1.000,binary_f1:0.939,binary_precision:1.000,binary_recall:0.884},
    gates:{system_macro_f1:false,noncomplied_f1:true,major_precision:false,major_recall:null,ie_handling:false},
    gates_passed:2,upskill:"ref-38 Human logic calibration",
    failure:"Oscillation: composite↓0.624; 20 false-negative NC→Complied",
    refs_applied:["ref-36","ref-37","ref-38"],
  },
  {
    version:"v5.4",round:4,date:"2026-06-04",
    metrics:{composite_macro_f1:0.660,verdict_macro_f1:0.686,major_precision:0.566,major_recall:1.000,major_f1:0.723,minor_f1:0.826,ofi_f1:1.000,ie_recall:0.000,ie_f1:0.000,clause_accuracy:1.000,binary_f1:0.939,binary_precision:1.000,binary_recall:1.000},
    gates:{system_macro_f1:false,noncomplied_f1:true,major_precision:false,major_recall:true,ie_handling:false},
    gates_passed:3,upskill:"ref-39 IE/Complied boundary + ref-40 Severity anchor",
    failure:"IE recall 0/21 every round; Major FP=23 unchanged",
    refs_applied:["ref-36","ref-37","ref-38","ref-39","ref-40"],
  },
  {
    version:"v5.5",round:5,date:"2026-06-05",
    metrics:{composite_macro_f1:0.783,verdict_macro_f1:0.896,major_precision:0.566,major_recall:1.000,major_f1:0.723,minor_f1:0.826,ofi_f1:1.000,ie_recall:0.000,ie_f1:0.000,clause_accuracy:1.000,binary_f1:0.939,binary_precision:0.991,binary_recall:1.000},
    gates:{system_macro_f1:false,noncomplied_f1:true,major_precision:false,major_recall:true,ie_handling:false},
    gates_passed:3,upskill:"ref-41 Deterministic Harness spec + harness_gate_executor.py",
    failure:"IE collapse structural; Major precision 0.566 stuck",
    refs_applied:["ref-36","ref-37","ref-38","ref-39","ref-40","ref-41"],
  },
];

const BASELINE = {
  version:"v5.5-DH",
  locked_date:"2026-06-06",
  locked_by:"myThee / MASCI",
  metrics:{
    composite_macro_f1:0.783, verdict_macro_f1:0.896,
    major_precision:0.566, major_recall:1.000, major_f1:0.723,
    minor_f1:0.826, ofi_f1:1.000, ie_recall:0.000,
    clause_accuracy:1.000, binary_f1:0.939,
    binary_precision:0.991, binary_recall:1.000,
  },
  targets:{
    composite_macro_f1:0.850, verdict_macro_f1:0.920,
    major_precision:0.900, major_recall:0.880, major_f1:0.890,
    minor_f1:0.900, ofi_f1:1.000, ie_recall:0.800,
    clause_accuracy:1.000, binary_f1:0.950,
    binary_precision:0.990, binary_recall:0.990,
  },
  drift_thresholds:{
    f1_drop_per_window:-0.020,
    f1_consecutive_windows:3,
    psi_verdict_shift:0.250,
    ie_recall_floor:0.700,
    major_precision_floor:0.800,
  },
  immutable_gates:[
    {id:"G0",name:"Closed-source preflight"},
    {id:"G1",name:"Linguistic trigger classifier"},
    {id:"G2",name:"IE Hard Stop (4-step chain)"},
    {id:"G3",name:"D2-safe ceiling check"},
    {id:"G4",name:"M4 three-condition test"},
    {id:"G6",name:"Complied C1–C4 pre-conditions"},
    {id:"G7",name:"Calibration trace required"},
  ],
};

const DRIFT_EVENTS = [
  {ts:"2026-06-02",skill:"qms-auditor-iso-9001-2026",rule:"over_correction",metric:"major_precision",severity:"critical",detail:"major_precision 0.941→0.566 after ref-36 over-escalation"},
  {ts:"2026-06-03",skill:"qms-auditor-iso-9001-2026",rule:"f1_drop_consecutive_windows",metric:"composite_macro_f1",severity:"warning",detail:"composite_f1 0.825→0.624 oscillation"},
  {ts:"2026-06-01",skill:"qms-auditor-iso-9001-2026",rule:"stuck_metric",metric:"ie_recall",severity:"critical",detail:"ie_recall=0.000 for 5 consecutive rounds — structural fix required"},
  {ts:"2026-06-04",skill:"qms-auditor-iso-9001-2026",rule:"psi_verdict_shift",metric:"psi",severity:"warning",detail:"verdict distribution shift PSI=0.31 after probabilistic upskill"},
];

const GATE_STATUS = [
  {id:"G0",name:"Closed-source preflight",type:"immutable",status:"pass",coverage:"100%"},
  {id:"G1",name:"Linguistic trigger",type:"immutable",status:"pass",coverage:"100%"},
  {id:"G2",name:"IE Hard Stop",type:"immutable",status:"enforced",coverage:"21/21 pending"},
  {id:"G3",name:"D2-safe ceiling",type:"immutable",status:"enforced",coverage:"18 clauses"},
  {id:"G4",name:"M4 three-condition",type:"immutable",status:"enforced",coverage:"22 clauses"},
  {id:"G6",name:"Complied C1–C4",type:"immutable",status:"enforced",coverage:"all Complied"},
  {id:"G7",name:"Calibration trace",type:"immutable",status:"enforced",coverage:"all verdicts"},
];

// ── Utils ──────────────────────────────────────────────────────────────────
const fmt = (v, d=3) => v == null ? "—" : v.toFixed(d);
const pct = (v) => v == null ? "—" : (v*100).toFixed(1)+"%";

function statusColor(v, target) {
  if (v == null) return "#888";
  if (v >= target) return "#3B8A0F";
  if (v >= target - 0.05) return "#B35C00";
  return "#C0392B";
}

// ── Tiny Sparkline ─────────────────────────────────────────────────────────
function Sparkline({ data, width=120, height=32, color="#3B8A0F", baseline, target }) {
  const valid = data.filter(d => d != null);
  if (!valid.length) return <span style={{color:"#888",fontSize:11}}>no data</span>;
  const min = Math.min(...valid, baseline||99, target||99) - 0.05;
  const max = Math.max(...valid, baseline||0, target||0) + 0.05;
  const range = max - min || 0.01;
  const pts = data.map((d, i) => {
    if (d == null) return null;
    const x = (i / (data.length - 1)) * (width - 8) + 4;
    const y = height - ((d - min) / range) * (height - 8) - 4;
    return `${x},${y}`;
  }).filter(Boolean);
  const targetY = height - ((target - min) / range) * (height - 8) - 4;
  const baseY = height - ((baseline - min) / range) * (height - 8) - 4;
  const last = valid[valid.length - 1];
  const lc = statusColor(last, target);
  return (
    <svg width={width} height={height} style={{overflow:"visible"}}>
      {target != null && (
        <line x1={0} y1={targetY} x2={width} y2={targetY}
          stroke="#3B8A0F" strokeWidth={0.8} strokeDasharray="3,2" opacity={0.5}/>
      )}
      {baseline != null && (
        <line x1={0} y1={baseY} x2={width} y2={baseY}
          stroke="#888" strokeWidth={0.6} strokeDasharray="2,2" opacity={0.4}/>
      )}
      <polyline points={pts.join(" ")} fill="none" stroke={lc} strokeWidth={1.5}
        strokeLinejoin="round" strokeLinecap="round"/>
      {pts.map((pt, i) => {
        const [x, y] = pt.split(",").map(Number);
        return <circle key={i} cx={x} cy={y} r={2} fill={lc}/>;
      })}
    </svg>
  );
}

// ── Release Gate Badge ─────────────────────────────────────────────────────
function GateBadge({ pass, label }) {
  return (
    <span style={{
      display:"inline-flex", alignItems:"center", gap:4,
      fontSize:10, fontWeight:600, padding:"2px 7px", borderRadius:20,
      background: pass===null?"#F1EEE8" : pass?"#E9F5DF":"#FAEAE8",
      color: pass===null?"#7A7670" : pass?"#2D6B0C":"#B93020",
    }}>
      {pass===null ? "—" : pass ? "✓" : "✗"} {label}
    </span>
  );
}

// ── Section Heading ────────────────────────────────────────────────────────
function SectionHead({ title, sub, badge, badgeColor }) {
  return (
    <div style={{marginBottom:12}}>
      <div style={{display:"flex",alignItems:"center",gap:8}}>
        <span style={{fontSize:13,fontWeight:600,color:"#0D0D0D",letterSpacing:-0.2}}>{title}</span>
        {badge && (
          <span style={{
            fontSize:9,fontWeight:700,padding:"2px 8px",borderRadius:20,
            background:badgeColor||"#E6F0FB",color:badgeColor?"#fff":"#185FA5",
            letterSpacing:0.05,textTransform:"uppercase",
          }}>{badge}</span>
        )}
      </div>
      {sub && <div style={{fontSize:11,color:"#888",marginTop:2}}>{sub}</div>}
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("overview");
  const [selectedRound, setSelectedRound] = useState(4); // v5.5 index

  const round = BENCHMARK_HISTORY[selectedRound];
  const baseline = BASELINE;

  const metricKeys = [
    {key:"composite_macro_f1", label:"Composite F1", target:0.85},
    {key:"verdict_macro_f1", label:"Verdict Macro F1", target:0.85},
    {key:"major_precision", label:"Major Precision", target:0.90},
    {key:"major_recall", label:"Major Recall", target:0.88},
    {key:"major_f1", label:"Major F1", target:0.89},
    {key:"minor_f1", label:"Minor F1", target:0.90},
    {key:"ofi_f1", label:"OFI F1", target:1.00},
    {key:"ie_recall", label:"IE Recall", target:0.80},
    {key:"clause_accuracy", label:"Clause Accuracy", target:1.00},
    {key:"binary_f1", label:"Binary F1 (NC detect)", target:0.95},
  ];

  const NAV = [
    {id:"overview", label:"Overview"},
    {id:"baseline", label:"Baseline Lock"},
    {id:"gates", label:"Immutable Gates"},
    {id:"drift", label:"Drift Monitor"},
    {id:"history", label:"Round History"},
    {id:"governance", label:"Governance Policy"},
  ];

  const navStyle = (id) => ({
    padding:"7px 14px", fontSize:12, fontWeight:tab===id?600:400,
    borderRadius:6, border:"none", background:tab===id?"#0D0D0D":"transparent",
    color:tab===id?"#fff":"#555", cursor:"pointer", transition:"all .15s",
  });

  return (
    <div style={{
      fontFamily:"'IBM Plex Mono','Courier New',monospace",
      background:"#F8F7F4", minHeight:"100vh", padding:"0 0 48px",
      color:"#0D0D0D",
    }}>
      {/* Top bar */}
      <div style={{
        background:"#0D0D0D", padding:"12px 24px",
        display:"flex", alignItems:"center", justifyContent:"space-between",
      }}>
        <div>
          <div style={{fontSize:13,fontWeight:700,color:"#E8E5DF",letterSpacing:0.5}}>
            MASCI · AI HARNESS GOVERNANCE
          </div>
          <div style={{fontSize:10,color:"#666",marginTop:2,letterSpacing:0.3}}>
            ai-audit-platform-core · qms-auditor-iso-9001-2026 · F1 IMMUTABLE BASELINE SYSTEM
          </div>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={{textAlign:"right"}}>
            <div style={{fontSize:9,color:"#666",letterSpacing:0.3}}>BASELINE LOCKED</div>
            <div style={{fontSize:11,fontWeight:700,color:"#E8B84B"}}>{BASELINE.locked_date}</div>
          </div>
          <div style={{
            width:8,height:8,borderRadius:"50%",
            background:"#3B8A0F",
            boxShadow:"0 0 6px #3B8A0F",
          }}/>
        </div>
      </div>

      {/* Nav */}
      <div style={{
        borderBottom:"0.5px solid #E0DDD5",
        padding:"8px 20px", display:"flex", gap:4,
        background:"#FDFCFA",
      }}>
        {NAV.map(n => (
          <button key={n.id} style={navStyle(n.id)} onClick={() => setTab(n.id)}>
            {n.label}
          </button>
        ))}
      </div>

      <div style={{padding:"24px 24px 0"}}>

        {/* ── TAB: OVERVIEW ─────────────────────────────────────────── */}
        {tab === "overview" && (
          <div>
            <SectionHead
              title="System Health Overview"
              sub="Baseline v5.5-DH · 203 benchmark cases · 65 clauses · 39 IAF sectors"
              badge="LIVE"
              badgeColor="#2D6B0C"
            />

            {/* KPI strip */}
            <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:8,marginBottom:16}}>
              {[
                {label:"Composite F1",v:0.783,t:0.85,delta:"+0.115 vs v5.1"},
                {label:"Major Precision",v:0.566,t:0.90,delta:"⚠ Target 0.90",warn:true},
                {label:"IE Recall",v:0.000,t:0.80,delta:"Structural fix pending",crit:true},
                {label:"Clause Accuracy",v:1.000,t:1.00,delta:"Stable all 5 rounds"},
                {label:"Binary F1",v:0.939,t:0.95,delta:"+0.095 vs v5.1"},
              ].map(k => (
                <div key={k.label} style={{
                  background:"#fff", border:`1px solid ${k.crit?"#C0392B":k.warn?"#D4880A":"#E0DDD5"}`,
                  borderRadius:6, padding:"10px 12px",
                  borderTop:`3px solid ${k.crit?"#C0392B":k.warn?"#D4880A":k.v>=k.t?"#3B8A0F":"#D4880A"}`,
                }}>
                  <div style={{fontSize:9,color:"#888",letterSpacing:0.3,marginBottom:4,textTransform:"uppercase"}}>{k.label}</div>
                  <div style={{
                    fontSize:22,fontWeight:700,
                    color:k.crit?"#C0392B":k.warn?"#B35C00":k.v>=k.t?"#2D6B0C":"#B35C00",
                    letterSpacing:-1,
                  }}>{fmt(k.v,3)}</div>
                  <div style={{fontSize:9,color:"#999",marginTop:2}}>{k.delta}</div>
                  <div style={{
                    marginTop:6, fontSize:9, fontWeight:600,
                    color:k.v>=k.t?"#2D6B0C":"#C0392B",
                  }}>target {fmt(k.t,2)} {k.v>=k.t?"✓":"✗"}</div>
                </div>
              ))}
            </div>

            {/* F1 trend chart */}
            <div style={{
              background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,
              padding:"16px 20px",marginBottom:16,
            }}>
              <div style={{fontSize:11,fontWeight:600,marginBottom:12,color:"#333"}}>F1 Trend — 5 Benchmark Rounds</div>
              <div style={{overflowX:"auto"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
                  <thead>
                    <tr style={{borderBottom:"0.5px solid #E0DDD5"}}>
                      <th style={{textAlign:"left",padding:"4px 8px",fontWeight:600,fontSize:10,color:"#888"}}>Metric</th>
                      {BENCHMARK_HISTORY.map(r=>(
                        <th key={r.version} style={{textAlign:"center",padding:"4px 8px",fontWeight:600,fontSize:10,color:"#888"}}>{r.version}</th>
                      ))}
                      <th style={{textAlign:"center",padding:"4px 8px",fontWeight:700,fontSize:10,color:"#0D0D0D"}}>Target</th>
                      <th style={{textAlign:"center",padding:"4px 8px",fontWeight:600,fontSize:10,color:"#888"}}>Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metricKeys.map(mk => {
                      const vals = BENCHMARK_HISTORY.map(r=>r.metrics[mk.key]);
                      const last = vals[vals.length-1];
                      const bc = BASELINE.metrics[mk.key];
                      return (
                        <tr key={mk.key} style={{borderBottom:"0.5px solid #F0EDE8"}}>
                          <td style={{padding:"5px 8px",fontWeight:500,fontSize:11,color:"#333"}}>{mk.label}</td>
                          {vals.map((v,i)=>(
                            <td key={i} style={{
                              textAlign:"center",padding:"5px 8px",
                              fontFamily:"'IBM Plex Mono',monospace",fontSize:11,
                              color:v==null?"#bbb":statusColor(v,mk.target),
                              background:v!=null&&v>=mk.target?"#F6FBF0":"transparent",
                            }}>{fmt(v,3)}</td>
                          ))}
                          <td style={{textAlign:"center",padding:"5px 8px",fontSize:11,fontWeight:700,color:"#185FA5",fontFamily:"monospace"}}>{fmt(mk.target,2)}</td>
                          <td style={{textAlign:"center",padding:"5px 8px"}}>
                            <Sparkline data={vals.filter(v=>v!=null)} width={80} height={24}
                              color={statusColor(last, mk.target)} target={mk.target}/>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div style={{marginTop:8,fontSize:9,color:"#aaa"}}>
                — = no data · Green bg = at/above target · Dashed line = target · Gray dashes = baseline
              </div>
            </div>

            {/* Gate matrix */}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
              <div style={{background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,padding:"14px 16px"}}>
                <div style={{fontSize:11,fontWeight:600,marginBottom:10,color:"#333"}}>Release Gates — Latest Round (v5.5)</div>
                {[
                  {label:"System Macro F1 ≥ 0.85",pass:false},
                  {label:"Noncomplied F1 ≥ 0.87",pass:true},
                  {label:"Major Precision ≥ 0.90",pass:false},
                  {label:"Major Recall ≥ 0.88",pass:true},
                  {label:"IE Recall ≥ 0.80",pass:false},
                  {label:"Clause Accuracy = 1.00",pass:true},
                  {label:"Gate trace present",pass:true},
                ].map(g=>(
                  <div key={g.label} style={{
                    display:"flex",alignItems:"center",justifyContent:"space-between",
                    padding:"5px 0",borderBottom:"0.5px solid #F0EDE8",
                    fontSize:11,
                  }}>
                    <span style={{color:"#444"}}>{g.label}</span>
                    <GateBadge pass={g.pass} label={g.pass?"PASS":"FAIL"}/>
                  </div>
                ))}
                <div style={{marginTop:8,padding:"6px 10px",background:"#FAEAE8",borderRadius:4,fontSize:10,color:"#B93020",fontWeight:600}}>
                  VERDICT: NOT RELEASE READY — 3 gates failing
                </div>
              </div>

              <div style={{background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,padding:"14px 16px"}}>
                <div style={{fontSize:11,fontWeight:600,marginBottom:10,color:"#333"}}>Drift Events</div>
                {DRIFT_EVENTS.map((e,i)=>(
                  <div key={i} style={{
                    padding:"6px 0",borderBottom:"0.5px solid #F0EDE8",
                    fontSize:10,
                  }}>
                    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                      <span style={{
                        fontWeight:600,
                        color:e.severity==="critical"?"#C0392B":"#B35C00",
                        fontSize:9,textTransform:"uppercase",letterSpacing:0.3,
                      }}>{e.severity}</span>
                      <span style={{color:"#999",fontSize:9}}>{e.ts}</span>
                    </div>
                    <div style={{color:"#444",marginTop:2}}>{e.detail}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB: BASELINE LOCK ────────────────────────────────────── */}
        {tab === "baseline" && (
          <div>
            <SectionHead
              title="Baseline Lock — Immutable F1 Reference"
              sub="Locked 2026-06-06 · All future benchmarks compared against this baseline · Cannot be changed without formal review"
              badge="IMMUTABLE"
              badgeColor="#0D0D0D"
            />

            <div style={{
              background:"#0D0D0D",borderRadius:8,padding:"16px 20px",
              marginBottom:16,border:"1px solid #E8B84B",
            }}>
              <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:12}}>
                <div>
                  <div style={{fontSize:13,fontWeight:700,color:"#E8E5DF"}}>BASELINE: {BASELINE.version}</div>
                  <div style={{fontSize:10,color:"#666",marginTop:2}}>Locked by {BASELINE.locked_by} · {BASELINE.locked_date}</div>
                </div>
                <div style={{
                  padding:"4px 12px",background:"#E8B84B",borderRadius:4,
                  fontSize:10,fontWeight:700,color:"#0D0D0D",
                }}>🔒 LOCKED</div>
              </div>
              <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:8}}>
                {Object.entries(BASELINE.metrics).slice(0,8).map(([k,v])=>(
                  <div key={k} style={{background:"#1A1A1A",borderRadius:4,padding:"8px 10px"}}>
                    <div style={{fontSize:9,color:"#666",marginBottom:2,textTransform:"uppercase",letterSpacing:0.3}}>{k.replace(/_/g," ")}</div>
                    <div style={{fontSize:16,fontWeight:700,color:"#E8E5DF",fontFamily:"monospace"}}>{fmt(v,3)}</div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{
              background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,
              padding:"16px 20px",marginBottom:12,
            }}>
              <div style={{fontSize:11,fontWeight:600,marginBottom:12,color:"#333"}}>
                Baseline vs Target — Gap Analysis
              </div>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
                <thead>
                  <tr style={{borderBottom:"0.5px solid #E0DDD5"}}>
                    {["Metric","Baseline","Target","Gap","Priority","Mechanism"].map(h=>(
                      <th key={h} style={{textAlign:"left",padding:"4px 8px",fontSize:10,color:"#888",fontWeight:600}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    {m:"ie_recall",label:"IE Recall",b:0.000,t:0.80,pri:"P0 · Critical",mech:"G2 IE Hard Stop chain enforcement"},
                    {m:"major_precision",label:"Major Precision",b:0.566,t:0.90,pri:"P1 · High",mech:"G3 D2-safe ceiling + G4 M4 conditions"},
                    {m:"composite_macro_f1",label:"Composite F1",b:0.783,t:0.85,pri:"P2 · Derived",mech:"Fix IE + Major → composite rises to ~0.99"},
                    {m:"minor_f1",label:"Minor F1",b:0.826,t:0.90,pri:"P3 · Monitor",mech:"D1 detection gate + false negative reduction"},
                    {m:"verdict_macro_f1",label:"Verdict Macro F1",b:0.896,t:0.92,pri:"P4 · Near",mech:"IE fix eliminates F1=0 class pulling macro down"},
                    {m:"ofi_f1",label:"OFI F1",b:1.000,t:1.00,pri:"Stable",mech:"No action — maintain"},
                    {m:"clause_accuracy",label:"Clause Accuracy",b:1.000,t:1.00,pri:"Stable",mech:"No action — maintain"},
                  ].map(row=>{
                    const gap = row.t - row.b;
                    const gapColor = gap > 0.2 ? "#C0392B" : gap > 0.05 ? "#B35C00" : "#2D6B0C";
                    return (
                      <tr key={row.m} style={{borderBottom:"0.5px solid #F0EDE8"}}>
                        <td style={{padding:"6px 8px",fontWeight:500,color:"#333"}}>{row.label}</td>
                        <td style={{padding:"6px 8px",fontFamily:"monospace",color:statusColor(row.b,row.t)}}>{fmt(row.b,3)}</td>
                        <td style={{padding:"6px 8px",fontFamily:"monospace",color:"#185FA5",fontWeight:700}}>{fmt(row.t,3)}</td>
                        <td style={{padding:"6px 8px",fontFamily:"monospace",color:gapColor,fontWeight:600}}>{gap>0?"+"+fmt(gap,3):fmt(gap,3)}</td>
                        <td style={{padding:"6px 8px",fontSize:10,color:row.pri.startsWith("P0")?"#C0392B":row.pri.startsWith("P1")?"#B35C00":"#555"}}>{row.pri}</td>
                        <td style={{padding:"6px 8px",fontSize:10,color:"#666"}}>{row.mech}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div style={{
              background:"#F6F2E8",border:"0.5px solid #D4A017",borderRadius:8,
              padding:"14px 16px",
            }}>
              <div style={{fontSize:11,fontWeight:700,color:"#7A5700",marginBottom:8}}>
                🔒 Baseline Change Protocol
              </div>
              <div style={{fontSize:11,color:"#5C4000",lineHeight:1.8}}>
                The baseline is the single source of truth for F1 governance. It cannot be changed without:
              </div>
              <ol style={{marginTop:6,paddingLeft:20,fontSize:11,color:"#5C4000",lineHeight:2}}>
                <li>Full 203-case benchmark run with new model predictions</li>
                <li>All current failing gates must PASS before baseline promotion</li>
                <li>Drift regression suite (50 cases) must pass 50/50</li>
                <li>F1 delta per metric must be positive vs current baseline</li>
                <li>Human reviewer sign-off with governance_decision_record.json</li>
                <li>New baseline locked with new version number and date</li>
              </ol>
              <div style={{marginTop:8,fontSize:10,color:"#7A5700",fontWeight:600}}>
                Shortcutting this protocol = governance violation → auto-rollback to last valid baseline
              </div>
            </div>
          </div>
        )}

        {/* ── TAB: IMMUTABLE GATES ─────────────────────────────────── */}
        {tab === "gates" && (
          <div>
            <SectionHead
              title="Immutable Gate Architecture"
              sub="G0–G7 · deterministic enforcement · cannot be skipped or overridden by model · harness_gate_executor.py enforces"
              badge="DETERMINISTIC"
              badgeColor="#185FA5"
            />

            <div style={{
              background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,
              padding:"16px 20px",marginBottom:12,
            }}>
              <div style={{fontSize:11,color:"#555",lineHeight:1.8,marginBottom:12}}>
                <span style={{fontWeight:700,color:"#0D0D0D"}}>Architecture principle:</span> The model fills a structured JSON struct (gate_execution_trace G0–G7). 
                harness_gate_executor.py validates the struct and <span style={{fontWeight:700}}>rejects contradictions</span>. 
                The model cannot override gate results. This converts Type 1 (rule-skip) and Type 2 (rule-override) drift 
                from probabilistic to <span style={{fontWeight:700}}>structurally impossible</span>.
              </div>

              {[
                {id:"G0",name:"Closed-source preflight",rule:"closed_source_confirmed = true before any audit work",output:"BLOCK → no audit without preflight",
                  why:"Prevents web/connector contamination; ensures controlled sources only",
                  field:"G0_preflight.closed_source_confirmed",type:"PREFLIGHT"},
                {id:"G1",name:"Linguistic trigger classifier",rule:"detect evidence_activity ∈ {PRESENTED, VERIFIED, PARTIAL, ABSENT}",output:"Routes to G2/G5/G3 path deterministically",
                  why:"Prevents model from treating 'องค์กรแสดง' as Complied by routing it to IE chain first",
                  field:"G1_linguistic.evidence_activity",type:"ROUTER"},
                {id:"G2",name:"IE Hard Stop (4-step chain)",rule:"STEP 2: 'ครบถ้วน สอดคล้อง' alone → IE | STEP 3: 'ยืนยันการใช้งานจริง' alone → IE | STEP 4: stage_1+PRESENTED → IE",output:"HARD STOP → InsufficientEvidence if any step fires",
                  why:"Root cause of IE recall=0.000 across all 5 rounds; model kept returning Complied despite rule prose",
                  field:"G2_ie_chain.chain_result",type:"HARD STOP",critical:true},
                {id:"G3",name:"D2-safe ceiling check",rule:"if clause ∈ D2_SAFE_LIST (18 clauses) → nc_class ceiling = Minor; block Major",output:"CEILING → Major blocked for sub-element clauses",
                  why:"Root cause of Major FP=23; ref 36 fired too broadly; 18 clauses have sub-element requirements not entire processes",
                  field:"G3_severity_ceiling.clause_category",type:"CEILING",critical:true},
                {id:"G4",name:"M4 three-condition test",rule:"M4 requires A (process absent) AND B (zero records) AND C (mismatch confirms); missing any → D2",output:"3-COND → Major only when all 3 confirmed",
                  why:"Prevents M4 escalation when process exists but records are weak (= D2 not M4)",
                  field:"G4_m4_conditions.m4_result",type:"3-COND"},
                {id:"G6",name:"Complied pre-conditions C1–C4",rule:"C1 implementation_proven + C2 record_proven + C3 elements_covered + C4 evidence_current = all required",output:"BLOCK → InsufficientEvidence if any C fails",
                  why:"Prevents false Complied when model treats 'consistent records' as 'verified implementation'",
                  field:"G6_complied_check.complied_result",type:"PRE-COND"},
                {id:"G7",name:"Calibration trace required",rule:"decisive_question + calibration_trace with risk, evidence_pattern, severity_path",output:"REJECT → incomplete output without trace",
                  why:"Provides audit trail; enables root cause analysis; prevents opaque verdicts",
                  field:"G7_trace.decisive_question",type:"TRACE"},
              ].map(g=>(
                <div key={g.id} style={{
                  border:`0.5px solid ${g.critical?"#D4880A":"#E0DDD5"}`,
                  borderLeft:`3px solid ${g.critical?"#C0392B":"#185FA5"}`,
                  borderRadius:4,padding:"10px 14px",marginBottom:8,
                  background:g.critical?"#FFFAF4":"#FAFAF8",
                }}>
                  <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:6}}>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <span style={{
                        fontFamily:"monospace",fontWeight:800,fontSize:13,
                        color:g.critical?"#C0392B":"#185FA5",
                      }}>{g.id}</span>
                      <span style={{fontSize:12,fontWeight:600,color:"#0D0D0D"}}>{g.name}</span>
                      {g.critical && <span style={{fontSize:9,padding:"1px 6px",background:"#C0392B",color:"#fff",borderRadius:10,fontWeight:700}}>CRITICAL FIX</span>}
                    </div>
                    <span style={{
                      fontSize:9,fontWeight:700,padding:"2px 8px",
                      borderRadius:10,background:"#E6EFF8",color:"#185FA5",
                      letterSpacing:0.3,
                    }}>{g.type}</span>
                  </div>
                  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,fontSize:11}}>
                    <div>
                      <div style={{fontSize:9,color:"#888",marginBottom:2,textTransform:"uppercase",letterSpacing:0.3}}>Rule</div>
                      <div style={{color:"#444",lineHeight:1.6}}>{g.rule}</div>
                    </div>
                    <div>
                      <div style={{fontSize:9,color:"#888",marginBottom:2,textTransform:"uppercase",letterSpacing:0.3}}>Output if triggered</div>
                      <div style={{fontWeight:600,color:g.critical?"#C0392B":"#185FA5"}}>{g.output}</div>
                    </div>
                  </div>
                  <div style={{marginTop:6,fontSize:10,color:"#888"}}>
                    <span style={{fontWeight:600,color:"#555"}}>Struct field: </span>
                    <code style={{background:"#EEECEA",padding:"1px 4px",borderRadius:3,fontSize:10,fontFamily:"monospace"}}>{g.field}</code>
                    <span style={{marginLeft:10}}>{g.why}</span>
                  </div>
                </div>
              ))}
            </div>

            <div style={{
              background:"#0D0D0D",borderRadius:8,padding:"14px 18px",
              fontFamily:"monospace",fontSize:11,color:"#9BE198",lineHeight:1.9,
            }}>
              <div style={{color:"#666",marginBottom:6,fontSize:10,letterSpacing:0.3}}>// harness_gate_executor.py — enforcement call</div>
              <div><span style={{color:"#E8B84B"}}>result</span> = enforce_gates(model_output)</div>
              <div><span style={{color:"#888"}}>if</span> result[<span style={{color:"#E8CFA0"}}>"gate_validation"</span>] == <span style={{color:"#E8CFA0"}}>"FAIL"</span>:</div>
              <div>&nbsp;&nbsp;<span style={{color:"#888"}}># G2: IE Hard Stop violation</span></div>
              <div>&nbsp;&nbsp;reject(reason=<span style={{color:"#E8CFA0"}}>"G2_STEP2_VIOLATION"</span>, forced_verdict=<span style={{color:"#E8CFA0"}}>"InsufficientEvidence"</span>)</div>
              <div>&nbsp;&nbsp;<span style={{color:"#888"}}># G3: D2-safe ceiling</span></div>
              <div>&nbsp;&nbsp;reject(reason=<span style={{color:"#E8CFA0"}}>"G3_D2_SAFE_CEILING_VIOLATION"</span>, forced_nc_class=<span style={{color:"#E8CFA0"}}>"Minor"</span>)</div>
              <div><span style={{color:"#9BE198"}}>→ model cannot override; rejection is final</span></div>
            </div>
          </div>
        )}

        {/* ── TAB: DRIFT MONITOR ───────────────────────────────────── */}
        {tab === "drift" && (
          <div>
            <SectionHead
              title="Drift Monitor"
              sub="PSI verdict shift · F1 consecutive drop · stuck metric detection · upskill candidate queue"
              badge="ACTIVE"
              badgeColor="#2D6B0C"
            />

            {/* Drift thresholds */}
            <div style={{
              display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8,marginBottom:16,
            }}>
              {[
                {label:"F1 drop per window",v:"−0.020",desc:"Alert if F1 drops ≥ 0.02 in a window"},
                {label:"Consecutive windows",v:"3",desc:"Alert after 3 consecutive declines"},
                {label:"PSI verdict shift",v:"0.25",desc:"Kolmogorov-Smirnov threshold"},
                {label:"IE recall floor",v:"0.700",desc:"Hard floor — below triggers P0 upskill"},
                {label:"Major precision floor",v:"0.800",desc:"Below 0.80 → emergency recalibration"},
                {label:"Stuck threshold",v:"2 rounds",desc:"Same metric flat across 2 rounds → structural fix"},
              ].map(t=>(
                <div key={t.label} style={{
                  background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:6,
                  padding:"10px 12px",
                }}>
                  <div style={{fontSize:9,color:"#888",textTransform:"uppercase",letterSpacing:0.3,marginBottom:4}}>{t.label}</div>
                  <div style={{fontSize:18,fontWeight:700,color:"#0D0D0D",fontFamily:"monospace"}}>{t.v}</div>
                  <div style={{fontSize:10,color:"#888",marginTop:2}}>{t.desc}</div>
                </div>
              ))}
            </div>

            {/* Drift events table */}
            <div style={{background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,padding:"14px 16px",marginBottom:12}}>
              <div style={{fontSize:11,fontWeight:600,marginBottom:10,color:"#333"}}>Drift Event Log</div>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
                <thead>
                  <tr style={{borderBottom:"0.5px solid #E0DDD5"}}>
                    {["Timestamp","Skill","Rule","Metric","Severity","Detail"].map(h=>(
                      <th key={h} style={{textAlign:"left",padding:"4px 8px",fontSize:10,color:"#888",fontWeight:600}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {DRIFT_EVENTS.map((e,i)=>(
                    <tr key={i} style={{borderBottom:"0.5px solid #F0EDE8"}}>
                      <td style={{padding:"6px 8px",fontFamily:"monospace",fontSize:10,color:"#888"}}>{e.ts}</td>
                      <td style={{padding:"6px 8px",fontSize:10,color:"#444"}}>{e.skill.replace("qms-auditor-iso-9001-2026","qms-9001")}</td>
                      <td style={{padding:"6px 8px",fontFamily:"monospace",fontSize:10,color:"#555"}}>{e.rule}</td>
                      <td style={{padding:"6px 8px",fontFamily:"monospace",fontSize:10,color:"#185FA5"}}>{e.metric}</td>
                      <td style={{padding:"6px 8px"}}>
                        <span style={{
                          fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:10,
                          background:e.severity==="critical"?"#FAEAE8":"#FFF4E0",
                          color:e.severity==="critical"?"#C0392B":"#B35C00",
                        }}>{e.severity.toUpperCase()}</span>
                      </td>
                      <td style={{padding:"6px 8px",fontSize:10,color:"#666"}}>{e.detail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Upskill candidate queue */}
            <div style={{background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,padding:"14px 16px"}}>
              <div style={{fontSize:11,fontWeight:600,marginBottom:10,color:"#333"}}>Upskill Candidate Queue</div>
              {[
                {priority:"P0",label:"IE Hard Stop enforcement",metric:"ie_recall=0.000",action:"Enforce G2 as hard function in harness_gate_executor.py",type:"deterministic",status:"In progress"},
                {priority:"P1",label:"D2-safe ceiling fix",metric:"major_precision=0.566",action:"G3 D2_SAFE_LIST lookup — block Major for 18 clauses",type:"deterministic",status:"Implemented"},
                {priority:"P2",label:"M4 three-condition",metric:"major_precision drift",action:"G4 A+B+C all required before Major M4",type:"deterministic",status:"Implemented"},
                {priority:"P3",label:"False negative NC→Complied",metric:"20 false negatives",action:"G6 C1–C4 all required before Complied",type:"deterministic",status:"Spec complete"},
              ].map(u=>(
                <div key={u.priority} style={{
                  display:"flex",alignItems:"flex-start",gap:12,
                  padding:"8px 0",borderBottom:"0.5px solid #F0EDE8",fontSize:11,
                }}>
                  <span style={{
                    minWidth:24,height:24,borderRadius:4,
                    background:u.priority==="P0"?"#C0392B":u.priority==="P1"?"#D4880A":"#185FA5",
                    color:"#fff",fontWeight:800,fontSize:10,
                    display:"flex",alignItems:"center",justifyContent:"center",
                    flexShrink:0,
                  }}>{u.priority}</span>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:600,color:"#0D0D0D"}}>{u.label}</div>
                    <div style={{fontSize:10,color:"#888",marginTop:1}}>{u.metric} · {u.action}</div>
                  </div>
                  <div style={{display:"flex",flexDirection:"column",alignItems:"flex-end",gap:4}}>
                    <span style={{fontSize:9,padding:"1px 6px",background:"#EEF2F8",color:"#185FA5",borderRadius:10,fontWeight:600}}>{u.type}</span>
                    <span style={{fontSize:9,padding:"1px 6px",background:"#F0EDE8",color:"#666",borderRadius:10}}>{u.status}</span>
                  </div>
                </div>
              ))}
              <div style={{marginTop:8,fontSize:10,color:"#888"}}>
                Rule: if same metric stuck ≥ 2 rounds → stop adding markdown rules → design deterministic gate instead
              </div>
            </div>
          </div>
        )}

        {/* ── TAB: ROUND HISTORY ───────────────────────────────────── */}
        {tab === "history" && (
          <div>
            <SectionHead
              title="Benchmark Round History"
              sub="5 rounds · 203 cases each · qms-auditor-iso-9001-2026 · select round to inspect"
            />

            {/* Round selector */}
            <div style={{display:"flex",gap:6,marginBottom:16,flexWrap:"wrap"}}>
              {BENCHMARK_HISTORY.map((r,i)=>(
                <button key={r.version}
                  onClick={()=>setSelectedRound(i)}
                  style={{
                    padding:"6px 14px",fontSize:11,fontWeight:selectedRound===i?700:400,
                    borderRadius:4,border:`0.5px solid ${selectedRound===i?"#0D0D0D":"#D0CCC4"}`,
                    background:selectedRound===i?"#0D0D0D":"#fff",
                    color:selectedRound===i?"#fff":"#555",cursor:"pointer",
                  }}>
                  {r.version} <span style={{fontSize:9,opacity:0.7}}>({r.gates_passed}/5)</span>
                </button>
              ))}
            </div>

            {round && (
              <div>
                <div style={{
                  background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,
                  padding:"14px 16px",marginBottom:12,
                }}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
                    <div>
                      <div style={{fontSize:14,fontWeight:700,color:"#0D0D0D"}}>{round.version}</div>
                      <div style={{fontSize:11,color:"#888",marginTop:2}}>{round.date} · Upskill applied: {round.upskill}</div>
                    </div>
                    <div style={{display:"flex",gap:6,flexWrap:"wrap",justifyContent:"flex-end"}}>
                      {round.refs_applied.map(r=>(
                        <span key={r} style={{fontSize:9,padding:"2px 7px",background:"#EEF2F8",color:"#185FA5",borderRadius:10,fontWeight:600}}>{r}</span>
                      ))}
                    </div>
                  </div>
                  <div style={{
                    padding:"8px 12px",background:"#FEF9EC",borderRadius:4,
                    fontSize:11,color:"#7A5700",marginBottom:12,
                  }}>
                    <span style={{fontWeight:700}}>Failure: </span>{round.failure}
                  </div>
                  <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:6}}>
                    {metricKeys.map(mk=>{
                      const v = round.metrics[mk.key];
                      const t = mk.target;
                      return (
                        <div key={mk.key} style={{
                          background:"#FAFAF8",borderRadius:4,padding:"8px 10px",
                          borderTop:`2px solid ${statusColor(v,t)}`,
                        }}>
                          <div style={{fontSize:9,color:"#888",marginBottom:2,textTransform:"uppercase",letterSpacing:0.3}}>{mk.label}</div>
                          <div style={{fontSize:16,fontWeight:700,fontFamily:"monospace",color:statusColor(v,t)}}>{fmt(v,3)}</div>
                          <div style={{fontSize:9,color:"#999"}}>target {fmt(t,2)}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
                <div style={{
                  background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,
                  padding:"14px 16px",
                }}>
                  <div style={{fontSize:11,fontWeight:600,marginBottom:8,color:"#333"}}>Release Gates</div>
                  <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
                    {Object.entries(round.gates).map(([k,v])=>(
                      <GateBadge key={k} pass={v} label={k.replace(/_/g," ")}/>
                    ))}
                  </div>
                  <div style={{
                    marginTop:8,fontSize:11,fontWeight:600,
                    color:round.gates_passed>=5?"#2D6B0C":"#C0392B",
                  }}>
                    {round.gates_passed}/5 gates passed — {round.gates_passed>=5?"RELEASE READY":"NOT RELEASE READY"}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB: GOVERNANCE POLICY ──────────────────────────────── */}
        {tab === "governance" && (
          <div>
            <SectionHead
              title="AI Governance Policy"
              sub="ai-audit-platform-core · immutable rules · platform precedence · change protocol"
              badge="POLICY"
              badgeColor="#534AB7"
            />

            {/* Precedence hierarchy */}
            <div style={{
              background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,
              padding:"14px 16px",marginBottom:12,
            }}>
              <div style={{fontSize:11,fontWeight:600,marginBottom:10,color:"#333"}}>Platform Governance Precedence</div>
              {[
                {level:1,label:"Platform Governance Control Plane",color:"#C0392B",desc:"governance-layer.md · immutable governance rules · cannot be overridden by any domain skill"},
                {level:2,label:"Root ai-audit-platform-core SKILL.md",color:"#D4880A",desc:"Platform operating rules · crew dispatch · F1 governance · drift monitoring policy"},
                {level:3,label:"Domain Skill SKILL.md",color:"#185FA5",desc:"QMS/EMS specific behavior · v5.5.1 with refs 36–41 · harness gate rules"},
                {level:4,label:"Domain Skill references / scripts / assets",color:"#534AB7",desc:"refs 01–41 · harness_gate_executor.py · benchmark data · test suites"},
                {level:5,label:"User Request",color:"#888",desc:"User input after all platform layers applied"},
              ].map(p=>(
                <div key={p.level} style={{
                  display:"flex",alignItems:"flex-start",gap:10,
                  padding:"8px 0",borderBottom:"0.5px solid #F0EDE8",fontSize:11,
                }}>
                  <div style={{
                    minWidth:24,height:24,borderRadius:4,
                    background:p.color,color:"#fff",fontWeight:800,fontSize:11,
                    display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,
                  }}>{p.level}</div>
                  <div>
                    <div style={{fontWeight:700,color:"#0D0D0D"}}>{p.label}</div>
                    <div style={{fontSize:10,color:"#888",marginTop:1}}>{p.desc}</div>
                  </div>
                </div>
              ))}
              <div style={{
                marginTop:8,padding:"6px 10px",background:"#F0EDE8",borderRadius:4,
                fontSize:10,color:"#555",
              }}>
                Conflict rule: if domain instruction conflicts with platform governance → escalate as ReviewRequired; do NOT silently bypass Platform Core
              </div>
            </div>

            {/* Immutable rules */}
            <div style={{
              background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,
              padding:"14px 16px",marginBottom:12,
            }}>
              <div style={{fontSize:11,fontWeight:600,marginBottom:10,color:"#333"}}>Immutable Rules — Cannot Be Changed Without Full Governance Review</div>
              {[
                "Do not use web search, external connectors, or base model memory for audit substance",
                "Do not classify Major NC without objective evidence matching M1–M5 trigger conditions",
                "Do not compute model performance by comparing two gold files",
                "Do not show gold labels to the model during inference",
                "Gate enforcement (G0–G7) cannot be disabled, bypassed, or softened via upskill modules",
                "IE recall floor = 0.700 — below this, auto-reject production deployment",
                "Major precision floor = 0.800 — below this, freeze Major auto-classification",
                "Baseline cannot be promoted without all failing gates passing first",
                "Upskill modules added after v5.5-DH cannot remove or weaken existing gate rules",
                "Structured output (gate_execution_trace) is mandatory for all material verdicts",
              ].map((rule,i)=>(
                <div key={i} style={{
                  display:"flex",gap:8,padding:"5px 0",
                  borderBottom:"0.5px solid #F0EDE8",fontSize:11,
                }}>
                  <span style={{color:"#C0392B",fontWeight:800,fontSize:12,flexShrink:0}}>✗</span>
                  <span style={{color:"#444"}}>{rule}</span>
                </div>
              ))}
            </div>

            {/* Release workflow */}
            <div style={{
              background:"#fff",border:"0.5px solid #E0DDD5",borderRadius:8,
              padding:"14px 16px",
            }}>
              <div style={{fontSize:11,fontWeight:600,marginBottom:10,color:"#333"}}>Release Workflow — 6 Steps (all required)</div>
              {[
                {n:1,label:"Generate predictions",cmd:"python scripts/harness_gate_executor.py --batch model_predictions.jsonl --outdir gate_results/"},
                {n:2,label:"Validate artifact",cmd:"python scripts/validate_model_predictions.py --pred model_predictions.jsonl --blind blind_testcases.jsonl"},
                {n:3,label:"Run regression suite",cmd:"python scripts/run_regression_suite.py --cases assets/tests/drift-regression-suite.jsonl"},
                {n:4,label:"Compute F1",cmd:"python scripts/evaluate_model_predictions.py --gold answer_key.jsonl --pred model_predictions.jsonl"},
                {n:5,label:"Drift check",cmd:"python scripts/drift_monitor.py --f1 f1_timeseries.jsonl --feedback feedback_log_central.jsonl --output drift_events.jsonl"},
                {n:6,label:"Human review + baseline promote",cmd:"governance_decision_record.json → sign-off → update BASELINE object → lock with new date"},
              ].map(s=>(
                <div key={s.n} style={{
                  display:"flex",gap:10,padding:"6px 0",
                  borderBottom:"0.5px solid #F0EDE8",fontSize:11,
                  alignItems:"flex-start",
                }}>
                  <span style={{
                    minWidth:20,height:20,borderRadius:"50%",
                    background:"#0D0D0D",color:"#fff",fontWeight:800,fontSize:10,
                    display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,marginTop:1,
                  }}>{s.n}</span>
                  <div>
                    <div style={{fontWeight:600,color:"#0D0D0D",marginBottom:2}}>{s.label}</div>
                    <code style={{
                      display:"block",fontSize:10,
                      background:"#F0EDE8",padding:"3px 8px",borderRadius:3,
                      fontFamily:"monospace",color:"#333",
                    }}>{s.cmd}</code>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* Footer */}
      <div style={{
        marginTop:32,padding:"12px 24px",borderTop:"0.5px solid #E0DDD5",
        display:"flex",justifyContent:"space-between",alignItems:"center",
        fontSize:10,color:"#999",
      }}>
        <span>MASCI · ai-audit-platform-core · qms-auditor-iso-9001-2026 v5.5.1 · 203 cases · 65 clauses · 39 IAF sectors</span>
        <span>Baseline locked {BASELINE.locked_date} · F1 Immutable Governance System</span>
      </div>
    </div>
  );
}
