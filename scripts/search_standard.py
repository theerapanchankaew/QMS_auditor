#!/usr/bin/env python3
"""Search registered normative clauses; no TOC, Annex or unregistered PDFs."""
import argparse,json,re,sys
from pathlib import Path
from controlled_retrieval import ClauseStore,ReferenceGap

def main():
 p=argparse.ArgumentParser();p.add_argument('query');p.add_argument('--max',type=int,default=5);p.add_argument('--context',type=int,default=180);p.add_argument('--json',action='store_true');p.add_argument('--pdf');a=p.parse_args()
 try:
  s=ClauseStore()
  if a.pdf and Path(a.pdf).resolve()!=s.path:raise ReferenceGap('Unregistered PDF')
  if not a.query.strip() or not 1<=a.max<=20 or not 1<=a.context<=1000:raise ReferenceGap('Invalid search bounds')
  out=[];tokens=re.findall(r'[\w.]+',a.query.lower())
  for number in s.profiles:
   x=s.get(number);low=x['text'].lower();score=sum(t in low for t in tokens)
   if not score:continue
   at=min((low.find(t) for t in tokens if t in low),default=0)
   out.append({'clause':number,'source':x['source'],'source_sha256':x['source_sha256'],'page':x['start_page'],'score':score,'snippet':x['text'][max(0,at-a.context):at+a.context]})
  out=sorted(out,key=lambda x:x['score'],reverse=True)[:a.max]
  print(json.dumps({'status':'ok','results':out,'note':'Search hits are candidates; use exact clause lookup before assessment.'},ensure_ascii=False,indent=2));return 0
 except (ReferenceGap,OSError,ValueError) as e:
  print(json.dumps({'status':'ReferenceGap','error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':sys.exit(main())
