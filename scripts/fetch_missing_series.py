#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

def main():
    p=argparse.ArgumentParser(); p.add_argument('--series-json',type=Path,required=True); p.add_argument('--details-jsonl',type=Path,required=True); p.add_argument('--endpoint',required=True); p.add_argument('--username',required=True); p.add_argument('--password',required=True); p.add_argument('--workers',type=int,default=32); p.add_argument('--timeout',type=int,default=12); args=p.parse_args()
    series=json.loads(args.series_json.read_text())
    done=set()
    for raw in args.details_jsonl.read_text(errors='ignore').splitlines():
        try: row=json.loads(raw); sid=str((row.get('show') or {}).get('series_id','')); done.add(sid)
        except json.JSONDecodeError: pass
    missing=[item for item in series if str(item.get('series_id','')) not in done]
    def fetch(item):
        try:
            r=requests.get(args.endpoint,params={'username':args.username,'password':args.password,'action':'get_series_info','series_id':item['series_id']},timeout=args.timeout); r.raise_for_status(); return {'show':item,'detail':r.json()}
        except (requests.RequestException,ValueError): return None
    saved=0
    with args.details_jsonl.open('a',encoding='utf-8') as handle, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(fetch,item) for item in missing]
        for future in as_completed(futures):
            row=future.result()
            if row: handle.write(json.dumps(row,ensure_ascii=False)+'\n'); saved+=1
            if (saved+sum(f.done() for f in futures)) % 50 == 0: handle.flush(); print(f'processed={sum(f.done() for f in futures)}/{len(futures)} saved={saved}',flush=True)
    print(json.dumps({'series_total':len(series),'previously_done':len(done),'missing_requested':len(missing),'newly_saved':saved}))

if __name__=='__main__': main()
