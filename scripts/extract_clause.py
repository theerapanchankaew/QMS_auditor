#!/usr/bin/env python3
"""Exact clause lookup from the registered supplied PDF (clauses 4-10)."""
import argparse,json,sys
from pathlib import Path
from controlled_retrieval import ClauseStore,ReferenceGap

def main():
    p=argparse.ArgumentParser()
    p.add_argument('clause');p.add_argument('--json',action='store_true')
    p.add_argument('--pdf');p.add_argument('--max-chars',type=int,default=8000)
    p.add_argument('--include-annex',action='store_true')
    a=p.parse_args()
    try:
        store=ClauseStore()
        if a.pdf and Path(a.pdf).resolve()!=store.path:raise ReferenceGap('PDF is not the registered source')
        if a.include_annex or a.clause.startswith('A'):raise ReferenceGap('Annex is informative and not indexed as primary criteria')
        if a.max_chars<1:raise ReferenceGap('max-chars must be positive')
        result=store.get(a.clause);result['truncated']=len(result['text'])>a.max_chars
        result['text']=result['text'][:a.max_chars]
        print(json.dumps(result,ensure_ascii=False,indent=2) if a.json else result['text'])
        return 0
    except (ReferenceGap,OSError,ValueError) as e:
        print(json.dumps({'status':'ReferenceGap','error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':sys.exit(main())
