#!/usr/bin/env python3
"""Apply only high-confidence records from map_epg.py to an M3U file."""
from __future__ import annotations
import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--m3u', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    mapping = json.loads(args.mapping.read_text())
    ids_by_title = defaultdict(deque)
    for row in mapping:
        if row.get('confidence') == 'high' and row.get('xmltv_id'):
            ids_by_title[row.get('m3u_title', '')].append(row['xmltv_id'])
    lines = args.m3u.read_text(errors='ignore').splitlines()
    applied = 0
    headers = 0
    output = []
    for line in lines:
        if line.startswith('#EXTINF:'):
            headers += 1
            comma = line.find(',')
            title = line[comma + 1:].strip() if comma >= 0 else ''
            xmltv_id = ids_by_title[title].popleft() if ids_by_title[title] else ''
            if xmltv_id and 'tvg-id=' not in line.lower():
                line = re.sub(r'^(#EXTINF:[^ ]+)', r'\1 tvg-id="' + xmltv_id.replace('"', '') + '"', line, count=1)
                applied += 1
        output.append(line)
    args.out.write_text('\n'.join(output) + '\n')
    print(json.dumps({'headers': headers, 'high_confidence_ids_applied': applied, 'output': str(args.out)}))

if __name__ == '__main__':
    main()
