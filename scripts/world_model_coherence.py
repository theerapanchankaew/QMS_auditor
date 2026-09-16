#!/usr/bin/env python3
import argparse, json
from audit_state_canonicalizer import equivalent


def aset(x):
    return set(x or [])

def jaccard(a,b):
    a,b=aset(a),aset(b)
    if not a and not b:return 1.0
    return len(a&b)/len(a|b) if a|b else 1.0

def compression_score(case):
    eq = equivalent(case['state_a'],case['state_b'])
    sim = jaccard(case.get('continuations_a'),case.get('continuations_b'))
    expected = bool(case.get('expect_equivalent',True))
    passed = (eq == expected) and (sim >= float(case.get('min_jaccard',0.95)) if expected else True)
    return {'id':case.get('id'),'state_equivalent':eq,'continuation_jaccard':round(sim,4),'pass':passed}

def distinction_score(case):
    same = aset(case.get('continuations_a'))
    other = aset(case.get('continuations_b'))
    true_dist = aset(case.get('distinguishing_continuations'))
    model_dist = same ^ other
    tp=len(model_dist & true_dist); fp=len(model_dist-true_dist); fn=len(true_dist-model_dist)
    precision=tp/(tp+fp) if tp+fp else (1.0 if not true_dist else 0.0)
    recall=tp/(tp+fn) if tp+fn else 1.0
    states_distinct = not equivalent(case['state_a'],case['state_b'])
    passed=states_distinct and precision>=float(case.get('min_precision',0.90)) and recall>=float(case.get('min_recall',0.90))
    return {'id':case.get('id'),'states_distinct':states_distinct,'precision':round(precision,4),'recall':round(recall,4),'pass':passed}

def evaluate(data):
    comp=[compression_score(c) for c in data.get('compression_cases',[])]
    dist=[distinction_score(c) for c in data.get('distinction_cases',[])]
    def avg(xs,k): return round(sum(x[k] for x in xs)/len(xs),4) if xs else None
    return {
      'compression_cases':comp,'distinction_cases':dist,
      'summary':{
        'compression_consistency':avg(comp,'continuation_jaccard'),
        'compression_pass_rate':round(sum(x['pass'] for x in comp)/len(comp),4) if comp else None,
        'distinction_precision':avg(dist,'precision'),
        'distinction_recall':avg(dist,'recall'),
        'distinction_pass_rate':round(sum(x['pass'] for x in dist)/len(dist),4) if dist else None
      }
    }

def main():
    p=argparse.ArgumentParser(); p.add_argument('--cases',required=True); p.add_argument('--output',required=True); a=p.parse_args()
    with open(a.cases,encoding='utf-8') as f:d=json.load(f)
    out=evaluate(d)
    with open(a.output,'w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
    ok=all(x['pass'] for x in out['compression_cases']+out['distinction_cases'])
    raise SystemExit(0 if ok else 2)
if __name__=='__main__': main()
