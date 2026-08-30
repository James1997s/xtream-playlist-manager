#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests


def fetch(args, item):
    sid = item.get('series_id')
    if not sid:
        return None
    try:
        response = requests.get(args.endpoint, params={'username': args.username, 'password': args.password, 'action': 'get_series_info', 'series_id': sid}, timeout=args.timeout)
        response.raise_for_status()
        detail = response.json()
        return {'show': item, 'detail': detail}
    except (requests.RequestException, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--series-json', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--endpoint', required=True)
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--workers', type=int, default=32)
    parser.add_argument('--timeout', type=int, default=8)
    args = parser.parse_args()
    items = json.loads(args.series_json.read_text())
    completed = 0
    with args.out.open('a', encoding='utf-8') as handle, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(fetch, args, item) for item in items if item.get('series_id')]
        for future in as_completed(futures):
            result = future.result()
            if result:
                handle.write(json.dumps(result, ensure_ascii=False) + '\n')
                completed += 1
            if (completed + sum(1 for f in futures if f.done())) % 500 == 0:
                handle.flush()
                print(f'completed={completed} processed={sum(1 for f in futures if f.done())}/{len(futures)}', flush=True)
    print(json.dumps({'series_input': len(items), 'series_details_saved': completed, 'output': str(args.out)}))

if __name__ == '__main__':
    main()
